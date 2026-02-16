from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal, Union, TypedDict, Any


# --- Input Models ---

class Message(BaseModel):
    sender: str
    text: str = Field(..., max_length=10000)
    timestamp: Union[str, int]


class Metadata(BaseModel):
    channel: Optional[str] = "unknown"
    language: Optional[str] = "en"
    locale: Optional[str] = "IN"


class HoneypotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = []
    metadata: Optional[Metadata] = None


# --- Response Models (API) ---

class ResponseMeta(BaseModel):
    agentState: Literal["engaging", "completed"]
    sessionStatus: Literal["active", "closed"]
    persona: str
    turn: int
    confidence: Optional[float] = None
    agentNotes: str


# --- Callback Models (GUVI Final Output) ---

class ExtractedIntelligence(BaseModel):
    bankAccounts: List[str] = []
    upiIds: List[str] = []
    phishingLinks: List[str] = []
    phoneNumbers: List[str] = []
    emailAddresses: List[str] = []
    suspiciousKeywords: List[str] = []


class EngagementMetrics(BaseModel):
    totalMessagesExchanged: int = 0
    engagementDurationSeconds: float = 0


class JudgeResponse(BaseModel):
    status: str = "success"
    reply: str
    scamDetected: bool  # Required field (5 points)
    extractedIntelligence: ExtractedIntelligence  # Required field (5 points)
    engagementMetrics: Optional[EngagementMetrics] = None  # Optional field (2.5 points)
    agentNotes: Optional[str] = None  # Optional field (2.5 points)
    meta: ResponseMeta  # Keep for internal tracking


class GuviCallback(BaseModel):
    sessionId: str
    status: str = "completed"
    scamDetected: bool
    totalMessagesExchanged: int
    extractedIntelligence: ExtractedIntelligence
    engagementMetrics: EngagementMetrics
    agentNotes: str
    digitalArrestInfo: Optional[Dict] = None
    severity: Optional[str] = "NORMAL"


# --- Internal Workflow State ---

class AgentState(TypedDict):
    sessionId: str
    conversationHistory: List[Dict]
    metadata: Optional[Dict]
    scamDetected: bool
    extractedIntelligence: Dict
    totalMessages: int
    startTime: Optional[str]
    lastUpdated: Optional[str]
    wallClockStart: Optional[float]
    agentNotes: str
    sessionStatus: Optional[str]
    callbackSent: bool
    digitalArrestInfo: Optional[Dict]
    detectionConfidence: Optional[float]
    scamType: Optional[str]  # bank_fraud, upi_fraud, phishing, etc.
