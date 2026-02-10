import json
import random
import os

BASE_DATASET_PATH = r"evaluation/dataset/reddit_scams.json"
EXPANDED_DATASET_PATH = r"evaluation/dataset/expanded_scams.json"

# Simple Hinglish word map
HINGLISH_MAP = {
    "please": "kripaya",
    "money": "paisa",
    "work": "kaam",
    "job": "naukri",
    "call": "sampark",
    "account": "khata",
    "blocked": "band",
    "update": "navinikaran",
    "pay": "bhugtan",
    "friend": "dost",
    "gym": "vyayamshala",
    "class": "kaksha"
}

TYPO_RULES = [
    ("a", "q"), ("s", "a"), ("d", "s"), ("f", "d"), ("e", "r"),
    ("i", "o"), ("o", "p"), ("k", "l"), ("m", "n"), ("b", "v")
]

EMOJIS = ["🚨", "⚠️", "‼️", "🔥", "💰", "💸", "🛑", "❌", "📞"]

def add_typos(text: str, probability: float = 0.1) -> str:
    """Ideally swaps characters for adjacent keys."""
    chars = list(text)
    for i in range(len(chars)):
        if random.random() < probability:
            if chars[i].isalpha():
                for rule in TYPO_RULES:
                    if rule[0] == chars[i].lower():
                        chars[i] = rule[1] if chars[i].islower() else rule[1].upper()
                        break
    return "".join(chars)

def add_urgency(text: str) -> str:
    """Adds urgent prefixes/suffixes."""
    prefix = random.choice(["URGENT ALERT: ", "IMMEDIATE ATTENTION: ", "FINAL NOTICE: ", "ATTENTION REQUIRED: "])
    suffix = random.choice(["... REPLY NOW!!!", "... DO NOT IGNORE!!!", "... CALL IMMEDIATELY!!!"])
    return prefix + text + suffix

def to_hinglish(text: str) -> str:
    """Replaces common English words with Hindi equivalents."""
    words = text.split()
    new_words = []
    for word in words:
        clean_word = word.lower().strip(",.?!")
        if clean_word in HINGLISH_MAP and random.random() > 0.3:
            replacement = HINGLISH_MAP[clean_word]
            new_words.append(replacement)
        else:
            new_words.append(word)
    return " ".join(new_words)

def add_emojis(text: str) -> str:
    """Adds random emojis."""
    return f"{random.choice(EMOJIS)} {text} {random.choice(EMOJIS)}"

def main():
    if not os.path.exists(BASE_DATASET_PATH):
        print(f"Error: Base dataset not found at {BASE_DATASET_PATH}")
        return

    with open(BASE_DATASET_PATH, "r", encoding="utf-8") as f:
        base_scams = json.load(f)
    
    expanded_dataset = []
    
    print(f"Expanding {len(base_scams)} base prompts...")

    for item in base_scams:
        original = item["text"]
        
        # 1. Original
        expanded_dataset.append({
            "category": item["category"],
            "text": original,
            "variation": "original",
            "source": item["source"]
        })
        
        # 2. Typos
        expanded_dataset.append({
            "category": item["category"],
            "text": add_typos(original, 0.05),
            "variation": "typos_mild",
            "source": item["source"]
        })
        
        # 3. Urgency
        expanded_dataset.append({
            "category": item["category"],
            "text": add_urgency(original),
            "variation": "urgent_caps",
            "source": item["source"]
        })
        
        # 4. Hinglish
        expanded_dataset.append({
            "category": item["category"],
            "text": to_hinglish(original),
            "variation": "hinglish_mix",
            "source": item["source"]
        })
        
        # 5. Emojis + Urgency
        expanded_dataset.append({
            "category": item["category"],
            "text": add_emojis(add_urgency(original)),
            "variation": "emoji_urgent",
            "source": item["source"]
        })
        
        # 6. Typos + Hinglish (Hard Mode)
        expanded_dataset.append({
            "category": item["category"],
            "text": add_typos(to_hinglish(original), 0.08),
            "variation": "hard_mode_hinglish_typo",
            "source": item["source"]
        })

    # Save to file
    with open(EXPANDED_DATASET_PATH, "w", encoding="utf-8") as f:
        json.dump(expanded_dataset, f, indent=2, ensure_ascii=False)
        
    print(f"Success! Generated {len(expanded_dataset)} variations in {EXPANDED_DATASET_PATH}")

if __name__ == "__main__":
    main()
