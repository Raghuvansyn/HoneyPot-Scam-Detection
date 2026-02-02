

import re

def extract_intelligence(conversation_history: list) -> dict:
   
    
    # Combine all message texts into one string for easier searching
    all_text = " ".join([
        msg.get("text", "") 
        for msg in conversation_history
    ])
    
    # Extract different types of intelligence
    intelligence = {
        "bankAccounts": extract_bank_accounts(all_text),
        "upiIds": extract_upi_ids(all_text),
        "phishingLinks": extract_links(all_text),
        "phoneNumbers": extract_phone_numbers(all_text),
        "suspiciousKeywords": extract_keywords(all_text)
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

    # [\w\.-]+ = one or more word characters, dots, or hyphens
    # @ = literal @ symbol
    pattern = r'\b[\w\.-]+@[\w\.-]+\b'
    
    potential_upis = re.findall(pattern, text)
    
    # Filter to only include valid UPI-like patterns
    # (remove email addresses, keep UPI IDs)
    upis = [
        u for u in potential_upis 
        if '@' in u and not u.endswith('.com') and not u.endswith('.in')
    ]
    
    # Remove duplicates and limit to 5
    return list(set(upis))[:5]


def extract_links(text: str) -> list:

    # https? = http or https (? makes 's' optional)
    # :// = literal ://
    # [^\s]+ = one or more non-space characters
    pattern = r'https?://[^\s]+'
    
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