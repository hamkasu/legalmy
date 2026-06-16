from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Optional, List
from app.database import get_db
from app.models.judge import Judge
from app.models.court import Court
from app.models.judge_profile import JudgeProfile
from app.models.case import Case
from app.schemas.judges import JudgeListItem, JudgeDetail, JudgeProfileData, JudgeCaseResult
from app.analytics.judges import compute_judge_profile

router = APIRouter(prefix="/judges", tags=["judges"])

@router.get("", response_model=List[JudgeListItem])
async def list_judges(
    name: Optional[str] = None,
    court_type: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(
        Judge.id,
        Judge.name,
        Judge.state,
        Court.name.label("court_name"),
        Court.court_type.label("court_type"),
    ).outerjoin(Court)

    if name:
        query = query.where(Judge.name.ilike(f"%{name}%"))

    if court_type:
        query = query.where(Court.court_type == court_type)

    if state:
        query = query.where(or_(Judge.state == state, Court.state == state))

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    rows = result.all()

    return [
        JudgeListItem(
            id=row.id,
            name=row.name,
            state=row.state,
            court_name=row.court_name,
            court_type=row.court_type,
        )
        for row in rows
    ]

@router.get("/{judge_id}", response_model=JudgeDetail)
async def get_judge_detail(
    judge_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(
        Judge.id,
        Judge.name,
        Judge.state,
        Court.name.label("court_name"),
        Court.court_type.label("court_type"),
    ).where(Judge.id == judge_id).outerjoin(Court)

    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Judge not found",
        )

    # Get judge profile if exists
    profile_query = select(JudgeProfile).where(JudgeProfile.judge_id == judge_id)
    profile_result = await db.execute(profile_query)
    profile = profile_result.scalar_one_or_none()

    profile_data = None
    if profile:
        profile_data = JudgeProfileData(
            total_decisions=profile.total_decisions,
            plaintiff_favourable_rate=profile.plaintiff_favourable_rate,
            avg_disposal_days=profile.avg_disposal_days,
            interlocutory_grant_rate=profile.interlocutory_grant_rate,
            costs_awarded_rate=profile.costs_awarded_rate,
            top_practice_areas=profile.top_practice_areas,
        )

    return JudgeDetail(
        id=row.id,
        name=row.name,
        state=row.state,
        court_name=row.court_name,
        court_type=row.court_type,
        profile=profile_data,
    )

@router.get("/{judge_id}/analytics", response_model=JudgeProfileData)
async def get_judge_analytics(
    judge_id: str,
    db: AsyncSession = Depends(get_db),
):
    # Check if judge exists
    judge_query = select(Judge).where(Judge.id == judge_id)
    judge_result = await db.execute(judge_query)
    if not judge_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Judge not found",
        )

    # Get or compute judge profile
    profile_query = select(JudgeProfile).where(JudgeProfile.judge_id == judge_id)
    profile_result = await db.execute(profile_query)
    profile = profile_result.scalar_one_or_none()

    if not profile:
        # Try to compute profile
        profile = await compute_judge_profile(judge_id, db)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enough case data to generate analytics",
        )

    return JudgeProfileData(
        total_decisions=profile.total_decisions,
        plaintiff_favourable_rate=profile.plaintiff_favourable_rate,
        avg_disposal_days=profile.avg_disposal_days,
        interlocutory_grant_rate=profile.interlocutory_grant_rate,
        costs_awarded_rate=profile.costs_awarded_rate,
        top_practice_areas=profile.top_practice_areas,
    )

@router.get("/{judge_id}/cases", response_model=List[JudgeCaseResult])
async def get_judge_cases(
    judge_id: str,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    practice_area: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    # Check if judge exists
    judge_query = select(Judge).where(Judge.id == judge_id)
    judge_result = await db.execute(judge_query)
    if not judge_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Judge not found",
        )

    query = select(
        Case.id,
        Case.case_number,
        Case.title,
        Case.date_decided,
        Case.practice_area,
        Case.outcome,
    ).where(Case.judge_id == judge_id)

    if year_from:
        query = query.where(Case.date_decided >= f"{year_from}-01-01")

    if year_to:
        query = query.where(Case.date_decided <= f"{year_to}-12-31")

    if practice_area and practice_area != "other":
        query = query.where(Case.practice_area == practice_area)

    if outcome and outcome != "unknown":
        query = query.where(Case.outcome == outcome)

    query = query.order_by(Case.date_decided.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    rows = result.all()

    return [
        JudgeCaseResult(
            id=row.id,
            case_number=row.case_number,
            title=row.title,
            date_decided=row.date_decided,
            practice_area=row.practice_area,
            outcome=row.outcome,
        )
        for row in rows
    ]
