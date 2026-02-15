"""
Anti-Hallucination Filter
Scans LLM persona output before it enters the conversation.
Catches sensitive data the LLM may have invented (OTPs, bank accounts, etc).
"""

import re
from src.utils import logger

# Only catch patterns that are clearly sensitive data, not casual numbers
PATTERNS = {
    "OTP/PIN codes": r'\b(?:OTP|otp|pin|PIN|code)[\s:]*(\d{4,6})\b',
    "Phone numbers": r'(\+91[\s-]?\d{10}|\b\d{10}\b)',
    "Bank accounts": r'\b\d{11,18}\b',
    "UPI IDs": r'\b[\w\.-]+@(?:paytm|okaxis|okhdfcbank|oksbi|okicici|ybl|upi)\b',
    "URLs": r'https?://[^\s]+',
}

REPLACEMENTS = {
    "OTP/PIN codes": "some code",
    "Phone numbers": "a phone number",
    "Bank accounts": "some digits",
    "UPI IDs": "an ID",
    "URLs": "a link",
}


def filter_hallucinated_data(persona_response: str) -> tuple[str, dict]:
    report = {}
    cleaned = persona_response

    for category, pattern in PATTERNS.items():
        matches = re.findall(pattern, cleaned)
        matches = [m if isinstance(m, str) else m[0] for m in matches]
        matches = [m for m in matches if m.strip()]

        if matches:
            report[category] = matches
            cleaned = re.sub(pattern, REPLACEMENTS[category], cleaned)

    return cleaned, report


def validate_persona_output(persona_response: str) -> tuple[str, bool]:
    cleaned, report = filter_hallucinated_data(persona_response)

    if report:
        logger.warning(f"Hallucination filter triggered: {report}")
        return cleaned, True

    return persona_response, False
