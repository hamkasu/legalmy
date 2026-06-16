import re
from typing import Optional

JUDGE_TITLES = [
    "YA", "YAA", "Dato'", "Datin", "Tan Sri", "Dato Sri",
    "Justice", "Hakim", "Puan", "Encik"
]

PRACTICE_AREA_KEYWORDS = {
    "criminal": ["criminal", "culpable homicide", "theft", "rape", "murder", "penal code", "daripada"],
    "civil": ["negligence", "tort", "contract", "breach", "damages", "plaintiff", "defendant"],
    "commercial": ["company", "winding up", "shareholder", "commercial", "insolvent", "bankruptcy"],
    "family": ["divorce", "custody", "matrimonial", "conjugal", "marital", "separation", "talaq"],
    "land": ["land", "indefeasibility", "caveat", "property", "title", "registration"],
    "employment": ["dismissal", "reinstatement", "ILRA", "employment", "labour", "termination"],
    "syariah": ["syariah", "faraid", "hibah", "talaq", "islamic", "waqaf"],
}

def normalise_judge_name(raw_name: str) -> str:
    """
    Normalise judge name by stripping titles and standardising format.
    """
    if not raw_name:
        return ""

    name = raw_name.strip()

    # Remove titles (case-insensitive)
    for title in JUDGE_TITLES:
        name = re.sub(rf'\b{re.escape(title)}\b', '', name, flags=re.IGNORECASE)

    # Lowercase and strip whitespace
    name = name.lower().strip()

    # Remove punctuation except hyphens and spaces
    name = re.sub(r'[^\w\s\-]', '', name)

    # Collapse multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()

    return name

def normalise_case_number(raw: str) -> str:
    """
    Normalise case number to standard Malaysian format.
    E.g. WA-22NCvC-123-05/2023
    """
    if not raw:
        return ""

    # Strip whitespace and uppercase
    case_number = raw.strip().upper()

    return case_number

def detect_practice_area(text: str) -> str:
    """
    Detect practice area from case text using keyword matching.
    """
    if not text:
        return "other"

    text_lower = text.lower()

    # Check each practice area in order of specificity
    for area, keywords in PRACTICE_AREA_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return area

    return "other"
