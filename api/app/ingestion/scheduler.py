import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def daily_ecourt_scrape():
    """
    Daily job to scrape e-Court cause lists for all active courts.
    Runs at 06:00 MYT every day.
    """
    try:
        from app.ingestion.ecourt_scraper import scrape_cause_list, COURTS
        from app.database import AsyncSessionLocal
        from sqlalchemy import select
        from app.models.case import Case

        logger.info("Starting daily e-Court scrape")

        today = datetime.now().strftime("%Y-%m-%d")

        # Scrape all courts
        all_cases = []
        for court_code, court_name in COURTS.items():
            cases = await scrape_cause_list(today, court_code)
            all_cases.extend(cases)

        logger.info(f"Scraped {len(all_cases)} cases total")

        # Upsert cases to database
        async with AsyncSessionLocal() as db:
            for case_data in all_cases:
                # Check if case exists
                result = await db.execute(
                    select(Case).where(Case.case_number == case_data["case_number"])
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    case = Case(
                        title=f"{case_data['parties']} - {today}",
                        case_number=case_data["case_number"],
                        date_filed=today,
                        source="ecourt",
                        is_published=True,
                    )
                    db.add(case)

            await db.commit()
            logger.info(f"Upserted {len(all_cases)} cases to database")

    except Exception as e:
        logger.error(f"Error in daily_ecourt_scrape: {e}")

async def weekly_judge_profile_refresh():
    """
    Weekly job to recompute judge profile analytics.
    Runs at 02:00 MYT every Sunday.
    """
    try:
        logger.info("Starting weekly judge profile refresh")

        # This would call an analytics module (not yet implemented)
        # from app.analytics.judge_analytics import recompute_all_profiles
        # await recompute_all_profiles()

        logger.info("Completed weekly judge profile refresh")

    except Exception as e:
        logger.error(f"Error in weekly_judge_profile_refresh: {e}")

def start_scheduler():
    """
    Start the APScheduler with configured jobs.
    Call this from app lifespan.
    """
    if scheduler.running:
        return

    # Daily e-Court scrape at 06:00 MYT (UTC+8)
    scheduler.add_job(
        daily_ecourt_scrape,
        trigger=CronTrigger(hour=6, minute=0, timezone="Asia/Kuala_Lumpur"),
        id="daily_ecourt_scrape",
        name="Daily e-Court scrape",
    )

    # Weekly judge profile refresh at Sunday 02:00 MYT (UTC+8)
    scheduler.add_job(
        weekly_judge_profile_refresh,
        trigger=CronTrigger(day_of_week=6, hour=2, minute=0, timezone="Asia/Kuala_Lumpur"),
        id="weekly_judge_profile_refresh",
        name="Weekly judge profile refresh",
    )

    scheduler.start()
    logger.info("Scheduler started with background jobs")

def stop_scheduler():
    """
    Stop the scheduler.
    Call this from app lifespan shutdown.
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
