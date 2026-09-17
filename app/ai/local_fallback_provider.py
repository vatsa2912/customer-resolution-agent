import re
import json
from typing import List, Dict, Any, Optional
from app.ai.base_provider import BaseAIProvider

class LocalFallbackProvider(BaseAIProvider):
    def __init__(self, model_name: str = "local-deterministic-engine"):
        super().__init__(model_name)

    @property
    def provider_name(self) -> str:
        return "local"

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "status": "ready",
            "message": "Deterministic offline reasoning engine active. 0 external API dependencies."
        }

    def complete(self, messages: List[Dict[str, str]], system_prompt: str, response_format_json: bool = True) -> Dict[str, Any]:
        # Extract the latest user message
        user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user" or m.get("sender") == "customer":
                user_message = m.get("content", "") or m.get("message", "")
                break

        parsed = self.extract_structured_intent(user_message, messages)

        return {
            "raw_content": json.dumps(parsed, indent=2),
            "parsed_json": parsed,
            "provider": self.provider_name,
            "model": self.model_name,
            "success": True,
            "error": None
        }

    def extract_structured_intent(self, text: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        lower = text.lower().strip()

        # Emotion detection
        emotion = "neutral"
        if any(w in lower for w in ["furious", "livid", "enraged", "mad"]):
            emotion = "furious"
        elif any(w in lower for w in ["frustrated", "unacceptable", "terrible", "ruined", "ridiculous", "horrible", "annoyed", "upset"]):
            emotion = "frustrated"
        elif any(w in lower for w in ["please", "thank", "kindly"]):
            emotion = "polite"

        urgency = "high" if (emotion in ("furious", "frustrated") or any(w in lower for w in ["urgent", "immediately", "now", "emergency", "asap"])) else "normal"

        # Check for confirmation / cancellation in multi-turn context
        last_agent_message = ""
        if history:
            for m in reversed(history):
                sender = m.get("role") or m.get("sender")
                if sender in ("assistant", "agent"):
                    last_agent_message = (m.get("content") or m.get("message") or "").lower()
                    break

        awaiting_confirm = any(q in last_agent_message for q in ["confirm", "would you like me to", "which would you prefer", "do you want me to", "proceed"])

        # Intent classification
        primary_intent = "unknown"
        secondary_intents = []
        requested_action = None
        fare_difference_amount = None

        # 1. Legal / Formal complaint (immediate priority)
        if any(w in lower for w in ["legal action", "lawyer", "court", "formal complaint", "consumer court", "consumer forum", "sue"]):
            primary_intent = "legal_escalation"
            requested_action = "escalate_legal_complaint"

        # 2. Confirmation or rejection if awaiting confirmation
        elif awaiting_confirm and any(lower == w or lower.startswith(w + " ") or lower.endswith(" " + w) or w in lower for w in [
            "yes", "confirm", "proceed", "go ahead", "please do", "sure", "approve", "do it", "i confirm", "yes please", "yes initiate", "yes, please"
        ]):
            primary_intent = "action_confirmation"
            requested_action = "confirm_pending_action"
        elif awaiting_confirm and any(lower == w or lower.startswith(w + " ") or w in lower for w in [
            "no", "cancel", "don't", "stop", "never mind", "reject", "decline"
        ]):
            primary_intent = "action_cancellation"
            requested_action = "cancel_pending_action"

        # 3. Fare waiver / extra amount removal
        is_fare_query = (
            ("fare" in lower and any(w in lower for w in ["waive", "waiver", "difference", "remove", "cover", "extra"])) or
            (any(w in lower for w in ["waive", "waiver"]) and any(w in lower for w in ["2000", "2,000", "fare", "fee", "difference"])) or
            (any(w in lower for w in ["remove the extra", "remove extra", "waive the ₹2,000", "waive the 2000", "waive it"])) or
            ("2,000" in lower or "2000" in lower) and any(w in lower for w in ["waive", "remove", "cover", "extra", "difference"])
        )
        if is_fare_query:
            fare_intent = "fare_waiver_request"
            if primary_intent == "unknown":
                primary_intent = fare_intent
            else:
                secondary_intents.append(fare_intent)
            if "2000" in lower or "2,000" in lower:
                fare_difference_amount = 2000.0
            else:
                fare_match = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9,]+)', lower)
                if fare_match:
                    try:
                        fare_difference_amount = float(fare_match.group(1).replace(",", ""))
                    except Exception:
                        pass
            requested_action = "waive_fare_difference"

        # 4. Hotel accommodation / Full night
        if any(w in lower for w in ["full night", "whole night", "overnight", "night's hotel", "night stay", "entire night"]):
            hotel_night_intent = "hotel_full_night_request"
            if primary_intent == "unknown":
                primary_intent = hotel_night_intent
            else:
                secondary_intents.append(hotel_night_intent)
            if not requested_action or requested_action == "waive_fare_difference":
                requested_action = "arrange_full_night_hotel"
        elif any(w in lower for w in ["hotel", "place to stay", "accommodation", "room"]):
            hotel_intent = "hotel_request"
            if primary_intent == "unknown":
                primary_intent = hotel_intent
            else:
                secondary_intents.append(hotel_intent)
            if not requested_action:
                requested_action = "arrange_hotel_accommodation"

        # 5. Upgrade to business class
        if any(w in lower for w in ["business class", "business-class", "upgrade", "first class", "seat upgrade"]):
            upgrade_intent = "upgrade_request"
            if primary_intent == "unknown":
                primary_intent = upgrade_intent
            else:
                secondary_intents.append(upgrade_intent)
            if not requested_action:
                requested_action = "business_class_upgrade"

        # 6. Refund request
        if any(w in lower for w in [
            "refund", "money back", "return my money", "cash refund", "cash back",
            "return the amount", "don't want to travel", "cancel and refund", "return the amount i paid"
        ]):
            refund_intent = "refund_request"
            if primary_intent == "unknown":
                primary_intent = refund_intent
            else:
                secondary_intents.append(refund_intent)
            requested_action = "full_refund"

        # 7. Rebooking / alternative flight
        if any(w in lower for w in [
            "rebook", "another flight", "next flight", "next available",
            "change flight", "move me", "get to goa", "get to destination",
            "reschedule", "alternative flight", "take another flight"
        ]):
            rebook_intent = "rebooking_request"
            if primary_intent == "unknown":
                primary_intent = rebook_intent
            else:
                secondary_intents.append(rebook_intent)
            if not requested_action or requested_action == "full_refund":
                if requested_action != "full_refund":
                    requested_action = "rebook_flight"

        # 8. Meal voucher & lounge
        if any(w in lower for w in ["voucher", "meal", "food", "lounge", "refreshment"]):
            comp_intent = "meal_lounge_request"
            if primary_intent == "unknown":
                primary_intent = comp_intent
            else:
                secondary_intents.append(comp_intent)
            if not requested_action:
                requested_action = "issue_delay_benefits"

        # 9. Flight status / Options
        if primary_intent == "unknown" and any(w in lower for w in [
            "status", "delayed", "cancelled", "departure", "timing", "what happened", "why", "when", "what are my options"
        ]):
            primary_intent = "flight_status"
            requested_action = "provide_flight_status"

        # 10. Ambiguous / Greeting
        if primary_intent == "unknown":
            if any(w in lower for w in ["hi", "hello", "hey", "good morning", "good evening"]):
                primary_intent = "greeting"
            else:
                primary_intent = "general_query"

        # Precise PNR / Booking Reference extraction
        customer_reference = None
        explicit_match = re.search(r'\b(?:pnr|booking|ref(?:erence)?)\s*[:#]?\s*([A-Za-z0-9]{5,7})\b', text, re.IGNORECASE)
        if explicit_match:
            customer_reference = explicit_match.group(1).upper()
        else:
            # Check for tokens that have both letters and digits (e.g. SK4821X, TR1190B, WL7742)
            for word in re.findall(r'\b[A-Za-z0-9]{5,7}\b', text):
                w_upper = word.upper()
                if any(c.isdigit() for c in w_upper) and any(c.isalpha() for c in w_upper):
                    customer_reference = w_upper
                    break

        return {
            "primary_intent": primary_intent,
            "secondary_intents": secondary_intents,
            "customer_reference": customer_reference,
            "requested_action": requested_action,
            "fare_difference_amount": fare_difference_amount,
            "emotion": emotion,
            "urgency": urgency,
            "requires_clarification": primary_intent in ("general_query", "unknown"),
            "missing_information": [],
            "policy_question": True
        }
