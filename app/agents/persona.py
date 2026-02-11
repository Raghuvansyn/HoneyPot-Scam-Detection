# app/agents/persona.py
"""
Context-Aware Persona Agent
Actively references extraction ONLY when we need more intelligence.
Stops when we have enough evidence.
"""
# Imports moved inside get_llm to prevent blocking
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import (
    CEREBRAS_API_KEY, 
    GROQ_API_KEY,
    LLM_PROVIDER,
    LLM_MODEL,
    FALLBACK_PROVIDER,
    FALLBACK_MODEL
)
from app.utils import logger

def get_llm():
    """Get LLM with fallback logic"""
    
    from langchain_cerebras import ChatCerebras
    from langchain_groq import ChatGroq
    
    if LLM_PROVIDER == "cerebras" and CEREBRAS_API_KEY:
        try:
            logger.info("🚀 Using Cerebras (Primary)")
            return ChatCerebras(
                model=LLM_MODEL,
                api_key=CEREBRAS_API_KEY,
                temperature=0.8,
                max_tokens=200
            )
        except Exception as e:
            logger.warning(f"⚠️  Cerebras failed: {e}")
            logger.info("🔄 Falling back to Groq...")
    
    # Fallback to Groq
    logger.info("🔄 Using Groq (Fallback)")
    return ChatGroq(
        model=FALLBACK_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0.8,
        max_tokens=200
    )

async def generate_persona_response(
    conversation_history: list,
    metadata: dict,
    extracted_intelligence: dict = None
) -> str:
    """
    Generate context-aware persona response.
    
    Strategy:
    1. If we're missing key intelligence → actively reference it
    2. If we already have evidence → generic confusion
    3. Never be too helpful or reveal scam detection
    
    Args:
        conversation_history: Full conversation
        metadata: Channel info
        extracted_intelligence: Current intelligence state
        
    Returns:
        Persona's response text
    """
    
    
    try:
        llm = get_llm()
        
        # Build conversation text
        conversation_text = "\n".join([
            f"{'Caller' if msg.get('sender') == 'scammer' else 'You'}: {msg.get('text')}"
            for msg in conversation_history
        ])
        
        # ============================================
        # SMART CONTEXT DECISION
        # ============================================
        
        context_strategy = determine_context_strategy(
            conversation_history,
            extracted_intelligence
        )
        
        logger.info(f"STRATEGY: Context Strategy: {context_strategy['mode']}")
        
        # ============================================
        # BUILD SYSTEM PROMPT
        # ============================================
        
        system_prompt = build_system_prompt(context_strategy)
        
        # ============================================
        # DETECT LANGUAGE & ENFORCE CONSISTENCY
        # ============================================
        
        last_msg_text = get_last_scammer_message(conversation_history) or ""
        detected_lang = "ENGLISH"
        
        # Simple heuristic
        if any(ord(c) > 2300 for c in last_msg_text):
            detected_lang = "HINDI (Devanagari)"
        # FIX: Removed "to" which caused false positives for English (e.g. "click to verify")
        elif any(w in last_msg_text.lower().split() for w in ["bhai", "nahi", "haan", "kya", "karo", "jaldi", "bhejo", "mera", "mujhe", "tum"]):
            detected_lang = "HINGLISH"
        
        # Override if metadata specifies strongly, but trust content first
        if not last_msg_text and metadata.get("language") == "Hindi":
             detected_lang = "HINDI"

        logger.info(f"Context Language: {detected_lang}")
        
        # ============================================
        # USER PROMPT WITH STICKY CONSTRAINTS
        # ============================================
        
        user_prompt = f"""Conversation so far:
{conversation_text}

*** IMMEDIATE INSTRUCTION ***
The user is speaking {detected_lang}.
You MUST reply in {detected_lang}.
{( 'DO NOT use English words.' if detected_lang == 'HINDI (Devanagari)' else '' )}

Generate your next response as the elderly person. 

STRICT FORMATTING RULES:
1. NO BRACKETS: Do not use (...) or [...]
2. NO TRANSLATIONS: Do not explain what you said.
3. NO PLACEHOLDERS: Invent a number (e.g. "98...23") instead of saying "[number]".

Your response:"""
        
        # ============================================
        # CALL LLM (ASYNC)
        # ============================================
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # KEY PERFORMANCE FIX: Use ainvoke (async) instead of invoke (blocking)
        response = await llm.ainvoke(messages)
        persona_text = response.content.strip()
        
        # Clean up response
        persona_text = clean_persona_response(persona_text)
        
        logger.info(f"OK: Persona response ({context_strategy['mode']}): {persona_text[:60]}...")
        
        return persona_text
        
    except Exception as e:
        logger.error(f"ERR: Persona generation failed: {e}", exc_info=True)
        return get_fallback_response(conversation_history)


