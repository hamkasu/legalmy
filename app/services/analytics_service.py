import logging
from datetime import datetime
from sqlalchemy import func, and_, cast, Integer
from app.extensions import db
from app.models.judge import Judge, JudgeAnalytics
from app.models.judgment import Judgment, Citation, CourtLevel
from app.models.case import Case, Party
from app.services.anthropic_service import AnthropicService

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Computes judge analytics and ruling statistics."""

    def __init__(self):
        self.anthropic_service = AnthropicService()

    def compute_judge_analytics(self, judge_id):
        """
        Compute comprehensive analytics for a judge.

        Queries all judgments where judge appears in coram, calculates:
        - Total cases
        - Cases by court level and year
        - Cases by subject matter
        - Win rates (plaintiff/defendant perspective)
        - Average days to judgment
        - Most cited statutes
        - Most common opposing counsel
        - Landmark judgments (cited 10+ times)

        Args:
            judge_id: Judge ID

        Returns:
            JudgeAnalytics object (saved to DB)
        """
        judge = Judge.query.get(judge_id)
        if not judge:
            logger.error(f'Judge {judge_id} not found')
            return None

        try:
            # Find all judgments where this judge is in coram
            # coram is a JSONB array of {name: "Judge Name", title: "title"}
            judgments = db.session.query(Judgment).filter(
                Judgment.coram.contains([{'name': judge.full_name}])
            ).all()

            if not judgments:
                logger.info(f'No judgments found for judge {judge.full_name}')
                return None

            # 1. Total cases
            total_cases = len(judgments)

            # 2. Cases by court level
            cases_by_court_level = {}
            for judgment in judgments:
                level = judgment.court_level.value if judgment.court_level else 'Unknown'
                cases_by_court_level[level] = cases_by_court_level.get(level, 0) + 1

            # 3. Cases by year
            cases_by_year = {}
            for judgment in judgments:
                if judgment.date_decided:
                    year = judgment.date_decided.year
                    cases_by_year[str(year)] = cases_by_year.get(str(year), 0) + 1

            # 4. Cases by subject matter
            subject_breakdown = {}
            for judgment in judgments:
                for subject in judgment.subject_matter or []:
                    subject_breakdown[subject] = subject_breakdown.get(subject, 0) + 1

            # 5. Outcome breakdown
            outcome_breakdown = {}
            allowed_count = 0
            dismissed_count = 0

            for judgment in judgments:
                if judgment.outcome:
                    outcome = judgment.outcome.value
                    outcome_breakdown[outcome] = outcome_breakdown.get(outcome, 0) + 1
                    if outcome == 'allowed':
                        allowed_count += 1
                    elif outcome == 'dismissed':
                        dismissed_count += 1

            # 6. Plaintiff win rate (from plaintiff perspective)
            plaintiff_win_rate = None
            if allowed_count + dismissed_count > 0:
                plaintiff_win_rate = (allowed_count / (allowed_count + dismissed_count)) * 100

            # 7. Defendant win rate
            defendant_win_rate = None
            if allowed_count + dismissed_count > 0:
                defendant_win_rate = (dismissed_count / (allowed_count + dismissed_count)) * 100

            # 8. Average days to judgment
            avg_days_to_judgment = self._compute_avg_days_to_judgment(judgments)

            # 9. Most cited statutes
            most_cited_statutes = self._extract_most_cited_statutes(judgments)

            # 10. Most common counsel
            most_common_counsel = self._extract_most_common_counsel(judgments)

            # 11. Landmark judgments (cited 10+ times)
            landmark_judgments = self._find_landmark_judgments(judgments, min_citations=10)

            # Create or update JudgeAnalytics record
            analytics = JudgeAnalytics.query.filter_by(judge_id=judge_id).first()
            if not analytics:
                analytics = JudgeAnalytics(judge_id=judge_id)

            analytics.total_cases = total_cases
            analytics.plaintiff_win_rate = plaintiff_win_rate
            analytics.defendant_win_rate = defendant_win_rate
            analytics.avg_days_to_judgment = avg_days_to_judgment
            analytics.subject_matter_breakdown = subject_breakdown
            analytics.cases_by_year = cases_by_year
            analytics.cases_by_court_level = cases_by_court_level
            analytics.most_cited_statutes = most_cited_statutes
            analytics.landmark_judgments = landmark_judgments
            analytics.motion_grant_rates = {}  # Placeholder for future motion-specific analysis
            analytics.computed_at = datetime.utcnow()

            db.session.add(analytics)
            db.session.commit()

            logger.info(f'Computed analytics for judge {judge.full_name}: {total_cases} cases')
            return analytics

        except Exception as e:
            logger.error(f'Error computing analytics for judge {judge_id}: {e}')
            db.session.rollback()
            return None

    def _compute_avg_days_to_judgment(self, judgments):
        """Compute average days from filing to judgment."""
        total_days = 0
        count = 0

        for judgment in judgments:
            # Get linked case
            case = Case.query.filter_by(judgment_id=judgment.id).first()
            if case and case.filing_date and judgment.date_decided:
                days = (judgment.date_decided - case.filing_date).days
                if days > 0:
                    total_days += days
                    count += 1

        if count > 0:
            return total_days / count
        return None

    def _extract_most_cited_statutes(self, judgments, limit=10):
        """Extract most frequently cited acts/sections."""
        statute_counts = {}

        for judgment in judgments:
            # Parse statute references from full text (simple regex-based extraction)
            statutes = self._extract_statutes_from_text(judgment.full_text)
            for statute in statutes:
                statute_counts[statute] = statute_counts.get(statute, 0) + 1

        # Sort by frequency and return top N
        sorted_statutes = sorted(
            statute_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [{'statute': s[0], 'count': s[1]} for s in sorted_statutes]

    def _extract_statutes_from_text(self, text):
        """Extract statute citations from judgment text."""
        import re

        if not text:
            return []

        # Simple patterns for Malaysian statutes
        patterns = [
            r'(?:the\s+)?(\w+\s+Act\s+\d{4})',
            r'Section\s+(\d+)\s+of\s+the\s+(\w+\s+Act)',
            r'Article\s+(\d+)\s+of\s+the\s+(\w+)',
        ]

        statutes = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    statutes.add(' '.join(match))
                else:
                    statutes.add(match)

        return list(statutes)

    def _extract_most_common_counsel(self, judgments, limit=10):
        """Find lawyers appearing most frequently against this judge."""
        counsel_counts = {}

        for judgment in judgments:
            # Find cases linked to this judgment
            case = Case.query.filter_by(judgment_id=judgment.id).first()
            if case:
                parties = Party.query.filter_by(case_id=case.id).all()
                for party in parties:
                    if party.counsel_id:
                        counsel = party.counsel
                        if counsel:
                            key = f'{counsel.full_name} ({counsel.bar_council_number})'
                            counsel_counts[key] = counsel_counts.get(key, 0) + 1

        # Sort and return top N
        sorted_counsel = sorted(
            counsel_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [{'counsel': c[0], 'appearances': c[1]} for c in sorted_counsel]

    def _find_landmark_judgments(self, judgments, min_citations=10):
        """Find judgments in this list that are frequently cited."""
        landmark = []

        for judgment in judgments:
            # Count times this judgment is cited
            citation_count = Citation.query.filter_by(
                cited_judgment_id=judgment.id
            ).count()

            if citation_count >= min_citations:
                landmark.append({
                    'citation': judgment.citation,
                    'title': judgment.title,
                    'date_decided': judgment.date_decided.isoformat() if judgment.date_decided else None,
                    'citation_count': citation_count,
                })

        # Sort by citation count descending
        landmark.sort(key=lambda x: x['citation_count'], reverse=True)
        return landmark

    def generate_judge_insight(self, judge_id, use_cache=True):
        """
        Generate AI-powered insight into judge's ruling tendencies.

        Uses Anthropic API to generate 150-word analysis based on JudgeAnalytics.
        Cached in Redis for 24 hours.

        Args:
            judge_id: Judge ID
            use_cache: Use Redis cache if available

        Returns:
            Insight string
        """
        import redis
        import os

        judge = Judge.query.get(judge_id)
        analytics = JudgeAnalytics.query.filter_by(judge_id=judge_id).first()

        if not judge or not analytics:
            return None

        cache_key = f'judge_insight:{judge_id}'

        # Try cache
        if use_cache:
            try:
                redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
                r = redis.from_url(redis_url)
                cached = r.get(cache_key)
                if cached:
                    return cached.decode('utf-8')
            except Exception as e:
                logger.debug(f'Cache lookup failed: {e}')

        # Generate insight
        prompt = f"""Based on this judge's ruling statistics, write a 150-word insight into their
