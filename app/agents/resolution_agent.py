from typing import Dict, Any, Optional
from app.agents.conversation_manager import ConversationManager

class CustomerResolutionAgent:
    """
    Autonomous AI Customer Support System for Airline Disruptions.
    Strictly grounded in Assignment 3 Data Pack.
    """
    def __init__(self, conversation_manager: Optional[ConversationManager] = None):
        self.manager = conversation_manager or ConversationManager()

    def handle(self, message: str, customer_key: str, force_provider: Optional[str] = None) -> Dict[str, Any]:
        return self.manager.handle_message(
            customer_key=customer_key,
            message=message,
            force_provider=force_provider
        )