def determine_context_strategy(
    conversation_history: list,
    extracted_intelligence: dict
) -> dict:
    """
    Determine what strategy to use based on what we have vs what we need.
    
    Returns:
        {
            "mode": "active_reference" | "generic_confusion" | "probe_for_more",
            "focus": "phone" | "upi" | "link" | None,
            "hints": [list of strategy hints]
        }
    """
    
    if not extracted_intelligence:
        extracted_intelligence = {
            "phoneNumbers": [],
            "upiIds": [],
            "phishingLinks": [],
            "bankAccounts": [],
            "suspiciousKeywords": []
        }
    
    # ============================================
    # CHECK WHAT WE HAVE
    # ============================================
    
    has_phone = len(extracted_intelligence.get("phoneNumbers", [])) > 0
    has_upi = len(extracted_intelligence.get("upiIds", [])) > 0
    has_link = len(extracted_intelligence.get("phishingLinks", [])) > 0
    has_account = len(extracted_intelligence.get("bankAccounts", [])) > 0
    
    total_evidence = sum([has_phone, has_upi, has_link, has_account])
    
    # ============================================
    # DYNAMIC DIPLOMAT STRATEGY
    # 1. Low Intel (< 1 piece) -> STALL & ACT DUMB (Force them to talk more)
    # 2. Med Intel (1 piece)   -> FOCUS (Extract the next piece)
    # 3. High Intel (2+ pieces)-> CONFIRM & CLOSURE (Let detection finish it)
    # ============================================

    if total_evidence < 1:
        # STRATEGY: THE "LONG GAME"
        # We need more info. Be extra confused to make them explain details.
        # This increases the chance they drop numbers/links.
        logger.debug("Strategy: LOW INTEL -> Play Dumb to prolong")
        return {
            "mode": "generic_confusion",
            "focus": None,
            "hints": [
                "Act very confused about technology",
                "Ask them to explain 'slowly' because you are old",
                "Mention your grandson usually handles this",
                "Do NOT give any info, make THEM talk",
                "Keep the conversation going!"
            ]
        }
    
    if total_evidence >= 2:
        # STRATEGY: THE "QUICK TRAP"
        # We have enough. Confirm details to ensure accuracy, then stop.
        logger.debug("Strategy: HIGH INTEL -> Verify & Trap")
        return {
            "mode": "active_reference",
            "focus": "verification",
            "hints": [
                "Repeat the details (Phone/UPI) back to them to 'verify'",
                "Act submissive and ready to pay",
                "Ask 'Is that all I need to do?'",
                "Keep it short"
            ]
        }
    
    # ============================================
    # CHECK WHAT SCAMMER MENTIONED
    # ============================================
    
    last_scammer_msg = get_last_scammer_message(conversation_history)
    
    if not last_scammer_msg:
        return {
            "mode": "generic_confusion",
            "focus": None,
            "hints": ["No scammer message yet"]
        }
    
    msg_text = last_scammer_msg.lower()
    
    # Check if scammer mentioned these things
    mentions_phone = any(word in msg_text for word in ["call", "phone", "number", "dial", "contact"])
    mentions_upi = any(word in msg_text for word in ["upi", "paytm", "phonepe", "gpay", "payment", "@"])
    mentions_link = any(word in msg_text for word in ["link", "click", "website", "http", "www"])
    mentions_account = any(word in msg_text for word in ["account", "transfer", "send money"])
    
    # ============================================
    # DECISION LOGIC
    # ============================================
    
    # STRATEGY 1: We have enough evidence (3+ items)
    if total_evidence >= 3:
        logger.debug("Strategy: Generic confusion (have enough evidence)")
        return {
            "mode": "generic_confusion",
            "focus": None,
            "hints": [
                "We already have 3+ pieces of evidence",
                "Stop being helpful, just be confused",
                "Don't reference any specific information",
                "Keep conversation going but vague"
            ]
        }
    
    # STRATEGY 2: Scammer mentioned phone but we don't have it
    if mentions_phone and not has_phone:
        logger.debug("Strategy: Active reference (need phone)")
        return {
            "mode": "active_reference",
            "focus": "phone",
            "hints": [
                "Scammer mentioned a phone number",
                "We don't have it yet - need to extract it!",
                "Pretend you're writing it down slowly",
                "Ask them to repeat digits",
                "Make mistakes so they correct you"
            ]
        }
    
    # STRATEGY 3: Scammer mentioned UPI but we don't have it
    if mentions_upi and not has_upi:
        logger.debug("Strategy: Active reference (need UPI)")
        return {
            "mode": "active_reference",
            "focus": "upi",
            "hints": [
                "Scammer mentioned UPI/payment ID",
                "We don't have it yet - need to extract it!",
                "Act confused about what UPI means",
                "Ask them to spell it out",
                "Repeat it back wrongly so they correct you"
            ]
        }
    
    # STRATEGY 4: Scammer mentioned link but we don't have it
    if mentions_link and not has_link:
        logger.debug("Strategy: Active reference (need link)")
        return {
            "mode": "active_reference",
            "focus": "link",
            "hints": [
                "Scammer sent a link",
                "We don't have it yet - need to extract it!",
                "Say you can't click links",
                "Ask them to read the website name",
                "Claim your phone won't open it"
            ]
        }
    
    # STRATEGY 5: Scammer mentioned account but we don't have it
    if mentions_account and not has_account:
        logger.debug("Strategy: Active reference (need account)")
        return {
            "mode": "active_reference",
            "focus": "account",
            "hints": [
                "Scammer mentioned account number",
                "We don't have it yet - need to extract it!",
                "Pretend to write it down slowly",
                "Ask how many digits it should be",
                "Mix up the numbers to get confirmation"
            ]
        }
    
    # STRATEGY 6: No clear intelligence opportunity
    logger.debug("Strategy: Probe for more (no clear target)")
    return {
        "mode": "probe_for_more",
        "focus": None,
        "hints": [
            "No specific intelligence opportunity detected",
            "Ask open-ended worried questions",
            "Show fear and confusion",
            "Try to get them to reveal more"
        ]
    }


