# app/agents/__init__.py
"""
Agent Package
Contains all agent modules: detection, persona, extraction
"""

from src.agents.detection import detect_scam
from src.agents.persona import generate_persona_response
from src.agents.extraction import extract_intelligence

__all__ = [
    "detect_scam",
    "generate_persona_response", 
    "extract_intelligence"
]