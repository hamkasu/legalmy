import logging
import json
from anthropic import Anthropic

logger = logging.getLogger(__name__)

client = Anthropic()

async def assess_case(facts: str, claim_type: str, court: str) -> dict:
    """
    Assess a case using Claude Sonnet.

    Args:
        facts: Case facts
        claim_type: Type of claim
        court: Court jurisdiction

    Returns:
        Assessment dictionary with keys:
        - success_probability
        - key_strengths
        - key_risks
        - recommended_cause_of_action
        - relevant_statutes
        - similar_cases_to_research
    """
    try:
        system_prompt = """You are a senior Malaysian litigation counsel.
Assess cases based on Malaysian law, statutes, and precedent.
Always cite relevant Malaysian cases and legislation.
Structure your response as JSON only."""

        user_prompt = f"""Facts: {facts}

Claim Type: {claim_type}

Court: {court}

Return JSON with keys:
success_probability (0-100),
key_strengths (list),
key_risks (list),
recommended_cause_of_action (str),
relevant_statutes (list),
similar_cases_to_research (list of case names)"""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        # Extract JSON from response
        response_text = message.content[0].text

        # Try to parse JSON
        try:
            # Handle markdown code blocks if present
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text

            assessment = json.loads(json_str)
            return assessment
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON response: {response_text}")
            return {
                "success_probability": 50,
                "key_strengths": [],
                "key_risks": [],
                "recommended_cause_of_action": "Review needed",
                "relevant_statutes": [],
                "similar_cases_to_research": [],
                "raw_response": response_text,
            }

    except Exception as e:
        logger.error(f"Error assessing case: {e}")
        raise
