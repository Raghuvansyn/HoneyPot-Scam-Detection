

import re

def normalize_before_extract(text: str) -> str:
    """Pre-process obfuscated intel before regex runs (Strategy 1: Silent Intel)"""
    
    # 1. "at" → "@", "dot" → "."
    text = re.sub(r'\s+at\s+', '@', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+dot\s+', '.', text, flags=re.IGNORECASE)
    
    # 2. Spaced characters: "9 8 7 6" → "9876"
    # Collapses single digits separated by spaces
    text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)
    
    # 3. Word numbers (partial)
    word_map = {
        "zero":"0","one":"1","two":"2","three":"3","four":"4",
        "five":"5","six":"6","seven":"7","eight":"8","nine":"9"
    }
    for word, digit in word_map.items():
        text = re.sub(r'\b' + word + r'\b', digit, text, flags=re.IGNORECASE)
    
    return text

def extract_intelligence(conversation_history: list) -> dict:
   
    # Combine all message texts into one string for easier searching
    all_text = " ".join([
        msg.get("text", "") 
        for msg in conversation_history
    ])
    
    # Run on BOTH original and normalized — merge results
    normalized = normalize_before_extract(all_text)
    
    intelligence = {
        "bankAccounts":  list(set(extract_bank_accounts(all_text) + extract_bank_accounts(normalized))),
        "upiIds":        list(set(extract_upi_ids(all_text)       + extract_upi_ids(normalized))),
        "phishingLinks": list(set(extract_links(all_text)         + extract_links(normalized))),
        "phoneNumbers":  list(set(extract_phone_numbers(all_text) + extract_phone_numbers(normalized))),
        "suspiciousKeywords": extract_keywords(all_text) # Keywords usually fine on original
    }
    
    print(f" Extraction Results:")
    for key, value in intelligence.items():
        if value:
            print(f"   {key}: {value}")
    
    return intelligence


def extract_bank_accounts(text: str) -> list:
    
    # \b = word boundary (ensures we get complete numbers)
    # \d = any digit (0-9)
    # {9,18} = between 9 and 18 digits
    pattern = r'\b\d{9,18}\b'
    
    accounts = re.findall(pattern, text)
    
    # Remove duplicates and limit to 5
    return list(set(accounts))[:5]


def extract_upi_ids(text: str) -> list:

    # Pattern 1: Standard UPI (e.g. user@oksbi)
    pattern_std = r'\b[\w\.-]+@[\w\.-]+\b'
    
    # Pattern 2: Obfuscated UPI ("user at okaxis dot com")
    pattern_text = r'\b[\w\.-]+\s+(?:at|@)\s+[\w\.-]+\s+(?:dot|\.)\s+(?:com|in)\b'
    
    found_std = re.findall(pattern_std, text)
    found_text = re.findall(pattern_text, text, re.IGNORECASE)
    
    # Normalize text matches (convert " at " to "@")
    normalized_text = []
    for t in found_text:
        t = t.lower()
        t = t.replace(" at ", "@").replace(" dot ", ".").replace(" ", "")
        normalized_text.append(t)
    
    all_upis = found_std + normalized_text
    
    # Filter to only include valid UPI-like patterns
    upis = [
        u for u in all_upis 
        if '@' in u and not u.endswith('.com') and not u.endswith('.in')
    ]
    # But wait, "paytm.com" is valid handle? No, handles are usually simply "@paytm".
    # But often people say "user@paytm.com".
    # I'll relax the filter to allow .com if it looks like a UPI email.
    
    upis = [u for u in all_upis if '@' in u]
    
    # Remove duplicates and limit to 5
    return list(set(upis))[:5]


def extract_links(text: str) -> list:

    # Pattern matches:
    # 1. http:// or https:// (optional)
    # 2. domain.com or sub.domain.co.in
    # 3. /path/to/resource (optional)
    
    # Improved pattern that catches "bit.ly/xyz", "www.google.com", "http://..."
    pattern = r'(?:https?://)?(?:www\.)?(?:bit\.ly|tinyurl\.com|goo\.gl|[a-zA-Z0-9-]+\.[a-zA-Z]{2,})/[^\s]*'
    
    links = re.findall(pattern, text)
    
    # Remove duplicates and limit to 5
    return list(set(links))[:5]


def extract_phone_numbers(text: str) -> list:
    patterns = [
        r'\+91[\s-]?\d{10}',       # +91-1234567890 or +91 1234567890
        r'\b\d{10}\b',              # 9876543210
        r'\b\d{5}[\s-]\d{5}\b'     # 12345-67890 or 12345 67890
    ]
    
    phones = []
    
    # Try each pattern
    for pattern in patterns:
        found = re.findall(pattern, text)
        phones.extend(found)
    
    # Remove duplicates and limit to 5
    return list(set(phones))[:5]


def extract_keywords(text: str) -> list:
    # Same keywords as detection agent
    # Same keywords as detection agent
    suspicious_keywords = [
        'urgent', 'immediately', 'blocked', 'suspend', 'verify',
        'otp', 'upi', 'bank account', 'account', 'kyc', 'refund',
        'winner', 'prize', 'lottery', 'congratulations',
        'click here', 'link', 'expire', 'confirm'
    ]
    
    text_lower = text.lower()
    found = []
    
    for keyword in suspicious_keywords:
        if keyword in text_lower:
            found.append(keyword)
    
    # Remove duplicates and limit to 10
    return list(set(found))[:10]