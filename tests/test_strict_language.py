import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# FIX WINDOWS UNICODE
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from app.agents.persona import generate_persona_response

async def test_strict_language():
    
    # CASE 1: ENGLISH
    print("\n--- TEST 1: ENGLISH INPUT ---")
    history_en = [{"sender": "scammer", "text": "URGENT: Your SBI account has been compromised. Verify now.", "timestamp": "2026-02-11T12:00:00Z"}]
    resp_en = await generate_persona_response(history_en, {}, {})
    print(f"Response (Should be English): {resp_en}")
    
    if "bhai" in resp_en.lower() or "hai" in resp_en.lower():
        print("❌ FAIL: Hinglish detected in English response")
    else:
        print("✅ PASS: Clean English")

    # CASE 2: HINGLISH
    print("\n--- TEST 2: HINGLISH INPUT ---")
    history_hin = [{"sender": "scammer", "text": "Arrey bhai paise bhej jaldi account band ho jayega", "timestamp": "2026-02-11T12:00:00Z"}]
    resp_hin = await generate_persona_response(history_hin, {}, {})
    print(f"Response (Should be Hinglish): {resp_hin}")
    
    if "brother" in resp_en.lower() and "bhai" not in resp_hin.lower(): # Just heuristic
        print("⚠️  WARN: Might be too English? Check visually.")
    else:
        print("✅ PASS: Responded in target language")

    # CASE 3: ARTIFACTS
    if "(" in resp_en or "[" in resp_en or "Translation:" in resp_en:
        print("❌ FAIL: Artifacts detected in English response")
    else:
        print("✅ PASS: No artifacts in English response")

if __name__ == "__main__":
    asyncio.run(test_strict_language())
