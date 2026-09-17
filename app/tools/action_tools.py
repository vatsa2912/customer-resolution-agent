from typing import Dict, Any, Optional
from app.services.action_service import ActionService
from app.tools.registry import default_tool_registry

action_svc = ActionService()

@default_tool_registry.register(
    name="create_refund_request",
    description="Propose a full refund for an airline-caused cancelled flight.",
    parameters={
        "type": "object",
        "properties": {
            "customer_key": {"type": "string"},
            "pnr": {"type": "string"},
            "flight_number": {"type": "string"},
            "conversation_id": {"type": "integer"}
        },
        "required": ["customer_key", "pnr", "flight_number"]
    }
)
def create_refund_request(customer_key: str, pnr: str, flight_number: str, conversation_id: Optional[int] = None) -> Dict[str, Any]:
    idempotency_key = f"{customer_key}_refund_{flight_number}"
    details = f"Full cash refund for cancelled flight {flight_number} (PNR {pnr}) to original payment method within 7 business days."
    return action_svc.propose_action(
        customer_key=customer_key,
        action_type="refund_request",
        details=details,
        idempotency_key=idempotency_key,
        requires_confirmation=True,
        conversation_id=conversation_id
    )

@default_tool_registry.register(
    name="create_rebooking_request",
    description="Propose free priority rebooking on the next available flight within 24 hours.",
    parameters={
        "type": "object",
        "properties": {
            "customer_key": {"type": "string"},
            "pnr": {"type": "string"},
            "flight_number": {"type": "string"},
            "priority": {"type": "boolean"},
            "conversation_id": {"type": "integer"}
        },
        "required": ["customer_key", "pnr", "flight_number"]
    }
)
def create_rebooking_request(customer_key: str, pnr: str, flight_number: str, priority: bool = False, conversation_id: Optional[int] = None) -> Dict[str, Any]:
    idempotency_key = f"{customer_key}_rebook_{flight_number}"
    priority_label = "Priority " if priority else ""
    details = f"{priority_label}Rebooking requested on next available flight within 24 hours for flight {flight_number} (PNR {pnr})."
    return action_svc.propose_action(
        customer_key=customer_key,
        action_type="priority_rebooking" if priority else "rebooking_request",
        details=details,
        idempotency_key=idempotency_key,
        requires_confirmation=True,
        conversation_id=conversation_id
    )

@default_tool_registry.register(
    name="apply_delay_benefits",
    description="Issue standard delay compensation (meal voucher and lounge access).",
    parameters={
        "type": "object",
        "properties": {
            "customer_key": {"type": "string"},
            "pnr": {"type": "string"},
            "flight_number": {"type": "string"},
            "benefits": {"type": "string"},
            "conversation_id": {"type": "integer"}
        },
        "required": ["customer_key", "pnr", "flight_number", "benefits"]
    }
)
def apply_delay_benefits(customer_key: str, pnr: str, flight_number: str, benefits: str, conversation_id: Optional[int] = None) -> Dict[str, Any]:
    idempotency_key = f"{customer_key}_delay_benefits_{flight_number}"
    details = f"Issued delay benefits: {benefits} for flight {flight_number} (PNR {pnr})."
    return action_svc.propose_action(
        customer_key=customer_key,
        action_type="delay_benefits",
        details=details,
        idempotency_key=idempotency_key,
        requires_confirmation=False,
        conversation_id=conversation_id
    )

@default_tool_registry.register(
    name="create_hotel_request",
    description="Arrange hotel accommodation for the delayed-hours portion where eligible (>5h delay).",
    parameters={
        "type": "object",
        "properties": {
            "customer_key": {"type": "string"},
            "pnr": {"type": "string"},
            "flight_number": {"type": "string"},
            "hours": {"type": "number"},
            "conversation_id": {"type": "integer"}
        },
        "required": ["customer_key", "pnr", "flight_number", "hours"]
    }
)
def create_hotel_request(customer_key: str, pnr: str, flight_number: str, hours: float, conversation_id: Optional[int] = None) -> Dict[str, Any]:
    idempotency_key = f"{customer_key}_hotel_{flight_number}"
    details = f"Hotel accommodation arranged covering delayed hours ({hours:.0f} hours) for flight {flight_number} (PNR {pnr})."
    return action_svc.propose_action(
        customer_key=customer_key,
        action_type="hotel_accommodation",
        details=details,
        idempotency_key=idempotency_key,
        requires_confirmation=False,
        conversation_id=conversation_id
    )
