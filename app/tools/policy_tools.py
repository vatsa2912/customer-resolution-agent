from typing import Dict, Any, Optional
from app.policies.policy_data import POLICIES_MASTER
from app.policies.policy_engine import PolicyEngine
from app.tools.registry import default_tool_registry

@default_tool_registry.register(
    name="retrieve_policy",
    description="Retrieve specific airline disruption policies and rule text.",
    parameters={
        "type": "object",
        "properties": {
            "policy_code": {"type": "string", "description": "Policy code (e.g. POL-CANCEL-01, POL-DELAY-02)"}
        },
        "required": ["policy_code"]
    }
)
def retrieve_policy(policy_code: str) -> Optional[Dict[str, Any]]:
    return POLICIES_MASTER.get(policy_code)

@default_tool_registry.register(
    name="check_delay_benefits",
    description="Evaluate delay compensation benefits for a given delay duration.",
    parameters={
        "type": "object",
        "properties": {
            "delay_hours": {"type": "number", "description": "Delay duration in hours"},
            "tier": {"type": "string", "description": "Customer tier (Silver, Gold, Platinum)"}
        },
        "required": ["delay_hours"]
    }
)
def check_delay_benefits(delay_hours: float, tier: str = "Silver") -> Dict[str, Any]:
    return PolicyEngine.evaluate_delay_benefits(delay_hours, tier)

@default_tool_registry.register(
    name="check_rebooking_eligibility",
    description="Evaluate whether a cancelled or delayed flight qualifies for free rebooking or refund.",
    parameters={
        "type": "object",
        "properties": {
            "is_cancelled": {"type": "boolean", "description": "Whether flight was cancelled"},
            "tier": {"type": "string", "description": "Customer loyalty tier"}
        },
        "required": ["is_cancelled"]
    }
)
def check_rebooking_eligibility(is_cancelled: bool, tier: str = "Silver") -> Dict[str, Any]:
    flight_mock = {"status": "Cancelled" if is_cancelled else "On-time", "reason": "operational reasons"}
    return PolicyEngine.evaluate_cancellation(flight_mock, tier)
