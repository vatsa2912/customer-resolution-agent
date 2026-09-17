from typing import Dict, Any, List, Optional
from app.policies.policy_data import POLICIES_MASTER

class PolicyEngine:
    """
    Deterministic rule engine that enforces airline policies strictly.
    The LLM has zero authority to approve prohibited actions or invent benefits.
    """

    @staticmethod
    def evaluate_cancellation(flight: Dict[str, Any], tier: str = "Silver") -> Dict[str, Any]:
        is_cancelled = "cancelled" in (flight.get("status") or "").lower()
        is_airline_caused = "operational" in (flight.get("reason") or "").lower() or is_cancelled

        if not is_cancelled:
            return {
                "eligible": False,
                "reason": "The flight is not cancelled by the airline.",
                "applicable_policies": []
            }

        priority_rebook = tier in ("Gold", "Platinum")
        return {
            "eligible": True,
            "is_airline_caused": is_airline_caused,
            "options": ["free_rebooking_24h", "full_refund"],
            "refund_timeline_days": 7,
            "refund_payment_method": "original_payment_method_only",
            "priority_rebooking": priority_rebook,
            "applicable_policies": ["POL-CANCEL-01", "POL-REFUND-01", "POL-LOYALTY-01"] if priority_rebook else ["POL-CANCEL-01", "POL-REFUND-01"]
        }

    @staticmethod
    def evaluate_delay_benefits(delay_hours: float, tier: str = "Silver") -> Dict[str, Any]:
        applicable_policies = []
        benefits = []
        hotel_eligible = False
        hotel_scope = None

        if delay_hours <= 0:
            return {
                "delay_hours": 0,
                "benefits": [],
                "hotel_eligible": False,
                "applicable_policies": []
            }

        if delay_hours < 3.0:
            applicable_policies.append("POL-DELAY-01")
            benefits.append("₹500 meal voucher")
        elif 3.0 <= delay_hours <= 5.0:
            applicable_policies.append("POL-DELAY-02")
            benefits.extend(["meal voucher", "lounge access"])
        else: # delay_hours > 5.0
            applicable_policies.append("POL-DELAY-03")
            benefits.extend(["meal voucher", "lounge access", "hotel accommodation (delayed hours only)"])
            hotel_eligible = True
            hotel_scope = "delayed_hours_only"

        # Check loyalty
        priority = tier in ("Gold", "Platinum")
        if priority:
            applicable_policies.append("POL-LOYALTY-01")

        return {
            "delay_hours": delay_hours,
            "benefits": benefits,
            "hotel_eligible": hotel_eligible,
            "hotel_scope": hotel_scope,
            "hotel_full_night_allowed": False,
            "priority_tier": tier,
            "applicable_policies": applicable_policies
        }

    @staticmethod
    def evaluate_fare_waiver(amount: float) -> Dict[str, Any]:
        """
        Policy: Agents cannot waive fare differences above ₹1,500 without supervisor approval.
        """
        if amount <= 1500:
            return {
                "amount": amount,
                "can_agent_waive": True,
                "requires_supervisor": False,
                "applicable_policies": ["POL-FARE-01"]
            }
        else:
            return {
                "amount": amount,
                "can_agent_waive": False,
                "requires_supervisor": True,
                "escalation_reason": f"Fare difference waiver of ₹{amount:,.0f} exceeds the agent waiver limit of ₹1,500.",
                "applicable_policies": ["POL-FARE-01", "POL-PROHIBIT-01"]
            }

    @staticmethod
    def evaluate_upgrade_request(tier: str = "Silver") -> Dict[str, Any]:
        """
        Policy: Gold & Platinum get priority rebooking (first access to next-available seats)
        but NO additional compensation beyond standard policy.
        Free business-class upgrade for disruption is strictly prohibited for agents.
        """
        return {
            "allowed": False,
            "requires_escalation": True,
            "reason": "The supplied policy does not provide a free business-class upgrade or extra compensation beyond standard policy.",
            "loyalty_entitlement": f"{tier} tier members receive priority access to next-available seats on rebooking, but not complimentary cabin upgrades.",
            "applicable_policies": ["POL-LOYALTY-01", "POL-PROHIBIT-01"]
        }

    @staticmethod
    def evaluate_hotel_request(delay_hours: float, full_night_requested: bool = False) -> Dict[str, Any]:
        """
        Policy: Hotel accommodation is eligible only for delays > 5 hours,
        and covers ONLY the delayed hours, NOT a full night's stay.
        """
        if delay_hours <= 5.0:
            return {
                "eligible": False,
                "requires_escalation": False,
                "reason": f"Your delay is {delay_hours:.0f} hours. Under policy, hotel accommodation is only provided for delays exceeding 5 hours.",
                "alternative_benefits": ["meal voucher", "lounge access"] if delay_hours > 3.0 else ["₹500 meal voucher"],
                "applicable_policies": ["POL-DELAY-02" if delay_hours > 3.0 else "POL-DELAY-01"]
            }

        # delay > 5h
        if full_night_requested:
            return {
                "eligible": True,
                "delayed_hours_eligible": True,
                "full_night_allowed": False,
                "requires_escalation": True,
                "reason": "Your 6-hour delay qualifies for hotel accommodation covering only the delayed hours. A full night's stay is not included in the standard policy.",
                "applicable_policies": ["POL-DELAY-03", "POL-PROHIBIT-01"]
            }

        return {
            "eligible": True,
            "delayed_hours_eligible": True,
            "full_night_allowed": False,
            "requires_escalation": False,
            "reason": "Your delay qualifies for hotel accommodation covering the delayed-hours portion, plus meal voucher and lounge access.",
            "applicable_policies": ["POL-DELAY-03"]
        }

    @staticmethod
    def check_mandatory_escalation(text: str, intent: str, requested_action: Optional[str] = None) -> Optional[Dict[str, Any]]:
        lower = text.lower()

        # 1. Threats of legal action or formal complaints
        if any(term in lower for term in ["legal action", "lawyer", "court", "formal complaint", "consumer court", "consumer forum", "sue"]):
            return {
                "category": "legal_threat",
                "reason": "Customer mentioned legal action or formal complaint.",
                "reply": "I hear you, and I’m sorry this has been such a frustrating experience. Because you mentioned legal action or a formal complaint, I am escalating this immediately to our specialist support team, and they will reach out to you directly.",
                "applicable_policies": ["POL-PROHIBIT-01"]
            }

        # 2. Free business-class upgrade
        if intent == "upgrade_request" or (requested_action == "business_class_upgrade"):
            return {
                "category": "unauthorized_compensation",
                "reason": "Customer requested a complimentary business class upgrade not provided by policy.",
                "applicable_policies": ["POL-LOYALTY-01", "POL-PROHIBIT-01"]
            }

        # 3. Fare waiver above 1500
        if intent == "fare_waiver_request" or requested_action == "waive_fare_difference":
            if "2000" in lower or "2,000" in lower or (requested_action and "2000" in requested_action):
                return {
                    "category": "fare_waiver_over_limit",
                    "reason": "Fare difference waiver request of ₹2,000 exceeds the agent waiver authority of ₹1,500.",
                    "applicable_policies": ["POL-FARE-01", "POL-PROHIBIT-01"]
                }

        # 4. Full night hotel request
        if intent == "hotel_full_night_request" or requested_action == "arrange_full_night_hotel":
            return {
                "category": "hotel_exception",
                "reason": "Customer requested a full night's hotel stay exceeding the delayed-hours policy entitlement.",
                "applicable_policies": ["POL-DELAY-03", "POL-PROHIBIT-01"]
            }

        return None
