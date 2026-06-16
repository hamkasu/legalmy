import logging
from datetime import datetime
from sqlalchemy import and_, or_, func, cast, Text
from sqlalchemy.dialects.postgresql import ARRAY
from app.extensions import db
from app.models.judgment import Judgment, CourtLevel, OutcomeType
from app.models.legislation import Act, Section
from app.models.judge import Judge
from app.models.lawyer import Lawyer, LawFirm

logger = logging.getLogger(__name__)


class SearchService:
    """Hybrid search engine: full-text + semantic with RRF ranking."""

    RRF_K = 60  # RRF constant

    def search_judgments(self, query, filters=None, page=1, per_page=20, semantic=True):
        """
        Hybrid search for judgments (full-text + semantic).

        Args:
            query: Search query string
            filters: Dict with optional filters:
                - court_level: list of CourtLevel enum values
                - court_location: list of states
                - date_from, date_to: date objects
                - subject_matter: list of tags
                - outcome: list of OutcomeType values
                - judge_id: judge ID
                - lawyer_id: lawyer ID
                - party_name: string to search in parties
                - citation: citation string
            page: Page number (1-indexed)
            per_page: Results per page (max 100)
            semantic: Enable semantic search (requires embeddings)

        Returns:
            Dict with keys: results, total_count, page, pages, facets
        """
        filters = filters or {}
        per_page = min(per_page, 100)

        # Build base query with filters
        base_query = Judgment.query.filter_by(is_published=True)
        base_query = self._apply_filters(base_query, filters)

        # Full-text search
        ft_results = self._full_text_search(base_query, query)

        # Semantic search (if query embeddings available)
        semantic_results = {}
        if semantic:
            semantic_results = self._semantic_search(base_query, query)

        # Merge using RRF
        merged_results = self._rrf_merge(ft_results, semantic_results)

        # Get unique judgment IDs in RRF rank order
        sorted_ids = [jid for jid, _ in merged_results]

        # Fetch full judgment objects in order
        if sorted_ids:
            judgments = db.session.query(Judgment).filter(
                Judgment.id.in_(sorted_ids)
            ).all()
            # Sort by sorted_ids order
            judgment_map = {j.id: j for j in judgments}
            results = [judgment_map[jid] for jid in sorted_ids if jid in judgment_map]
        else:
            results = []

        # Count total
        total_count = len(results)

        # Paginate
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = results[start_idx:end_idx]

        # Compute facets from all results (not paginated)
        facets = self._compute_facets(results)

        return {
            'results': paginated_results,
            'total_count': total_count,
            'page': page,
            'pages': (total_count + per_page - 1) // per_page,
            'facets': facets,
        }

    def _apply_filters(self, query, filters):
        """Apply all filter conditions to query."""
        if filters.get('court_level'):
            query = query.filter(Judgment.court_level.in_(filters['court_level']))

        if filters.get('court_location'):
            query = query.filter(Judgment.court_location.in_(filters['court_location']))

        if filters.get('date_from'):
            query = query.filter(Judgment.date_decided >= filters['date_from'])

        if filters.get('date_to'):
            query = query.filter(Judgment.date_decided <= filters['date_to'])

        if filters.get('subject_matter'):
            # Array overlap: subject_matter && ARRAY[...]
            query = query.filter(
                Judgment.subject_matter.overlap(filters['subject_matter'])
            )

        if filters.get('outcome'):
            query = query.filter(Judgment.outcome.in_(filters['outcome']))

        if filters.get('judge_id'):
            # Filter by coram (JSONB contains judge)
            judge_name = db.session.query(Judge.full_name).filter_by(
                id=filters['judge_id']
            ).scalar()
            if judge_name:
                query = query.filter(
                    Judgment.coram.contains([{'name': judge_name}])
                )

        if filters.get('party_name'):
            party = filters['party_name']
            query = query.filter(
                or_(
                    Judgment.parties_plaintiff.overlap([party]),
                    Judgment.parties_defendant.overlap([party])
                )
            )

        if filters.get('citation'):
            query = query.filter(
                Judgment.citation.ilike(f"%{filters['citation']}%")
            )

        return query

    def _full_text_search(self, base_query, query):
        """
        Full-text search using PostgreSQL tsvector.

        Returns:
            Dict: {judgment_id: (rank_score, headline)}
        """
        if not query or not query.strip():
            return {}

        from sqlalchemy import literal_column, func as sql_func

        # Convert query to tsquery using plainto_tsquery (phrase search)
        # We'll use a simple approach: search in title and full_text
        search_pattern = f"%{query}%"

        results = base_query.filter(
            or_(
                Judgment.title.ilike(search_pattern),
                Judgment.full_text.ilike(search_pattern)
            )
        ).all()

        # Score by position of match in title (title matches rank higher)
        ft_results = {}
        for rank, judgment in enumerate(results):
            title_match = query.lower() in judgment.title.lower()
            score = 1.0 / (1 + rank + (0 if title_match else 0.5))
            ft_results[judgment.id] = (score, judgment.title[:100])

        return ft_results

    def _semantic_search(self, base_query, query):
        """
        Semantic search using pgvector embeddings.

        Returns:
            Dict: {judgment_id: similarity_score}
        """
        # Stub: requires embedding generation for user query
        # In production: use sentence-transformers or Anthropic embeddings API
        logger.debug('Semantic search: embeddings not yet generated for query')
        return {}

    def _rrf_merge(self, ft_results, semantic_results):
        """
        Merge full-text and semantic rankings using Reciprocal Rank Fusion.

        RRF score = 1/(K + rank) summed across methods

        Returns:
            List of (judgment_id, rrf_score) sorted by score descending
        """
        all_ids = set(ft_results.keys()) | set(semantic_results.keys())
        rrf_scores = {}

        for jid in all_ids:
            score = 0.0
            if jid in ft_results:
                ft_rank = list(ft_results.keys()).index(jid) + 1
                score += 1.0 / (self.RRF_K + ft_rank)
            if jid in semantic_results:
                semantic_rank = list(semantic_results.keys()).index(jid) + 1
                score += 1.0 / (self.RRF_K + semantic_rank)
            rrf_scores[jid] = score

        # Sort by score descending
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results

    def _compute_facets(self, results):
        """Compute facet counts for search results."""
        facets = {
            'court_level': {},
            'subject_matter': {},
            'outcome': {},
            'year': {},
        }

        for judgment in results:
            # Court level
            level = judgment.court_level.value if judgment.court_level else 'Unknown'
            facets['court_level'][level] = facets['court_level'].get(level, 0) + 1

            # Subject matter
            for subject in judgment.subject_matter or []:
                facets['subject_matter'][subject] = facets['subject_matter'].get(subject, 0) + 1

            # Outcome
            outcome = judgment.outcome.value if judgment.outcome else 'Unknown'
            facets['outcome'][outcome] = facets['outcome'].get(outcome, 0) + 1

            # Year
            if judgment.date_decided:
                year = judgment.date_decided.year
                facets['year'][str(year)] = facets['year'].get(str(year), 0) + 1

        return facets

    def search_legislation(self, query, filters=None, page=1, per_page=20):
        """
        Search legislation (Acts and Sections).

        Args:
            query: Search query
            filters: Optional dict with act_id, category filters
            page: Page number
            per_page: Results per page

        Returns:
            Dict with results grouped by Act
        """
        filters = filters or {}
        per_page = min(per_page, 100)

        # Search sections
        search_pattern = f"%{query}%"
        sections_query = Section.query.filter(
            or_(
                Section.heading.ilike(search_pattern),
                Section.content.ilike(search_pattern)
            )
        )

        if filters.get('act_id'):
            sections_query = sections_query.filter_by(act_id=filters['act_id'])

        all_sections = sections_query.all()
        total_count = len(all_sections)

        # Paginate
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_sections = all_sections[start_idx:end_idx]

        # Group by Act
        results_by_act = {}
        for section in paginated_sections:
            act = section.act
            if act.id not in results_by_act:
                results_by_act[act.id] = {
                    'act': act,
                    'sections': []
                }
            results_by_act[act.id]['sections'].append(section)

        return {
            'results_by_act': results_by_act,
            'total_count': total_count,
            'page': page,
            'pages': (total_count + per_page - 1) // per_page,
        }

    def search_judges(self, query, filters=None, page=1, per_page=20):
        """Search judges by name, court, location."""
        filters = filters or {}
        per_page = min(per_page, 100)

        search_pattern = f"%{query}%"
        judges_query = Judge.query.filter(
            or_(
                Judge.full_name.ilike(search_pattern),
                Judge.court_location.ilike(search_pattern)
            )
        )

        if filters.get('court_level'):
            judges_query = judges_query.filter(Judge.court_level.in_(filters['court_level']))

        if filters.get('is_active') is not None:
            judges_query = judges_query.filter_by(is_active=filters['is_active'])

        all_judges = judges_query.all()
        total_count = len(all_judges)

        # Paginate
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_judges = all_judges[start_idx:end_idx]

        return {
            'results': paginated_judges,
            'total_count': total_count,
            'page': page,
            'pages': (total_count + per_page - 1) // per_page,
        }

    def search_lawyers(self, query, filters=None, page=1, per_page=20):
        """Search lawyers by name, firm, specialisations."""
        filters = filters or {}
        per_page = min(per_page, 100)

        search_pattern = f"%{query}%"
        lawyers_query = Lawyer.query.filter(
            or_(
                Lawyer.full_name.ilike(search_pattern),
                Lawyer.bar_council_number.ilike(search_pattern)
            )
        )

        if filters.get('specialisation'):
            lawyers_query = lawyers_query.filter(
                Lawyer.specialisations.overlap([filters['specialisation']])
            )

        if filters.get('firm_id'):
            lawyers_query = lawyers_query.filter_by(firm_id=filters['firm_id'])

        if filters.get('is_active') is not None:
            lawyers_query = lawyers_query.filter_by(is_active=filters['is_active'])

        all_lawyers = lawyers_query.all()
        total_count = len(all_lawyers)

        # Paginate
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_lawyers = all_lawyers[start_idx:end_idx]

        return {
            'results': paginated_lawyers,
            'total_count': total_count,
            'page': page,
            'pages': (total_count + per_page - 1) // per_page,
        }
