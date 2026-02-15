import re
from datetime import datetime

DIGITAL_ARREST_INTELLIGENCE = {
    "total_attempts": 0,
    "active_campaigns": {},
    "scammer_phone_numbers": set(),
    "fake_authority_claims": {
        "CBI": 147, "ED": 89, "TRAI": 203,
        "Supreme Court": 56, "Income Tax": 34
    },
}


def normalize_before_extract(text: str) -> str:
    """Collapse obfuscated intel: 'at' -> '@', spaced digits, word-numbers."""
    text = re.sub(r'\s+at\s+', '@', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+dot\s+', '.', text, flags=re.IGNORECASE)
    text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)

    word_map = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
    }
    for word, digit in word_map.items():
        text = re.sub(r'\b' + word + r'\b', digit, text, flags=re.IGNORECASE)

    return text


def extract_intelligence(conversation_history: list) -> dict:
    all_text = " ".join(msg.get("text", "") for msg in conversation_history)
    normalized = normalize_before_extract(all_text)

    phone_numbers = list(set(
        extract_phone_numbers(all_text) + extract_phone_numbers(normalized)
    ))

    # bank accounts are extracted separately, then we remove any that are also phone numbers
    raw_accounts = list(set(
        extract_bank_accounts(all_text) + extract_bank_accounts(normalized)
    ))
    phone_digits = {re.sub(r'[\s\-\+]', '', p) for p in phone_numbers}
    bank_accounts = [a for a in raw_accounts if a not in phone_digits]

    intelligence = {
        "bankAccounts": bank_accounts,
        "upiIds": list(set(extract_upi_ids(all_text) + extract_upi_ids(normalized))),
        "phishingLinks": list(set(extract_links(all_text) + extract_links(normalized))),
        "phoneNumbers": phone_numbers,
        "emailAddresses": list(set(extract_emails(all_text) + extract_emails(normalized))),
        "suspiciousKeywords": extract_keywords(all_text),
    }

    return intelligence


def extract_phone_numbers(text: str) -> list:
    patterns = [
        r'\+91[\s-]?\d{10}',
        r'\b\d{10}\b',
        r'\b\d{5}[\s-]\d{5}\b',
    ]
    phones = []
    for pattern in patterns:
        phones.extend(re.findall(pattern, text))
    return list(set(phones))[:5]


def extract_bank_accounts(text: str) -> list:
    # 11-18 digits only (skip 9-10 which overlap with phone numbers)
    accounts = re.findall(r'\b\d{11,18}\b', text)
    return list(set(accounts))[:5]


def extract_upi_ids(text: str) -> list:
    upi_suffixes = (
        'paytm', 'okaxis', 'okhdfcbank', 'oksbi', 'okicici',
        'ybl', 'upi', 'apl', 'ibl', 'axl', 'sbi', 'icici',
        'hdfcbank', 'axisbank', 'kotak', 'boi', 'pnb',
        'phonepe', 'gpay', 'freecharge', 'mobikwik'
    )
    pattern = r'\b[\w\.\-]+@[\w\.\-]+\b'
    found = re.findall(pattern, text)
    # keep only those with UPI-like suffixes (not email domains)
    upis = [u for u in found if any(u.lower().endswith('@' + s) or ('@' + s + '.') in u.lower() for s in upi_suffixes)]

    # also catch obfuscated UPI: "user at okaxis dot com"
    pattern_text = r'\b[\w\.\-]+\s+(?:at|@)\s+[\w\.\-]+\s+(?:dot|\.)\s+(?:com|in)\b'
    found_text = re.findall(pattern_text, text, re.IGNORECASE)
    for t in found_text:
        t = t.lower().replace(" at ", "@").replace(" dot ", ".").replace(" ", "")
        if any(s in t for s in upi_suffixes):
            upis.append(t)

    # fallback: if nothing matched via suffix, include any @-pattern that is NOT an email
    if not upis:
        email_domains = ('.com', '.in', '.org', '.net', '.co', '.edu', '.gov', '.io')
        for u in found:
            domain = u.split('@')[1] if '@' in u else ''
            if not any(domain.endswith(d) for d in email_domains):
                upis.append(u)

    return list(set(upis))[:5]


def extract_emails(text: str) -> list:
    pattern = r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
    found = re.findall(pattern, text)
    # filter out UPI-like patterns
    upi_suffixes = ('paytm', 'okaxis', 'okhdfcbank', 'oksbi', 'okicici', 'ybl', 'upi', 'apl')
    emails = [e for e in found if not any(e.lower().endswith('@' + s) for s in upi_suffixes)]
    return list(set(emails))[:5]


def extract_links(text: str) -> list:
    # matches URLs with or without paths
    pattern = r'https?://[^\s<>\"\']+'
    links = re.findall(pattern, text)

    # also catch shortened URLs without protocol
    short_pattern = r'\b(?:bit\.ly|tinyurl\.com|goo\.gl|t\.co|is\.gd|buff\.ly)/[^\s<>\"\']+'
    links.extend(re.findall(short_pattern, text))

    # catch suspicious domains with paths (no protocol)
    domain_pattern = r'\b(?:www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?/[^\s<>\"\']+'
    candidates = re.findall(domain_pattern, text)
    # only add if it looks suspicious (not common domains)
    safe_domains = ('google.com', 'facebook.com', 'twitter.com', 'github.com', 'wikipedia.org')
    for c in candidates:
        if not any(d in c.lower() for d in safe_domains):
            links.append(c)

    return list(set(links))[:5]


def extract_keywords(text: str) -> list:
    suspicious_keywords = [
        'urgent', 'immediately', 'blocked', 'suspend', 'verify',
        'otp', 'upi', 'bank account', 'account', 'kyc', 'refund',
        'winner', 'prize', 'lottery', 'congratulations',
        'click here', 'link', 'expire', 'confirm'
    ]
    text_lower = text.lower()
    found = [kw for kw in suspicious_keywords if kw in text_lower]
    return list(set(found))[:10]


def analyze_digital_arrest_campaign(phone_number: str, claimed_authority: str, message: str):
    if not claimed_authority:
        msg_lower = message.lower()
        if "cbi" in msg_lower: claimed_authority = "CBI"
        elif "enforcement" in msg_lower: claimed_authority = "ED"
        elif "trai" in msg_lower: claimed_authority = "TRAI"
        elif "police" in msg_lower: claimed_authority = "POLICE"
        else: claimed_authority = "UNKNOWN"

    campaign_id = f"DA-{claimed_authority}-{phone_number[-6:]}"
    if campaign_id not in DIGITAL_ARREST_INTELLIGENCE["active_campaigns"]:
        DIGITAL_ARREST_INTELLIGENCE["active_campaigns"][campaign_id] = {
            "first_seen": datetime.now(), "attempts": 0,
            "victims_contacted": 0, "script_variations": []
        }

    campaign = DIGITAL_ARREST_INTELLIGENCE["active_campaigns"][campaign_id]
    campaign["attempts"] += 1
