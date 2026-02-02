# app/agents/__init__.py
"""
Agent Package
Contains all agent modules: detection, persona, extraction
"""

from app.agents.detection import detect_scam
from app.agents.persona import generate_persona_response
from app.agents.extraction import extract_intelligence

__all__ = [
    "detect_scam",
    "generate_persona_response", 
    "extract_intelligence"
]