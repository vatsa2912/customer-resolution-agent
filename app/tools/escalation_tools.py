from typing import Dict, Any, Optional
from app.services.escalation_service import EscalationService
from app.tools.registry import default_tool_registry

esc_svc = EscalationService()

@default_tool_registry.register(
    name="create_escalation",
    description="Escalate an unauthorized request, legal threat, or exception to a human supervisor.",
    parameters={
        "type": "object",
        "properties": {
            "customer_key": {"type": "string"},
            "category": {"type": "string"},
            "reason": {"type": "string"},
            "details": {"type": "string"},
            "conversation_id": {"type": "integer"}
        },
        "required": ["customer_key", "category", "reason", "details"]
    }
)
def create_escalation(customer_key: str, category: str, reason: str, details: str, conversation_id: Optional[int] = None) -> Dict[str, Any]:
    return esc_svc.create_escalation(
        customer_key=customer_key,
        category=category,
        reason=reason,
        details=details,
        conversation_id=conversation_id
    )