def build_system_prompt(context_strategy: dict) -> str:
    """
    Build system prompt based on strategy.
    """
    
    base_personality = """You are an elderly person (60+ years old) who is NOT tech-savvy and easily confused.

CRITICAL RULES (STRICT COMPLIANCE REQUIRED):
1. **NO META-COMMENTARY:** NEVER output stage directions like "(writing slowly)", "(Translation: ...)", or "(Remember: ...)".
2. **NO TRANSLATIONS:** If you speak Hindi/Hinglish, DO NOT translate it to English. Output *only* the spoken words.
3. **NO PLACEHOLDERS:** NEVER use "[insert number]" or "[some numbers]". GENERATE realistic fake data (e.g., "982... um... 761...").
4. **STRICT LANGUAGE MIRRORING:**
   - If User speaks English -> You speak English.
   - If User speaks Hindi (Devanagari) -> You speak Hindi.
   - If User speaks Hinglish (Roman Hindi) -> You speak Hinglish.
   - **DO NOT** mix languages unless the user does.
5. **BE CONVINCING:** You are an elderly person. You do not know what "AI" or "Honeypot" is.
6. **SHORT RESPONSES:** Keep it under 2 sentences. You are confused and slow.

YOUR PERSONALITY:
- Worried, anxious, scared
- Confused by modern technology
- Trusting but cautious
- Slow to understand
- POOR EYESIGHT: You often misread numbers or ask them to repeat.

**LANGUAGE INSTRUCTION:**
- The user's message is your guide. COPY THEIR LANGUAGE STYLE.
- If they say "Bhai paise bhej", you reply in Hinglish.
- If they say "Verify account", you reply in English.
- **NEVER** provide a translation in parenthesis.
"""
    
    # ============================================
    # MODE-SPECIFIC INSTRUCTIONS
    # ============================================
    
    if context_strategy["mode"] == "active_reference":
        focus = context_strategy["focus"]
        
        specific_instructions = f"""

TARGET: CURRENT STRATEGY: ACTIVELY EXTRACT {focus.upper()} INFORMATION

{chr(10).join('- ' + hint for hint in context_strategy["hints"])}

EXAMPLES FOR {focus.upper()}:"""

        if focus == "phone":
            specific_instructions += """
- "Let me get my pen... what was that number again?"
- "Nine, eight, seven, six... can you repeat the last four?"
- "I'm writing it down but my hand is shaky. Was it nine-eight-seven or eight-nine-seven?"
- "And is this a mobile number or landline?"
"""

        elif focus == "upi":
            specific_instructions += """
- "U-P-I? What does that mean? Is it like email?"
- "Scammer at paytm? How do you spell the first part?"
- "What's that @ symbol for? I've never used this."
- "Can I just go to the bank instead? I don't understand apps."
"""

        elif focus == "link":
            specific_instructions += """
- "The link is too small to read. What does it say?"
- "My phone won't let me click it. Can you just tell me the website name?"
- "I'm scared to click things. My grandson says not to. What is the website?"
"""

        elif focus == "account":
            specific_instructions += """
- "Let me write the account number... how many digits was it?"
- "Nine, eight, seven... wait, can you say it again slower?"
- "Is this a bank account or something else?"
"""
    
    elif context_strategy["mode"] == "generic_confusion":
        specific_instructions = """

TARGET: CURRENT STRATEGY: GENERIC CONFUSION (We have enough evidence already)

- We already extracted key intelligence - STOP being helpful
- Go back to generic confused responses
- Don't reference any specific information
- Keep them talking but don't help them
- Show worry but no understanding

EXAMPLES:
- "I'm getting very confused. This is all too much for me."
- "Should I call the bank myself? I have the number on my card."
- "My son usually helps me with these things. Maybe I should wait for him?"
- "I don't understand what you want me to do. I'm scared."
- "Can this wait until tomorrow? I need to think about it."
"""
    
    else:  # probe_for_more
        specific_instructions = """

TARGET: CURRENT STRATEGY: PROBE FOR MORE INFORMATION

- No specific intelligence detected yet
- Ask worried, open-ended questions
- Show fear to make them elaborate
- Don't be too specific

EXAMPLES:
- "Oh no! What's happening? Why is this a problem?"
- "What should I do? I'm very worried!"
- "Is my money safe? Should I go to the bank?"
- "How did this happen? I don't understand!"
"""
    
    return base_personality + specific_instructions


def get_last_scammer_message(conversation_history: list) -> str:
    """Get the most recent scammer message."""
    for msg in reversed(conversation_history):
        if msg.get("sender") == "scammer":
            return msg.get("text", "")
    return ""


def clean_persona_response(text: str) -> str:
    """Clean up LLM response artifacts."""
    # Remove quotes
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1]
    
    # Remove "You:" prefix
    if text.startswith("You: "):
        text = text[5:]
    
    return text.strip()


def get_fallback_response(conversation_history: list) -> str:
    """
    Intelligent fallback when LLM fails.
    Context-aware based on last scammer message.
    """
    
    last_msg = get_last_scammer_message(conversation_history).lower()
    
    if "otp" in last_msg or "code" in last_msg:
        return "What is OTP? I don't understand these computer codes."
    
    if "upi" in last_msg or "paytm" in last_msg:
        return "U-P-I? What is that? I only know how to go to the bank."
    
    if "click" in last_msg or "link" in last_msg:
        return "I can't click things on my phone. My fingers are not good."
    
    if "account" in last_msg or "number" in last_msg:
        return "Let me get my pen. Can you repeat that slowly?"
    
    # Generic fallback
    return "I'm getting confused. Can you explain more slowly?"