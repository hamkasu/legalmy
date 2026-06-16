from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from typing import Optional, List
from app.database import get_db
from app.models.user import User
from app.models.case import Case
from app.models.court import Court
from app.models.judge import Judge
from app.models.saved_case import SavedCase
from app.auth.security import get_current_user
from app.schemas.cases import CaseSearchResult, CaseDetail, SaveCaseRequest, SavedCaseResponse

router = APIRouter(prefix="/cases", tags=["cases"])
security = HTTPBearer()

@router.get("/search", response_model=List[CaseSearchResult])
async def search_cases(
    q: Optional[str] = Query(None),
    court_type: Optional[str] = None,
    state: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    practice_area: Optional[str] = None,
    outcome: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(
        Case.id,
        Case.case_number,
        Case.citation,
        Case.title,
        Court.name.label("court_name"),
        Judge.name.label("judge_name"),
        Case.date_decided,
        Case.practice_area,
        Case.outcome,
        Case.language,
        func.substring(Case.full_text, 1, 200).label("snippet"),
    ).outerjoin(Court).outerjoin(Judge)

    if q:
        query = query.where(
            or_(
                Case.title.ilike(f"%{q}%"),
                Case.full_text.ilike(f"%{q}%")
            )
        )

    if court_type:
        query = query.where(Court.court_type == court_type)

    if state:
        query = query.where(Court.state == state)

    if year_from:
        query = query.where(Case.date_decided >= f"{year_from}-01-01")

    if year_to:
        query = query.where(Case.date_decided <= f"{year_to}-12-31")

    if practice_area and practice_area != "other":
        query = query.where(Case.practice_area == practice_area)

    if outcome and outcome != "unknown":
        query = query.where(Case.outcome == outcome)

    if language:
        query = query.where(Case.language == language)

    query = query.order_by(Case.date_decided.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    rows = result.all()

    return [
        CaseSearchResult(
            id=row.id,
            case_number=row.case_number,
            citation=row.citation,
            title=row.title,
            court_name=row.court_name,
            judge_name=row.judge_name,
            date_decided=row.date_decided,
            practice_area=row.practice_area,
            outcome=row.outcome,
            language=row.language,
            snippet=row.snippet,
        )
        for row in rows
    ]

@router.get("/{case_id}", response_model=CaseDetail)
async def get_case_detail(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(
        Case.id,
        Case.case_number,
        Case.citation,
        Case.title,
        Case.plaintiff,
        Case.defendant,
        Case.date_filed,
        Case.date_decided,
        Case.practice_area,
        Case.outcome,
        Case.full_text,
        Case.summary,
        Case.source_url,
        Case.source,
        Case.language,
        Court.name.label("court_name"),
        Judge.name.label("judge_name"),
    ).where(Case.id == case_id).outerjoin(Court).outerjoin(Judge)

    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return CaseDetail(
        id=row.id,
        case_number=row.case_number,
        citation=row.citation,
        title=row.title,
        plaintiff=row.plaintiff,
        defendant=row.defendant,
        date_filed=row.date_filed,
        date_decided=row.date_decided,
        practice_area=row.practice_area,
        outcome=row.outcome,
        full_text=row.full_text,
        summary=row.summary,
        source_url=row.source_url,
        source=row.source,
        language=row.language,
        court_name=row.court_name,
        judge_name=row.judge_name,
    )

@router.post("/{case_id}/save")
async def save_case(
    case_id: str,
    request: SaveCaseRequest,
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token=credentials.credentials, db=db)

    # Check if case exists
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    if not case_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    # Check if already saved
    saved_result = await db.execute(
        select(SavedCase).where(
            and_(
                SavedCase.user_id == user.id,
                SavedCase.case_id == case_id,
            )
        )
    )
    if saved_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case already saved",
        )

    saved_case = SavedCase(
        user_id=user.id,
        case_id=case_id,
        notes=request.notes,
    )
    db.add(saved_case)
    await db.commit()
    await db.refresh(saved_case)

    return {"id": saved_case.id, "message": "Case saved successfully"}

@router.get("/saved", response_model=List[SavedCaseResponse])
async def get_saved_cases(
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(token=credentials.credentials, db=db)

    query = select(SavedCase).where(SavedCase.user_id == user.id)
    result = await db.execute(query)
    saved_cases = result.scalars().all()

    response = []
    for saved_case in saved_cases:
        case_query = select(
            Case.id,
            Case.case_number,
            Case.citation,
            Case.title,
            Case.plaintiff,
            Case.defendant,
            Case.date_filed,
            Case.date_decided,
            Case.practice_area,
            Case.outcome,
            Case.full_text,
            Case.summary,
            Case.source_url,
            Case.source,
            Case.language,
            Court.name.label("court_name"),
            Judge.name.label("judge_name"),
        ).where(Case.id == saved_case.case_id).outerjoin(Court).outerjoin(Judge)

        case_result = await db.execute(case_query)
        case_row = case_result.first()

        if case_row:
            response.append(
                SavedCaseResponse(
                    id=saved_case.id,
                    case_id=saved_case.case_id,
                    notes=saved_case.notes,
                    case=CaseDetail(
                        id=case_row.id,
                        case_number=case_row.case_number,
                        citation=case_row.citation,
                        title=case_row.title,
                        plaintiff=case_row.plaintiff,
                        defendant=case_row.defendant,
                        date_filed=case_row.date_filed,
                        date_decided=case_row.date_decided,
                        practice_area=case_row.practice_area,
                        outcome=case_row.outcome,
                        full_text=case_row.full_text,
                        summary=case_row.summary,
                        source_url=case_row.source_url,
                        source=case_row.source,
                        language=case_row.language,
                        court_name=case_row.court_name,
                        judge_name=case_row.judge_name,
                    ),
                )
            )

    return response
