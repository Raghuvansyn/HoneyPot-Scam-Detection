# app/agents/hallucination_filter.py
"""
Anti-Hallucination Filter
--------------------------
Scans the LLM persona's output BEFORE it enters the conversation.
If the LLM accidentally generates sensitive data (OTPs, bank accounts,
UPI IDs, phone numbers, URLs), this filter catches and neutralizes it.

This is the ethical guardrail — our system must never leak realistic
sensitive information, even if the LLM hallucinates it.
"""

import re
from app.utils import logger


# ============================================
# REGEX PATTERNS (same logic as extraction.py)
# ============================================

PATTERNS = {
    "OTP/PIN codes":      r'\b\d{4,6}\b',                      # 4-6 digit codes (OTP, PIN)
    "Phone numbers":      r'(\+91[\s-]?\d{10}|\b\d{10}\b|\b\d{5}[\s-]\d{5}\b)',  # Indian phone formats
    "Bank accounts":      r'\b\d{9,18}\b',                      # 9-18 digit account numbers
    "UPI IDs":            r'\b[\w\.-]+@[\w\.-]+\b',             # anything@something
    "URLs":               r'https?://[^\s]+',                   # http/https links
}

# Safe replacement phrases — sound natural for an elderly confused person
REPLACEMENTS = {
    "OTP/PIN codes":      "[some numbers]",
    "Phone numbers":      "[a phone number]",
    "Bank accounts":      "[some digits]",
    "UPI IDs":            "[an ID]",
    "URLs":               "[a link]",
}


def filter_hallucinated_data(persona_response: str) -> tuple[str, dict]:
    """
    Scan persona response for any sensitive data the LLM may have hallucinated.
    Replace matches with safe placeholder phrases.

    Args:
        persona_response: Raw LLM output from the persona agent

    Returns:
        Tuple of:
            - cleaned_response: The sanitized text (safe to send)
            - report: Dict logging exactly what was caught and replaced

    Example:
        >>> raw = "My OTP is 482916 and my number is 9876543210"
        >>> clean, report = filter_hallucinated_data(raw)
        >>> clean
        'My [some numbers] is [some numbers] and my number is [a phone number]'
        >>> report
        {"OTP/PIN codes": ["482916"], "Phone numbers": ["9876543210"], ...}
    """

    report = {}
    cleaned = persona_response

    for category, pattern in PATTERNS.items():
        matches = re.findall(pattern, cleaned)

        # re.findall with groups returns tuples — flatten them
        matches = [m if isinstance(m, str) else m[0] for m in matches]
        # Remove empty strings
        matches = [m for m in matches if m.strip()]

        if matches:
            report[category] = matches
            # Replace each match with the safe placeholder
            cleaned = re.sub(pattern, REPLACEMENTS[category], cleaned)

    return cleaned, report


def validate_persona_output(persona_response: str) -> tuple[str, bool]:
    """
    High-level entry point called from graph.py persona_node.

    Runs the filter. If anything was caught:
        - Logs a warning with details
        - Returns the cleaned response + True (was_filtered flag)
    If nothing caught:
        - Returns original response + False

    Args:
        persona_response: Raw LLM output

    Returns:
        Tuple of:
            - final_response: Safe response text
            - was_filtered: True if something was caught and replaced
    """

    cleaned, report = filter_hallucinated_data(persona_response)

    if report:
        # Something was caught — log it clearly
        logger.warning(f"⚠️  HALLUCINATION FILTER TRIGGERED")
        logger.warning(f"   Original : \"{persona_response}\"")
        logger.warning(f"   Cleaned  : \"{cleaned}\"")
        logger.warning(f"   Caught   : {report}")
        return cleaned, True
    else:
        # Nothing caught — response is clean
        logger.debug(f"✅ Hallucination filter: PASSED (no sensitive data)")
        return persona_response, False
