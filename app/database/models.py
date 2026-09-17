from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Customer:
    id: str
    name: str
    tier: str
    pnr: str
    email: str
    phone: str
    travel_history: str

@dataclass
class Flight:
    id: Optional[int]
    flight_number: str
    booking_pnr: str
    route: str
    date: str
    scheduled_departure: str
    new_departure: Optional[str]
    status: str
    reason: Optional[str]
    delay_hours: float = 0.0
    is_return: bool = False

@dataclass
class Booking:
    pnr: str
    customer_id: str
    status: str
    flights: List[Flight] = field(default_factory=list)

@dataclass
class PolicyRule:
    code: str
    category: str
    title: str
    description: str
    rule_json: str

@dataclass
class ActionRecord:
    id: Optional[int]
    customer_key: str
    action_type: str
    status: str  # proposed, awaiting_confirmation, approved, executed, rejected, escalated, failed
    details: str
    idempotency_key: Optional[str] = None
    conversation_id: Optional[int] = None
    created_at: Optional[str] = None
    executed_at: Optional[str] = None

@dataclass
class EscalationRecord:
    id: Optional[int]
    customer_key: str
    category: str  # legal_threat, unauthorized_compensation, fare_waiver_over_limit, hotel_exception, other
    reason: str
    details: str
    status: str = "pending"  # pending, under_review, resolved
    conversation_id: Optional[int] = None
    supervisor_notes: Optional[str] = None
    created_at: Optional[str] = None

@dataclass
class AgentDecision:
    primary_intent: str
    decision: str
    reason: str
    secondary_intents: List[str] = field(default_factory=list)
    policy_codes: List[str] = field(default_factory=list)
    proposed_action: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False
    requires_escalation: bool = False
    provider_used: str = "local"
