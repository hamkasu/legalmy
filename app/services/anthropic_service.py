import os
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AnthropicService:
    """Wrapper around Anthropic API for LegalMY."""

    def __init__(self):
        self.client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        self.model = 'claude-opus-4-8'

    def extract_judgment_metadata(self, prompt):
        """
        Use Claude to extract structured metadata from judgment text.

        Args:
            prompt: Extraction prompt with judgment content

        Returns:
            JSON string with extracted metadata
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f'Anthropic API error: {e}')
            raise

    def generate_embedding(self, text):
        """
        Generate embedding for text using Claude.
        Note: Claude doesn't have native embeddings endpoint.
        Falls back to returning None - actual embeddings should use
        sentence-transformers (multilingual-e5-large) as per Prompt 03.

        Args:
            text: Text to embed

        Returns:
            None (should be implemented with sentence-transformers)
        """
        # In production, use: sentence-transformers.SentenceTransformer('intfloat/multilingual-e5-large')
        # For now, return None to skip embedding generation
        logger.debug(f'Embedding generation not implemented. Text length: {len(text)}')
        return None

    def summarize_case(self, case_text):
        """
        Generate plain-language case summary.

        Args:
            case_text: Full case text

        Returns:
            Summary string
        """
        prompt = f"""Summarize this Malaysian court case in plain English (200 words),
suitable for a lawyer unfamiliar with the area:

{case_text[:3000]}

Return only the summary text, no other commentary."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f'Summary generation failed: {e}')
            return None

    def generate_legal_argument(self, case_facts, role, subject_matter):
        """
        Generate legal arguments based on case facts and similar cases.

        Args:
            case_facts: Description of case facts
            role: plaintiff, defendant, appellant, or respondent
            subject_matter: Practice area (e.g., 'Contract', 'Tort')

        Returns:
            Generated argument text
        """
        prompt = f"""You are a senior Malaysian litigation lawyer. Generate 3-5 primary
legal arguments for a {role} in a {subject_matter} case with these facts:

{case_facts}

For each argument, provide:
1. Argument heading
2. Legal basis (Malaysian statutes and cases)
3. Supporting case citations
4. Counter-argument anticipation

Format as structured text with clear sections."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f'Argument generation failed: {e}')
            return None

    def explain_legislation(self, section_text, act_name):
        """
        Generate plain-language explanation of legislation.

        Args:
            section_text: Section content
            act_name: Name of Act

        Returns:
            Explanation text
        """
        prompt = f"""Explain this section of Malaysian law in plain English, as if to an
educated non-lawyer:

Act: {act_name}
Section text: {section_text}

Include:
1. Plain English explanation
2. Real-world examples
3. Common misconceptions
4. Recent case law interpreting this section
5. Practical pitfalls"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f'Explanation generation failed: {e}')
            return None

    def analyze_case_strength(self, pleading_text, role):
        """
        Analyse case strength from pleading documents.

        Args:
            pleading_text: Writ of Summons or Statement of Claim text
            role: plaintiff or defendant

        Returns:
            Case strength analysis
        """
        prompt = f"""You are a senior Malaysian litigation lawyer with 20 years experience.
Analyse the case strength (1-10 scale) for the {role} based on this pleading:

{pleading_text[:4000]}

Provide:
1. Case strength rating (1-10 with justification)
2. Key causes of action identified
3. Potential defences the other side will raise
4. Risks and weaknesses
5. Recommended next steps (action plan)"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f'Case analysis failed: {e}')
            return None
