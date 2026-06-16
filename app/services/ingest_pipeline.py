import logging
import json
import re
from datetime import datetime
from app.extensions import db
from app.models.judgment import Judgment, Citation, CourtLevel
from app.services.anthropic_service import AnthropicService

logger = logging.getLogger(__name__)


class IngestPipeline:
    """Orchestrates judgment ingestion: parsing, cleaning, AI enrichment, embedding, citation extraction."""

    SUBJECT_MATTER_TAXONOMY = [
        'Contract', 'Tort', 'Criminal', 'Land Law', 'Company Law', 'Employment',
        'Constitutional', 'Administrative', 'Family', 'Probate', 'Bankruptcy',
        'Intellectual Property', 'Tax', 'Immigration', 'Banking', 'Insurance',
        'Shipping', 'Construction', 'Environment', 'Syariah Personal', 'Syariah Commercial'
    ]

    def __init__(self, anthropic_service=None):
        self.anthropic_service = anthropic_service or AnthropicService()
        self.stats = {
            'total': 0,
            'ingested': 0,
            'duplicates': 0,
            'errors': 0,
        }

    def process_judgment(self, raw_judgment_dict, index=None, total=None):
        """
        Main pipeline: raw dict → cleaned → enriched → embedded → stored.

        Args:
            raw_judgment_dict: Dict from scraper with citation, title, court_level, full_text, etc.
            index: Current position (for progress logging)
            total: Total count (for progress logging)

        Returns:
            Judgment object if successful, None otherwise
        """
        self.stats['total'] += 1

        try:
            # Step 1: Deduplication
            if self._check_duplicate(raw_judgment_dict):
                logger.info(f'Skipping duplicate: {raw_judgment_dict.get("citation")}')
                self.stats['duplicates'] += 1
                return None

            # Step 2: Text cleaning
            raw_judgment_dict = self._clean_text(raw_judgment_dict)

            # Step 3: AI enrichment (structured extraction)
            enriched = self._enrich_with_ai(raw_judgment_dict)

            # Step 4: Generate embedding
            embedding = self._generate_embedding(raw_judgment_dict['full_text'])

            # Step 5: Create TSVECTOR for full-text search
            search_vector = self._create_search_vector(
                raw_judgment_dict['title'],
                raw_judgment_dict['full_text'],
                raw_judgment_dict.get('language', 'en')
            )

            # Step 6: Create Judgment record
            judgment = Judgment(
                id=self._generate_id(),
                citation=raw_judgment_dict['citation'],
                title=raw_judgment_dict['title'],
                court_level=raw_judgment_dict['court_level'],
                court_location=raw_judgment_dict.get('court_location', 'Malaysia'),
                coram=enriched.get('coram', []),
                parties_plaintiff=raw_judgment_dict.get('parties_plaintiff', []),
                parties_defendant=raw_judgment_dict.get('parties_defendant', []),
                date_decided=raw_judgment_dict.get('date_decided'),
                date_delivered=raw_judgment_dict.get('date_delivered'),
                subject_matter=enriched.get('subject_matter', []),
                full_text=raw_judgment_dict['full_text'],
                summary_ai=enriched.get('summary_en'),
                summary_ai_bm=enriched.get('summary_bm'),
                outcome=enriched.get('outcome'),
                neutral_citation=raw_judgment_dict.get('neutral_citation'),
                mlj_citation=raw_judgment_dict.get('mlj_citation'),
                clj_citation=raw_judgment_dict.get('clj_citation'),
                amr_citation=raw_judgment_dict.get('amr_citation'),
                mlra_citation=raw_judgment_dict.get('mlra_citation'),
                law_report_refs=raw_judgment_dict.get('law_report_refs', {}),
                embedding=embedding,
                search_vector=search_vector,
                source_url=raw_judgment_dict.get('source_url'),
                is_published=True,
                language=raw_judgment_dict.get('language', 'en'),
            )

            db.session.add(judgment)
            db.session.flush()  # Get ID without committing

            # Step 6: Extract and create citation relationships
            cited_judgments = enriched.get('cited_judgments', [])
            self._create_citations(judgment.id, cited_judgments)

            db.session.commit()

            progress = ''
            if index is not None and total is not None:
                progress = f'{index + 1}/{total} — '

            logger.info(f'[INGEST] {progress}Ingested: {judgment.citation} ({judgment.court_level.value})')
            self.stats['ingested'] += 1
            return judgment

        except Exception as e:
            logger.error(f'Error processing judgment: {e}')
            db.session.rollback()
            self.stats['errors'] += 1
            return None

    def _check_duplicate(self, raw_judgment_dict):
        """Check if judgment already exists."""
        citation = raw_judgment_dict.get('citation')
        court_level = raw_judgment_dict.get('court_level')

        existing = Judgment.query.filter_by(
            citation=citation,
            court_level=court_level
        ).first()
        return existing is not None

    def _clean_text(self, raw_judgment_dict):
        """Clean judgment text: strip boilerplate, normalize spacing."""
        full_text = raw_judgment_dict.get('full_text', '')

        # Remove multiple spaces
        full_text = re.sub(r'\s+', ' ', full_text)

        # Remove common boilerplate (adjust based on actual judgment format)
        boilerplate_patterns = [
            r'(Printed and published by|Percetakan Negara Malaysia|Ministry of Justice)',
            r'(^ENDORSED.*?^$)',
        ]
        for pattern in boilerplate_patterns:
            full_text = re.sub(pattern, '', full_text, flags=re.MULTILINE | re.IGNORECASE)

        raw_judgment_dict['full_text'] = full_text.strip()
        return raw_judgment_dict

    def _enrich_with_ai(self, raw_judgment_dict):
        """Use Anthropic API for structured extraction."""
        full_text = raw_judgment_dict['full_text']
        title = raw_judgment_dict['title']

        # Build comprehensive extraction prompt
        extraction_prompt = f"""Analyse this Malaysian court judgment and extract structured information.

JUDGMENT:
Title: {title}
Text: {full_text[:5000]}...

Return ONLY valid JSON with these fields:
{{
  "summary_en": "200-word plain English summary",
  "summary_bm": "200-word Bahasa Malaysia summary",
  "subject_matter": ["one", "or", "more", "from: {', '.join(self.SUBJECT_MATTER_TAXONOMY)}"],
  "outcome": "allowed|dismissed|partly_allowed|struck_out",
  "coram": [{{"name": "Judge Name", "title": "title"}}],
  "statutes_cited": [{{"act_name": "Act Name", "sections": ["1", "2"]}}],
  "cited_judgments": [{{"citation": "[YYYY] X CLJ Y", "relationship": "followed|distinguished|overruled|considered|referred|approved"}}]
}}

Return ONLY the JSON object, no other text."""

        try:
            response = self.anthropic_service.extract_judgment_metadata(extraction_prompt)
            enriched = json.loads(response)
            return enriched
        except Exception as e:
            logger.warning(f'AI enrichment failed: {e}. Using fallback.')
            return {
                'summary_en': '',
                'summary_bm': '',
                'subject_matter': [],
                'outcome': None,
                'coram': [],
                'statutes_cited': [],
                'cited_judgments': [],
            }

    def _generate_embedding(self, text):
        """Generate 1536-dim embedding using Anthropic or sentence-transformers."""
        try:
            embedding = self.anthropic_service.generate_embedding(text[:2000])
            return embedding
        except Exception as e:
            logger.warning(f'Embedding generation failed: {e}')
            return None

    def _create_search_vector(self, title, full_text, language='en'):
        """Create PostgreSQL TSVECTOR string."""
        # This would be used in a SQL trigger or UPDATE statement
        # For now, return the combined text
        combined = f'{title} {full_text}'
        return combined[:10000]  # Truncate for storage

    def _generate_id(self):
        """Generate UUID for judgment."""
        import uuid
        return str(uuid.uuid4())

    def _create_citations(self, citing_judgment_id, cited_judgments):
        """Create Citation records for judgment relationships."""
        from app.models.judgment import CitationRelationship

        for cited in cited_judgments:
            citation_str = cited.get('citation')
            relationship_str = cited.get('relationship', 'considered')

            # Find cited judgment in DB
            cited_judgment = Judgment.query.filter_by(citation=citation_str).first()
            if not cited_judgment:
                # Try to find by partial match
                cited_judgment = Judgment.query.filter(
                    Judgment.citation.ilike(f'%{citation_str}%')
                ).first()

            if cited_judgment:
                try:
                    relationship = CitationRelationship[relationship_str.upper()]
                    citation = Citation(
                        citing_judgment_id=citing_judgment_id,
                        cited_judgment_id=cited_judgment.id,
                        relationship=relationship,
                    )
                    db.session.add(citation)
                except Exception as e:
                    logger.debug(f'Failed to create citation: {e}')

    def get_stats(self):
        """Return ingestion statistics."""
        return self.stats

    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            'total': 0,
            'ingested': 0,
            'duplicates': 0,
            'errors': 0,
        }