ruling tendencies and judicial philosophy:

Judge: {judge.display_name}
Court: {judge.court_level.value} at {judge.court_location}
Total Cases: {analytics.total_cases}
Plaintiff Win Rate: {analytics.plaintiff_win_rate:.1f}% if analytics.plaintiff_win_rate else 'N/A'
Defendant Win Rate: {analytics.defendant_win_rate:.1f}% if analytics.defendant_win_rate else 'N/A'
Avg Days to Judgment: {analytics.avg_days_to_judgment:.0f} days if analytics.avg_days_to_judgment else 'N/A'
Top Subject Matter: {', '.join(list(analytics.subject_matter_breakdown.keys())[:5]) if analytics.subject_matter_breakdown else 'N/A'}
Outcome Distribution: {analytics.cases_by_court_level}
Landmark Judgments (Cited 10+): {len(analytics.landmark_judgments)}

Focus on practical insights about their tendencies, not just statistics."""

        try:
            insight = self.anthropic_service.summarize_case(prompt)

            # Cache for 24 hours
            if use_cache:
                try:
                    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
                    r = redis.from_url(redis_url)
                    r.setex(cache_key, 86400, insight)
                except Exception as e:
                    logger.debug(f'Cache write failed: {e}')

            return insight
        except Exception as e:
            logger.error(f'Insight generation failed: {e}')
            return None
