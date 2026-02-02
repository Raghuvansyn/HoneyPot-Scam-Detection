# app/models.py
"""
Data Models using Pydantic
Updated to match judge's requirements with new response schema.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Literal, Union

# ============================================
# INPUT MODELS (What judges send to us)
# ============================================

class Message(BaseModel):
    """
    A single message in the conversation.
    
    Example:
    {
        "sender": "scammer",
        "text": "Your account is blocked!",
        "timestamp": "2026-01-31T10:00:00Z"
    }
    """
    sender: str          # "scammer" or "user"
    text: str            # The actual message content
    timestamp: Union[str, int]       # ISO format (str) or Unix timestamp (int)


class Metadata(BaseModel):
    """
    Information about the communication channel.
    
    Example:
    {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
    """
    channel: str         # "SMS", "WhatsApp", "Email"
    language: str        # "English", "Hindi", etc.
    locale: str          # "IN", "US", etc.


class HoneypotRequest(BaseModel):
    """
    Complete request from judges (what they POST to our API).
    
    Example:
    {
        "sessionId": "abc-123",
        "message": {...},
        "conversationHistory": [...],
        "metadata": {...}
    }
    """
    sessionId: str                        # Unique ID for this conversation
    message: Message                      # Latest message from scammer
    conversationHistory: List[Message] = []  # Previous messages (empty on first message)
    metadata: Optional[Metadata] = None   # Optional channel info


# ============================================
# OUTPUT MODELS (What we send back to judges)
# ============================================

class ResponseMeta(BaseModel):
    """
    Metadata about the current interaction state.
    
    During engagement:
    {
        "agentState": "engaging",
        "sessionStatus": "active",
        "persona": "confused_customer",
        "turn": 3,
        "agentNotes": "Detection: SCAM (confidence: 0.95)"
    }
    
    Final response:
    {
        "agentState": "completed",
        "sessionStatus": "closed",
        "persona": "confused_customer",
        "turn": 15,
        "confidence": "high",
        "agentNotes": "Detection: SCAM | Timeline summary here..."
    }
    """
    agentState: Literal["engaging", "completed"]  # Current state
    sessionStatus: Literal["active", "closed"]     # Session status
    persona: str                                    # Persona type
    turn: int                                       # Message count
    confidence: Optional[str] = None                # "high", "medium", "low" (final only)
    agentNotes: str                                 # Detection notes + timeline summary


class JudgeResponse(BaseModel):
    """
    Response format that judges see in their terminal.
    
    This is what appears on their screen (NOT the callback).
    
    Example:
    {
        "status": "success",
        "reply": "Oh no! What happened? I'm very worried!",
        "meta": {
            "agentState": "engaging",
            "sessionStatus": "active",
            "persona": "confused_customer",
            "turn": 3,
            "agentNotes": "Detection: SCAM (confidence: 0.95)"
        }
    }
    """
    status: str = "success"
    reply: str              # Persona's response text
    meta: ResponseMeta      # Metadata about interaction


# ============================================
# CALLBACK MODELS (What we send to GUVI)
# ============================================

class ExtractedIntelligence(BaseModel):
    """
    Information extracted from scammer.
    
    This goes to GUVI endpoint, NOT visible to judges in API response.
    
    Example:
    {
        "bankAccounts": ["123456789"],
        "upiIds": ["scammer@paytm"],
        "phishingLinks": ["http://fake-bank.com"],
        "phoneNumbers": ["+919876543210"],
        "suspiciousKeywords": ["urgent", "blocked"]
    }
    """
    bankAccounts: List[str] = []
    upiIds: List[str] = []
    phishingLinks: List[str] = []
    phoneNumbers: List[str] = []
    suspiciousKeywords: List[str] = []


class GuviCallback(BaseModel):
    """
    Final callback payload sent to GUVI endpoint.
    
    Endpoint: POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
    
    Example:
    {
        "sessionId": "abc-123",
        "scamDetected": true,
        "totalMessagesExchanged": 15,
        "extractedIntelligence": {...},
        "agentNotes": "Detection: SCAM | Timeline summary..."
    }
    """
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str

# ============================================
# AGENT STATE (Internal Workflow State)
# ============================================

from typing import TypedDict, List, Dict, Optional, Any

class AgentState(TypedDict):
    sessionId: str                      # Unique identifier
    conversationHistory: List[Dict]     # All messages so far
    metadata: Optional[Dict]            # Channel, language, locale
    scamDetected: bool                  # Is this a scam?
    extractedIntelligence: Dict         # Data extracted from scammer
    totalMessages: int                  # Count of messages
    startTime: Optional[str]            # When conversation started
    lastUpdated: Optional[str]          # Last update timestamp
    agentNotes: str                     # Notes about scammer behavior
    sessionStatus: Optional[str]        # "active" or "closed"
    callbackSent: bool                  # IDEMPOTENCY: Has final callback been sent?