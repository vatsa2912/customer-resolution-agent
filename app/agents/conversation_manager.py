from typing import Dict, Any, Optional
from app.database.repositories import CustomerRepository, ConversationRepository, AuditRepository
from app.ai.provider_factory import ProviderFactory
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.decision_engine import DecisionEngine

class ConversationManager:
    def __init__(
        self,
        cust_repo: Optional[CustomerRepository] = None,
        conv_repo: Optional[ConversationRepository] = None,
        decision_engine: Optional[DecisionEngine] = None
    ):
        self.cust_repo = cust_repo or CustomerRepository()
        self.conv_repo = conv_repo or ConversationRepository()
        self.decision_engine = decision_engine or DecisionEngine()
        self.audit_repo = AuditRepository()

    def handle_message(self, customer_key: str, message: str, force_provider: Optional[str] = None) -> Dict[str, Any]:
        customer = self.cust_repo.get_by_key(customer_key)
        if not customer:
            return {
                "reply": "Please select one of the three supplied customers (Priya, Arvind, Meher) to proceed.",
                "intent": "unknown_customer",
                "action": None,
                "escalated": False,
                "requires_confirmation": False
            }

        conv_id = self.conv_repo.get_or_create_active(customer_key)
        history = self.conv_repo.get_messages(customer_key)

        # 1. Obtain AI Provider
        provider = ProviderFactory.get_provider(force_provider)
        
        # 2. Extract structured intent via provider
        ai_response = provider.complete(
            messages=history + [{"role": "user", "content": message}],
            system_prompt=SYSTEM_PROMPT,
            response_format_json=True
        )

        intent_data = ai_response.get("parsed_json") or {}
        if not intent_data or not isinstance(intent_data, dict):
            # Safe fallback if LLM response failed to parse
            from app.ai.local_fallback_provider import LocalFallbackProvider
            fallback = LocalFallbackProvider()
            intent_data = fallback.extract_structured_intent(message, history)

        # 3. Process decision with deterministic Policy Engine
        decision = self.decision_engine.process_decision(
            customer=customer,
            intent_data=intent_data,
            message=message,
            history=history,
            conversation_id=conv_id
        )

        # 4. Save Customer and Agent Messages
        self.conv_repo.add_message(
            conversation_id=conv_id,
            customer_key=customer_key,
            sender="customer",
            content=message,
            intent=decision.get("intent")
        )
        self.conv_repo.add_message(
            conversation_id=conv_id,
            customer_key=customer_key,
            sender="agent",
            content=decision.get("reply"),
            intent=decision.get("intent"),
            metadata={
                "policies_cited": decision.get("policies_cited"),
                "decision": decision.get("decision"),
                "provider": provider.provider_name,
                "model": provider.model_name
            }
        )

        return {
            "reply": decision["reply"],
            "intent": decision["intent"],
            "decision": decision["decision"],
            "policies_cited": decision["policies_cited"],
            "action": decision["action"],
            "escalation": decision["escalation"],
            "escalated": bool(decision.get("escalation")),
            "requires_confirmation": decision.get("requires_confirmation", False),
            "reason": decision.get("reason"),
            "provider_used": provider.provider_name,
            "model_used": provider.model_name
        }
