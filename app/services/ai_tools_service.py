import logging
import json
import re
from datetime import datetime, timedelta
from app.extensions import db
from app.models.judgment import Judgment
from app.models.lawyer import Lawyer, LawyerAnalytics
from app.models.legislation import Act, Section
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AIToolsService:
    """Comprehensive AI tools for legal professionals using Anthropic API."""

    def __init__(self, api_key=None):
        self.client = Anthropic(api_key=api_key)
        self.model = 'claude-opus-4-8'

    def analyze_case(self, pleading_text, user_role='plaintiff'):
        """
        Tool 1: Case Analyser
        Analyzes a Writ of Summons or Statement of Claim.

        Args:
            pleading_text: Full text of pleading document
            user_role: 'plaintiff', 'defendant', 'appellant', 'respondent'

        Returns:
            Dict with: case_strength, causes_of_action, potential_defences,
                      next_steps, risk_factors, similar_cases
        """
        prompt = f"""You are a senior Malaysian litigation lawyer with 20 years of experience in Malaysian courts.
Analyse this pleading under Malaysian law and provide a comprehensive case assessment:

PLEADING:
{pleading_text[:5000]}

Your role: {user_role}

Provide analysis in JSON format:
{{
  "case_strength": {{"rating": 1-10, "justification": "explanation"}},
  "causes_of_action": [
    {{"cause": "name", "statute": "Malaysian Act reference", "elements_met": true/false}}
  ],
  "potential_defences": ["defence 1", "defence 2", ...],
  "next_steps": [
    {{"step": 1, "action": "description", "timeline": "timeframe"}},
    ...
  ],
  "risk_factors": ["risk 1", "risk 2", ...],
  "weaknesses": ["weakness 1", "weakness 2", ...],
  "recommended_reliefs": ["relief 1", "relief 2", ...]
}}

Return ONLY the JSON object."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return json.loads(response.content[0].text)
        except Exception as e:
            logger.error(f'Case analysis failed: {e}')
            return {'error': str(e)}

    def summarize_judgment(self, judgment_text, language='en'):
        """
        Tool 2: Judgment Summariser
        Summarizes a full judgment in structured format.

        Args:
            judgment_text: Full text of judgment
            language: 'en' or 'bm'

        Returns:
            Dict with: executive_summary, facts, legal_issues, reasoning,
                      decision, significance, statutes_cited, cases_cited
        """
        lang_instruction = "English" if language == 'en' else "Bahasa Malaysia"

        prompt = f"""Summarize this Malaysian court judgment in {lang_instruction}.

JUDGMENT:
{judgment_text[:6000]}

Provide analysis in JSON format:
{{
  "executive_summary": "3-sentence overview",
  "facts": ["fact 1", "fact 2", ...],
  "legal_issues": ["issue 1", "issue 2", ...],
  "court_reasoning": "explanation of court's logic",
  "decision": "judgment outcome and orders",
  "significance": "why this case matters",
  "obiter_dicta": "any significant commentary beyond ratio decidendi",
  "statutes_cited": ["Act 1", "Act 2", ...],
  "cases_cited": ["[YYYY] X CLJ Y", ...],
  "key_principles": ["principle 1", "principle 2", ...]
}}

Return ONLY the JSON object."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return json.loads(response.content[0].text)
        except Exception as e:
            logger.error(f'Judgment summarization failed: {e}')
            return {'error': str(e)}

    def generate_legal_arguments(self, case_facts, user_role, subject_matter):
        """
        Tool 3: Legal Argument Generator
        Generates primary legal arguments with supporting case law.

        Args:
            case_facts: Description of case facts
            user_role: 'plaintiff', 'defendant', 'appellant', 'respondent'
            subject_matter: Legal area (e.g., 'Contract', 'Tort', 'Employment')

        Returns:
            Dict with: arguments, recommended_reliefs, affidavit_structure
        """
        # Search for similar cases
        similar_cases = self._search_similar_judgments(case_facts, subject_matter)

        case_context = ""
        if similar_cases:
            case_context = "\n\nSupporting Malaysian cases:\n" + "\n".join(
                [f"- {c['citation']}: {c['summary']}" for c in similar_cases[:5]]
            )

        prompt = f"""You are a senior Malaysian litigation lawyer. Generate primary legal arguments
for a {user_role} in a {subject_matter} case with these facts:

CASE FACTS:
{case_facts}

{case_context}

Provide 3-5 primary arguments in JSON format:
{{
  "arguments": [
    {{
      "heading": "argument title",
      "legal_basis": "Malaysian statutes and common law principles",
      "supporting_cases": ["[YYYY] X CLJ Y", ...],
      "statute_references": [{{"act": "Act name", "sections": ["1", "2"]}}],
      "counter_arguments": "anticipated defences and responses"
    }},
    ...
  ],
  "recommended_reliefs": ["relief 1", "relief 2", ...],
  "affidavit_structure": ["section 1", "section 2", ...]
}}

Return ONLY the JSON object."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return json.loads(response.content[0].text)
        except Exception as e:
            logger.error(f'Argument generation failed: {e}')
            return {'error': str(e)}

    def build_case_timeline(self, document_texts):
        """
        Tool 4: Case Timeline Builder
        Extracts dates and events from documents.

        Args:
            document_texts: List of document text strings

        Returns:
            Dict with: events (sorted by date)
        """
        combined_text = "\n---\n".join(document_texts)

        prompt = f"""Extract all dates and events from these case documents.
