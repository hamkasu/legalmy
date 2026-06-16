import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

client = Anthropic()

async def summarise_judgment(full_text: str, language: str = "en") -> str:
    """
    Summarise a judgment using Claude Sonnet.

    Args:
        full_text: Full judgment text
        language: Language code (en=English, bm=Bahasa Malaysia)

    Returns:
        Summarised judgment text
    """
    try:
        # Truncate to first 8000 characters
        text_excerpt = full_text[:8000] if full_text else ""

        language_name = "English" if language == "en" else "Bahasa Malaysia"

        system_prompt = f"""You are a Malaysian legal analyst. Summarise judgments concisely
for legal practitioners. Extract: ratio decidendi, key statutory
provisions applied, outcome, notable dicta.
Respond in {language_name} (en=English, bm=Bahasa Malaysia)."""

        user_prompt = f"""{text_excerpt}

Provide a structured summary with sections:
Facts, Issues, Decision, Ratio, Provisions Applied."""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return message.content[0].text

    except Exception as e:
        logger.error(f"Error summarising judgment: {e}")
        raise
