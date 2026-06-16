import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

client = Anthropic()

DOC_TYPES = ["writ", "statement_of_claim", "submission", "client_update", "demand_letter"]

async def draft_legal_document(
    doc_type: str,
    facts: str,
    target_language: str = "en"
) -> str:
    """
    Draft a legal document using Claude Sonnet.

    Args:
        doc_type: Type of document (writ, statement_of_claim, submission, client_update, demand_letter)
        facts: Facts for the document
        target_language: Language code (en=English, bm=Bahasa Malaysia)

    Returns:
        Drafted document text
    """
    try:
        if doc_type not in DOC_TYPES:
            raise ValueError(f"Invalid doc_type. Must be one of: {DOC_TYPES}")

        language_name = "English" if target_language == "en" else "Bahasa Malaysia"

        system_prompt = f"""You are a Malaysian legal drafter.
Use correct Malaysian court terminology and form.
Follow Malaysian Rules of Court 2012 conventions.
Draft in {language_name}."""

        user_prompt = f"""Document Type: {doc_type}

Facts: {facts}

Draft the complete document with proper headings and formatting."""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return message.content[0].text

    except Exception as e:
        logger.error(f"Error drafting document: {e}")
        raise