For each event, identify the date and categorize by type:
- 'court_date': hearing, judgment, or court action
- 'deadline': filing deadline, response deadline
- 'event': event in dispute (accident, contract signing, etc.)

DOCUMENTS:
{combined_text[:6000]}

Return JSON:
{{
  "events": [
    {{
      "date": "YYYY-MM-DD",
      "type": "court_date|deadline|event",
      "title": "event title",
      "description": "details"
    }},
    ...
  ]
}}

Return ONLY the JSON object."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{'role': 'user', 'content': prompt}]
            )
            result = json.loads(response.content[0].text)
            # Sort events by date
            result['events'].sort(key=lambda x: x['date'])
            return result
        except Exception as e:
            logger.error(f'Timeline building failed: {e}')
            return {'error': str(e)}

    def research_opposing_counsel(self, counsel_name, court_level=None):
        """
        Tool 5: Opposing Counsel Research
        Generates strategic briefing on an opposing lawyer.

        Args:
            counsel_name: Full name or bar council number
            court_level: Optional court restriction

        Returns:
            Dict with: record, win_loss, common_arguments, recent_cases,
                      strategic_weaknesses, recommended_approach
        """
        # Query LawyerAnalytics
        lawyer = Lawyer.query.filter(
            (Lawyer.full_name.ilike(f'%{counsel_name}%')) |
            (Lawyer.bar_council_number.ilike(f'%{counsel_name}%'))
        ).first()

        if not lawyer:
            return {'error': f'Counsel "{counsel_name}" not found in database'}

        analytics = LawyerAnalytics.query.filter_by(lawyer_id=lawyer.id).first()

        if not analytics:
            return {'error': f'No analytics available for {lawyer.full_name}'}

        prompt = f"""Generate a strategic briefing on this opposing counsel based on their litigation record.

COUNSEL PROFILE:
- Name: {lawyer.full_name}
- Bar Council: {lawyer.bar_council_number}
- Total Appearances: {analytics.total_appearances}
- Win Rate (Plaintiff): {analytics.win_rate_plaintiff or 'N/A'}%
- Win Rate (Defendant): {analytics.win_rate_defendant or 'N/A'}%
- Specialisations: {', '.join(lawyer.specialisations) if lawyer.specialisations else 'General'}
- Court Breakdown: {analytics.court_breakdown}

Provide strategic briefing:
{{
  "win_loss_record": {{"total": number, "wins": number, "losses": number}},
  "common_arguments": ["argument 1", "argument 2", ...],
  "court_expertise": "which courts they're strongest in",
  "strategic_weaknesses": ["weakness 1", "weakness 2", ...],
  "recommended_approach": "how to prepare when facing this counsel",
  "precedent_tactics": "what arguments they've used successfully"
}}

Return ONLY the JSON object."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{'role': 'user', 'content': prompt}]
            )
            briefing = json.loads(response.content[0].text)
            briefing['counsel'] = {
                'name': lawyer.full_name,
                'bar_council': lawyer.bar_council_number,
                'specialisations': lawyer.specialisations,
            }
            return briefing
        except Exception as e:
            logger.error(f'Counsel research failed: {e}')
            return {'error': str(e)}

    def explain_legislation(self, section_text, act_name=None, language='en'):
        """
        Tool 6: Legislation Plain Language Explainer
        Explains statutes in plain language with examples.

        Args:
            section_text: Full text of section
            act_name: Optional Act name for context
            language: 'en' or 'bm'

        Returns:
            Dict with: plain_explanation, examples, pitfalls, cases,
                      amendments
        """
        lang = "English" if language == 'en' else "Bahasa Malaysia"

        prompt = f"""Explain this Malaysian statute section in plain {lang},
as if to an educated non-lawyer (not a law student):

ACT: {act_name or 'Unknown'}
SECTION TEXT:
{section_text}

Provide explanation:
{{
  "plain_explanation": "1-2 paragraph explanation in simple language",
  "practical_examples": [
    {{"scenario": "real-world example", "application": "how the law applies"}}
  ],
  "common_pitfalls": ["pitfall 1", "pitfall 2", ...],
  "recent_cases": ["[YYYY] X CLJ Y: key interpretation", ...],
  "amendments": "any recent changes and what they mean",
  "key_requirements": ["requirement 1", "requirement 2", ...],
  "penalties": "what happens if breached"
}}

Return ONLY the JSON object."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return json.loads(response.content[0].text)
        except Exception as e:
            logger.error(f'Legislation explanation failed: {e}')
            return {'error': str(e)}

    def _search_similar_judgments(self, query_text, subject_matter, limit=5):
        """Helper: Search for similar judgments by subject matter and facts."""
        judgments = Judgment.query.filter(
            Judgment.subject_matter.overlap([subject_matter])
        ).order_by(Judgment.date_decided.desc()).limit(limit).all()

        return [
            {
                'citation': j.citation,
                'title': j.title,
                'summary': j.summary_ai or j.title[:100],
                'date': j.date_decided.isoformat() if j.date_decided else None,
            }
            for j in judgments
        ]
