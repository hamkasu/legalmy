import logging
from datetime import datetime
from typing import List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.case import Case
from app.models.judge import Judge
from app.models.judge_profile import JudgeProfile

logger = logging.getLogger(__name__)

async def compute_judge_profile(judge_id: str, db: AsyncSession) -> JudgeProfile:
    """
    Compute judge profile analytics from their cases.

    Args:
        judge_id: Judge ID
        db: AsyncSession

    Returns:
        JudgeProfile with computed metrics
    """
    try:
        # Query all cases for this judge
        result = await db.execute(
            select(Case).where(
                and_(
                    Case.judge_id == judge_id,
                    Case.outcome != "unknown"
                )
            )
        )
        cases = result.scalars().all()

        if not cases:
            logger.warning(f"No cases found for judge {judge_id}")
            return None

        # Compute total_decisions
        total_decisions = len(cases)

        # Compute plaintiff_favourable_rate
        plaintiff_wins = sum(1 for case in cases if case.outcome == "plaintiff_wins")
        plaintiff_favourable_rate = plaintiff_wins / total_decisions if total_decisions > 0 else None

        # Compute avg_disposal_days
        disposal_days = []
        for case in cases:
            if case.date_filed and case.date_decided:
                try:
                    # Parse dates if they're strings
                    if isinstance(case.date_filed, str):
                        filed = datetime.strptime(case.date_filed, "%Y-%m-%d")
                    else:
                        filed = case.date_filed

                    if isinstance(case.date_decided, str):
                        decided = datetime.strptime(case.date_decided, "%Y-%m-%d")
                    else:
                        decided = case.date_decided

                    days = (decided - filed).days
                    if days >= 0:
                        disposal_days.append(days)
                except Exception as e:
                    logger.debug(f"Error parsing dates for case {case.id}: {e}")
                    continue

        avg_disposal_days = (
            sum(disposal_days) / len(disposal_days) if disposal_days else None
        )

        # Compute top_practice_areas
        practice_area_counts = {}
        for case in cases:
            area = case.practice_area or "other"
            practice_area_counts[area] = practice_area_counts.get(area, 0) + 1

        top_practice_areas = sorted(
            practice_area_counts.items(), key=lambda x: x[1], reverse=True
        )[:3]
        top_practice_areas_str = ",".join([area for area, _ in top_practice_areas])

        # Compute interlocutory_grant_rate
        interlocutory_cases = [
            case for case in cases
            if case.full_text and "interlocutory" in case.full_text.lower()
        ]
        if interlocutory_cases:
            granted = sum(
                1 for case in interlocutory_cases
                if case.full_text
                and (
                    "injunction granted" in case.full_text.lower()
                    or "allowed" in case.full_text.lower()
                )
            )
            interlocutory_grant_rate = (
                granted / len(interlocutory_cases) if interlocutory_cases else None
            )
        else:
            interlocutory_grant_rate = None

        # Compute costs_awarded_rate
        costs_cases = [
            case for case in cases
            if case.full_text and "costs" in case.full_text.lower()
        ]
        if costs_cases:
            costs_awarded = sum(
                1 for case in costs_cases
                if case.full_text and "costs awarded" in case.full_text.lower()
            )
            costs_awarded_rate = (
                costs_awarded / len(costs_cases) if costs_cases else None
            )
        else:
            costs_awarded_rate = None

        # Get existing profile or create new one
        result = await db.execute(
            select(JudgeProfile).where(JudgeProfile.judge_id == judge_id)
        )
        profile = result.scalar_one_or_none()

        if profile:
            # Update existing profile
            profile.total_decisions = total_decisions
            profile.plaintiff_favourable_rate = plaintiff_favourable_rate
            profile.avg_disposal_days = avg_disposal_days
            profile.interlocutory_grant_rate = interlocutory_grant_rate
            profile.costs_awarded_rate = costs_awarded_rate
            profile.top_practice_areas = top_practice_areas_str
            profile.last_computed_at = datetime.utcnow().isoformat()
        else:
            # Create new profile
            profile = JudgeProfile(
                judge_id=judge_id,
                total_decisions=total_decisions,
                plaintiff_favourable_rate=plaintiff_favourable_rate,
                avg_disposal_days=avg_disposal_days,
                interlocutory_grant_rate=interlocutory_grant_rate,
                costs_awarded_rate=costs_awarded_rate,
                top_practice_areas=top_practice_areas_str,
                last_computed_at=datetime.utcnow().isoformat(),
            )
            db.add(profile)

        await db.commit()
        await db.refresh(profile)

        logger.info(f"Computed profile for judge {judge_id} with {total_decisions} cases")
        return profile

    except Exception as e:
        logger.error(f"Error computing profile for judge {judge_id}: {e}")
        await db.rollback()
        return None

async def recompute_all_profiles(db: AsyncSession) -> int:
    """
    Recompute profiles for all judges with at least 5 cases.

    Args:
        db: AsyncSession

    Returns:
        Number of profiles updated
    """
    try:
        # Get all judges with at least 5 cases
        result = await db.execute(
            select(Case.judge_id, func.count(Case.id).label("case_count"))
            .where(Case.judge_id.isnot(None))
            .group_by(Case.judge_id)
            .having(func.count(Case.id) >= 5)
        )
        judge_cases = result.all()

        updated_count = 0
        for judge_id, case_count in judge_cases:
            try:
                profile = await compute_judge_profile(judge_id, db)
                if profile:
                    updated_count += 1
            except Exception as e:
                logger.error(f"Error computing profile for judge {judge_id}: {e}")
                continue

        logger.info(f"Recomputed {updated_count} judge profiles")
        return updated_count

    except Exception as e:
        logger.error(f"Error in recompute_all_profiles: {e}")
        await db.rollback()
        return 0
