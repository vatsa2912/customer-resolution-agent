"""
Backward compatibility wrapper for CustomerResolutionAgent.
Delegates directly to the upgraded app.agents package.
"""
from app.agents.resolution_agent import CustomerResolutionAgent

__all__ = ["CustomerResolutionAgent"]
