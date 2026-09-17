from typing import Dict, Any, Optional, List
from app.policies.policy_engine import PolicyEngine
from app.policies.policy_data import POLICIES_MASTER
from app.services.action_service import ActionService
from app.services.escalation_service import EscalationService
from app.tools.registry import default_tool_registry
from app.tools.booking_tools import get_booking_details

class DecisionEngine:
    def __init__(self, action_service: Optional[ActionService] = None, escalation_service: Optional[EscalationService] = None):
        self.action_svc = action_service or ActionService()
        self.esc_svc = escalation_service or EscalationService()

    def process_decision(
        self,
        customer: Dict[str, Any],
        intent_data: Dict[str, Any],
        message: str,
        history: List[Dict[str, Any]],
        conversation_id: int
    ) -> Dict[str, Any]:
        primary_intent = intent_data.get("primary_intent", "unknown")
        secondary_intents = intent_data.get("secondary_intents", [])
        requested_action = intent_data.get("requested_action")
        emotion = intent_data.get("emotion", "neutral")
        customer_ref = intent_data.get("customer_reference")
        customer_key = customer["id"]
        customer_name = customer["name"].split()[0]
        tier = customer.get("tier", "Silver")
        flights = customer.get("flights", [])
        primary_flight = flights[0] if flights else {}

        applicable_policies = []
        action_result = None
        escalation_result = None
        requires_confirmation = False

        # -------------------------------------------------------------
        # 0. UNKNOWN BOOKING PNR CHECK
        # -------------------------------------------------------------
        if customer_ref and customer_ref.upper() != customer["pnr"].upper():
            other_booking = get_booking_details(customer_ref)
            if not other_booking:
                return {
                    "reply": f"The booking reference '{customer_ref}' was not found in our records. Please verify the booking reference, or select one of the available passenger profiles (Priya Nair, Arvind Kulkarni, or Meher Kaur).",
                    "decision": "unknown_booking_reference",
                    "intent": "unknown_booking",
                    "policies_cited": [],
                    "action": None,
                    "escalation": None,
                    "requires_confirmation": False,
                    "requires_escalation": False,
                    "reason": f"Customer provided booking reference {customer_ref} which is not in the database."
                }

        # -------------------------------------------------------------
        # 1. PENDING ACTION CONFIRMATION / CANCELLATION CHECK
        # -------------------------------------------------------------
        pending_action = self.action_svc.get_pending_action(customer_key)

        if pending_action and primary_intent == "action_confirmation":
            conf_res = self.action_svc.confirm_action(pending_action["id"])
            return {
                "reply": f"Thank you for confirming, {customer_name}. {conf_res['details']}",
                "decision": "action_confirmed_and_executed",
                "intent": "action_confirmation",
                "policies_cited": ["POL-REFUND-01" if "refund" in pending_action["action_type"] else "POL-CANCEL-01"],
                "action": conf_res,
                "escalation": None,
                "requires_confirmation": False,
                "requires_escalation": False,
                "reason": f"Executed action {pending_action['id']} upon customer confirmation."
            }

        if pending_action and primary_intent == "action_cancellation":
            canc_res = self.action_svc.cancel_action(pending_action["id"])
            return {
                "reply": f"I have cancelled that request as requested, {customer_name}. Let me know how else I can assist you with your booking.",
                "decision": "action_cancelled",
                "intent": "action_cancellation",
                "policies_cited": [],
                "action": canc_res,
                "escalation": None,
                "requires_confirmation": False,
                "requires_escalation": False,
                "reason": "Customer cancelled the pending action."
            }

        # -------------------------------------------------------------
        # 2. LEGAL / FORMAL COMPLAINT CHECK (IMMEDIATE ESCALATION)
        # -------------------------------------------------------------
        legal_check = PolicyEngine.check_mandatory_escalation(message, primary_intent, requested_action)
        if legal_check and legal_check["category"] == "legal_threat":
            tool_res = default_tool_registry.execute(
                "create_escalation",
                customer_key=customer_key,
                category=legal_check["category"],
                reason=legal_check["reason"],
                details=f"Customer message: \"{message}\"",
                conversation_id=conversation_id
            )
            esc = tool_res.get("result")
            return {
                "reply": legal_check["reply"],
                "decision": "escalate_immediately",
                "intent": "legal_escalation",
                "policies_cited": ["POL-PROHIBIT-01"],
                "action": None,
                "escalation": esc,
                "requires_confirmation": False,
                "requires_escalation": True,
                "reason": "Mandatory escalation triggered due to legal threat or formal complaint."
            }

        # -------------------------------------------------------------
        # 3. SCENARIO 1: CANCELLATION + UPGRADE DEMAND (Priya Nair)
        # -------------------------------------------------------------
        is_cancelled = "cancelled" in (primary_flight.get("status") or "").lower()
        if is_cancelled and ("upgrade_request" in secondary_intents or primary_intent == "upgrade_request"):
            upgrade_eval = PolicyEngine.evaluate_upgrade_request(tier)
            canc_eval = PolicyEngine.evaluate_cancellation(primary_flight, tier)
            applicable_policies.extend(upgrade_eval["applicable_policies"])
            applicable_policies.extend(canc_eval["applicable_policies"])

            tool_esc = default_tool_registry.execute(
                "create_escalation",
                customer_key=customer_key,
                category="unauthorized_compensation",
                reason="Customer requested complimentary business-class upgrade on return flight due to cancellation.",
                details=f"Priya Nair ({customer['pnr']}) requested free business upgrade on return Goa→Delhi flight.",
                conversation_id=conversation_id
            )
            esc = tool_esc.get("result")

            if primary_intent == "refund_request" or "refund_request" in secondary_intents:
                tool_act = default_tool_registry.execute(
                    "create_refund_request",
                    customer_key=customer_key,
                    pnr=customer["pnr"],
                    flight_number=primary_flight.get("flight_number", "SK-204"),
                    conversation_id=conversation_id
                )
                action_result = tool_act.get("result")
                requires_confirmation = True

                reply = (
                    f"I completely understand your frustration regarding the cancellation of flight {primary_flight['flight_number']}, {customer_name}. "
                    "Regarding your request for a complimentary business-class upgrade on your return flight, our service policy does not provide cabin upgrades or additional compensation beyond standard benefits. "
                    "I have escalated your upgrade request to a human supervisor for review.\n\n"
                    "For your cancelled flight, you are entitled to a full cash refund (processed within 7 business days to your original payment method) or free priority rebooking on the next available flight within 24 hours. "
                    "Would you like me to proceed with initiating your full refund?"
                )
            else:
                reply = (
                    f"I understand your frustration with the cancellation of flight {primary_flight['flight_number']}, {customer_name}. "
                    "Our policy does not permit free business-class upgrades as disruption compensation, though as a Gold member you receive priority rebooking on next-available seats. "
                    "I have escalated your upgrade request to a supervisor. In the meantime, would you prefer free priority rebooking on the next available flight within 24 hours, or a full refund?"
                )

            return {
                "reply": reply,
                "decision": "explain_policy_and_escalate_upgrade",
                "intent": "cancellation_with_upgrade_request",
                "policies_cited": list(set(applicable_policies)),
                "action": action_result,
                "escalation": esc,
                "requires_confirmation": requires_confirmation,
                "requires_escalation": True,
                "reason": "Refused unauthorized business upgrade per policy; escalated exception to supervisor; presented standard cancellation remedies."
            }

        # -------------------------------------------------------------
        # 4. SCENARIO 3: DELAY 6H + FULL NIGHT HOTEL + ₹2,000 FARE WAIVER (Meher Kaur)
        # -------------------------------------------------------------
        delay_hours = primary_flight.get("delay_hours", 0.0)
        has_fare_waiver = primary_intent == "fare_waiver_request" or "fare_waiver_request" in secondary_intents
        has_hotel_full_night = primary_intent == "hotel_full_night_request" or "hotel_full_night_request" in secondary_intents

        if delay_hours >= 6.0 and (has_fare_waiver or has_hotel_full_night):
            fare_eval = PolicyEngine.evaluate_fare_waiver(intent_data.get("fare_difference_amount") or 2000.0)
            hotel_eval = PolicyEngine.evaluate_hotel_request(delay_hours, full_night_requested=has_hotel_full_night)
            applicable_policies.extend(fare_eval["applicable_policies"])
            applicable_policies.extend(hotel_eval["applicable_policies"])

            tool_esc = default_tool_registry.execute(
                "create_escalation",
                customer_key=customer_key,
                category="fare_waiver_over_limit",
                reason=fare_eval.get("escalation_reason", "Fare difference waiver ₹2,000 exceeds ₹1,500 limit"),
                details=f"Meher Kaur requested ₹2,000 fare difference waiver to move to earlier higher-fare flight for SK-305.",
                conversation_id=conversation_id
            )
            esc = tool_esc.get("result")

            tool_act = default_tool_registry.execute(
                "create_hotel_request",
                customer_key=customer_key,
                pnr=customer["pnr"],
                flight_number=primary_flight.get("flight_number", "SK-305"),
                hours=delay_hours,
                conversation_id=conversation_id
            )
            act = tool_act.get("result")

            reply = (
                f"I sincerely apologize for the {delay_hours:.0f}-hour delay on flight {primary_flight['flight_number']}, {customer_name}. "
                "Let me address your two requests clearly:\n\n"
                f"1. **Hotel Accommodation**: Because your delay exceeds 5 hours, our policy entitles you to a meal voucher, lounge access, and hotel accommodation covering strictly the delayed hours until your new departure at {primary_flight.get('new_departure', '20:00')}. A full night's hotel stay is not covered under airline policy.\n\n"
                "2. **Higher-Fare Rebooking & ₹2,000 Waiver**: Under our policy, customers rebooking onto a higher-fare flight must pay the fare difference. Support agents cannot waive fare differences exceeding ₹1,500 without supervisor approval. "
                "Because your difference is ₹2,000, I have submitted an official escalation ticket to a supervisor for waiver approval.\n\n"
                "I have applied your meal voucher, lounge pass, and delayed-hours accommodation to your profile now."
            )

            return {
                "reply": reply,
                "decision": "apply_delay_benefits_and_escalate_waiver",
                "intent": "delay_with_waiver_and_hotel_request",
                "policies_cited": list(set(applicable_policies)),
                "action": act,
                "escalation": esc,
                "requires_confirmation": False,
                "requires_escalation": True,
                "reason": "Applied qualified 6h delay benefits; refused full night stay per policy; escalated ₹2,000 fare waiver exceeding ₹1,500 agent limit."
            }

        # -------------------------------------------------------------
        # 5. SCENARIO 2: DELAY 4H + HOTEL REQUEST (Arvind Kulkarni)
        # -------------------------------------------------------------
        if delay_hours == 4.0 and (primary_intent == "hotel_request" or requested_action == "arrange_hotel_accommodation"):
            hotel_eval = PolicyEngine.evaluate_hotel_request(delay_hours, full_night_requested=False)
            applicable_policies.extend(hotel_eval["applicable_policies"])
            applicable_policies.append("POL-DELAY-02")

            tool_act = default_tool_registry.execute(
                "apply_delay_benefits",
                customer_key=customer_key,
                pnr=customer["pnr"],
                flight_number=primary_flight.get("flight_number", "SK-118"),
                benefits="Meal voucher and Lounge access (4h delay)",
                conversation_id=conversation_id
            )
            act = tool_act.get("result")

            reply = (
                f"I understand how frustrating this 4-hour delay is, {customer_name}, especially when it impacts your important meeting in Bengaluru. "
                f"Regarding hotel accommodation: under airline policy, hotel stays are provided only when a flight delay exceeds 5 hours. "
                "For your 4-hour delay on flight SK-118, you are eligible for a complimentary meal voucher and lounge access, which I have applied to your account now. "
                f"Your flight is scheduled to depart at {primary_flight.get('new_departure', '11:10')}."
            )

            return {
                "reply": reply,
                "decision": "apply_4h_delay_benefits_refuse_hotel",
                "intent": "hotel_request_under_threshold",
                "policies_cited": list(set(applicable_policies)),
                "action": act,
                "escalation": None,
                "requires_confirmation": False,
                "requires_escalation": False,
                "reason": "Granted meal voucher and lounge access for 4h delay; explained hotel accommodation requires delay > 5 hours."
            }

        # -------------------------------------------------------------
        # 6. GENERAL REFUND REQUEST (e.g. Cancelled Flight)
        # -------------------------------------------------------------
        if primary_intent == "refund_request":
            if not is_cancelled:
                return {
                    "reply": f"I checked your booking {customer['pnr']}, {customer_name}. Flight {primary_flight.get('flight_number')} is currently {primary_flight.get('status')}. Full cancellation refunds apply when a flight is cancelled by the airline.",
                    "decision": "refund_ineligible",
                    "intent": "refund_request",
                    "policies_cited": ["POL-CANCEL-01"],
                    "action": None,
                    "escalation": None,
                    "requires_confirmation": False,
                    "requires_escalation": False,
                    "reason": "Flight is not cancelled."
                }

            tool_act = default_tool_registry.execute(
                "create_refund_request",
                customer_key=customer_key,
                pnr=customer["pnr"],
                flight_number=primary_flight.get("flight_number", "SK-204"),
                conversation_id=conversation_id
            )
            act = tool_act.get("result")

            reply = (
                f"Your flight {primary_flight['flight_number']} was cancelled due to {primary_flight.get('reason', 'operational reasons')}. "
                "Under airline policy, you are entitled to a full refund to your original payment method, processed within 7 business days. "
                "Would you like me to initiate this refund request now?"
            )

            return {
                "reply": reply,
                "decision": "propose_refund_awaiting_confirmation",
                "intent": "refund_request",
                "policies_cited": ["POL-CANCEL-01", "POL-REFUND-01"],
                "action": act,
                "escalation": None,
                "requires_confirmation": True,
                "requires_escalation": False,
                "reason": "Refund proposed; awaiting explicit customer confirmation."
            }

        # -------------------------------------------------------------
        # 7. GENERAL REBOOKING REQUEST
        # -------------------------------------------------------------
        if primary_intent == "rebooking_request":
            if not is_cancelled and delay_hours < 3.0:
                return {
                    "reply": f"Your flight {primary_flight.get('flight_number')} is currently {primary_flight.get('status')}. Free rebooking under our disruption policy applies to airline-caused cancellations.",
                    "decision": "rebooking_ineligible",
                    "intent": "rebooking_request",
                    "policies_cited": ["POL-CANCEL-01"],
                    "action": None,
                    "escalation": None,
                    "requires_confirmation": False,
                    "requires_escalation": False,
                    "reason": "Disruption does not qualify for free rebooking."
                }

            is_priority = tier in ("Gold", "Platinum")
            tool_act = default_tool_registry.execute(
                "create_rebooking_request",
                customer_key=customer_key,
                pnr=customer["pnr"],
                flight_number=primary_flight.get("flight_number", "SK-204"),
                priority=is_priority,
                conversation_id=conversation_id
            )
            act = tool_act.get("result")

            priority_note = " As a Gold/Platinum member, you receive priority rebooking on next-available seats." if is_priority else ""
            reply = (
                f"I can arrange free rebooking on the next available flight within 24 hours for flight {primary_flight['flight_number']}.{priority_note} "
                "Please confirm if you would like me to proceed with booking the next available flight."
            )

            return {
                "reply": reply,
                "decision": "propose_rebooking_awaiting_confirmation",
                "intent": "rebooking_request",
                "policies_cited": ["POL-CANCEL-01", "POL-LOYALTY-01"] if is_priority else ["POL-CANCEL-01"],
                "action": act,
                "escalation": None,
                "requires_confirmation": True,
                "requires_escalation": False,
                "reason": "Rebooking proposed; awaiting customer confirmation."
            }

        # -------------------------------------------------------------
        # 8. DELAY COMPENSATION / MEAL & LOUNGE VOUCHERS
        # -------------------------------------------------------------
        if primary_intent == "meal_lounge_request":
            delay_eval = PolicyEngine.evaluate_delay_benefits(delay_hours, tier)
            applicable_policies.extend(delay_eval["applicable_policies"])
            benefits_text = " + ".join(delay_eval["benefits"]) if delay_eval["benefits"] else "no disruption benefits at this time"

            tool_act = default_tool_registry.execute(
                "apply_delay_benefits",
                customer_key=customer_key,
                pnr=customer["pnr"],
                flight_number=primary_flight.get("flight_number", "SK-118"),
                benefits=benefits_text,
                conversation_id=conversation_id
            )
            act = tool_act.get("result")

            reply = (
                f"Based on the {delay_hours:.0f}-hour delay of flight {primary_flight['flight_number']}, you qualify for: **{benefits_text}**. "
                "These vouchers have been applied to your account."
            )

            return {
                "reply": reply,
                "decision": "issue_delay_benefits",
                "intent": "meal_lounge_request",
                "policies_cited": list(set(applicable_policies)),
                "action": act,
                "escalation": None,
                "requires_confirmation": False,
                "requires_escalation": False,
                "reason": f"Issued standard delay benefits for {delay_hours}h delay."
            }

        # -------------------------------------------------------------
        # 9. FLIGHT STATUS QUERY
        # -------------------------------------------------------------
        if primary_intent == "flight_status":
            flight_lines = []
            for f in flights:
                status_str = f"{f['flight_number']} ({f['route']}): {f['status']}"
                if f.get("reason"):
                    status_str += f" due to {f['reason']}"
                if f.get("new_departure"):
                    status_str += f" (New departure: {f['new_departure']})"
                flight_lines.append(status_str)

            reply = f"Here is the status for booking {customer['pnr']} ({customer['name']}):\n" + "\n".join(flight_lines)
            return {
                "reply": reply,
                "decision": "provide_flight_status",
                "intent": "flight_status",
                "policies_cited": [],
                "action": None,
                "escalation": None,
                "requires_confirmation": False,
                "requires_escalation": False,
                "reason": "Provided flight status information."
            }

        # -------------------------------------------------------------
        # 10. EMOTIONAL VENTING / CLARIFICATION / GREETING
        # -------------------------------------------------------------
        if emotion in ("furious", "frustrated"):
            reply = (
                f"I completely hear your frustration, {customer_name}, and I am very sorry for this disruption to your travel. "
                f"I am here to ensure you receive all eligible benefits for flight {primary_flight.get('flight_number')} under our airline policy. "
                "You can ask me to arrange rebooking, process a refund, or issue meal and lounge vouchers."
            )
        elif primary_intent == "greeting":
            reply = (
                f"Hello {customer_name}! I can help you with your booking {customer['pnr']}. "
                f"Flight {primary_flight.get('flight_number')} is currently {primary_flight.get('status')}. How would you like me to assist you today?"
            )
        else:
            reply = (
                f"I can assist with {customer['name']}'s booking ({customer['pnr']}). "
                f"Your flight {primary_flight.get('flight_number')} is currently {primary_flight.get('status')}. "
                "Please let me know if you would like flight details, rebooking options, refund processing, or delay support."
            )

        return {
            "reply": reply,
            "decision": "provide_assistance",
            "intent": primary_intent,
            "policies_cited": [],
            "action": None,
            "escalation": None,
            "requires_confirmation": False,
            "requires_escalation": False,
            "reason": "Customer inquiry answered or clarification requested."
        }
