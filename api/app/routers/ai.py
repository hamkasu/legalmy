import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.case import Case
from app.auth.security import get_current_user
from app.ai.summariser import summarise_judgment
from app.ai.case_assessment import assess_case
from app.ai.bilingual_drafter import draft_legal_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])
security = HTTPBearer()

# Request schemas
class SummariseRequest(BaseModel):
    case_id: str

class AssessmentRequest(BaseModel):
    facts: str
    claim_type: str
    court: str

class DraftRequest(BaseModel):
    doc_type: str
    facts: str
    language: str = "en"

# Response schemas
class AssessmentResponse(BaseModel):
    success_probability: int
    key_strengths: List[str]
    key_risks: List[str]
    recommended_cause_of_action: str
    relevant_statutes: List[str]
    similar_cases_to_research: List[str]

@router.post("/summarise")
async def summarise_case(
    request: SummariseRequest,
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Summarise a judgment and update case summary.
    """
    try:
        # Verify user
        user = await get_current_user(token=credentials.credentials, db=db)

        # Get case
        result = await db.execute(select(Case).where(Case.id == request.case_id))
        case = result.scalar_one_or_none()

        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found",
            )

        if not case.full_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case has no full text to summarise",
            )

        # Generate summary
        summary = await summarise_judgment(case.full_text, language="en")

        # Update case
        case.summary = summary
        await db.commit()
        await db.refresh(case)

        return {
            "case_id": case.id,
            "summary": summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarising case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error summarising case",
        )

@router.post("/assess", response_model=AssessmentResponse)
async def assess_case_endpoint(
    request: AssessmentRequest,
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Assess a case and return analysis.
    """
    try:
        # Verify user
        user = await get_current_user(token=credentials.credentials, db=db)

        # Generate assessment
        assessment = await assess_case(
            facts=request.facts,
            claim_type=request.claim_type,
            court=request.court,
        )

        # Extract relevant fields
        return AssessmentResponse(
            success_probability=assessment.get("success_probability", 50),
            key_strengths=assessment.get("key_strengths", []),
            key_risks=assessment.get("key_risks", []),
            recommended_cause_of_action=assessment.get("recommended_cause_of_action", ""),
            relevant_statutes=assessment.get("relevant_statutes", []),
            similar_cases_to_research=assessment.get("similar_cases_to_research", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error assessing case",
        )

@router.post("/draft")
async def draft_document(
    request: DraftRequest,
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Draft a legal document.
    """
    try:
        # Verify user
        user = await get_current_user(token=credentials.credentials, db=db)

        # Generate draft
        draft = await draft_legal_document(
            doc_type=request.doc_type,
            facts=request.facts,
            target_language=request.language,
        )

        return {
            "doc_type": request.doc_type,
            "language": request.language,
            "draft": draft,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error drafting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error drafting document",
        )
