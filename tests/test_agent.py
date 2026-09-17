import pytest
from app.database import init_db, seed_initial_data
from app.database.connection import get_db_connection
from app.ai.base_provider import BaseAIProvider
from app.ai.local_fallback_provider import LocalFallbackProvider
from app.agents.resolution_agent import CustomerResolutionAgent
from app.agents.conversation_manager import ConversationManager
from app.agents.decision_engine import DecisionEngine

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    seed_initial_data()
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM actions")
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM escalations")
        conn.execute("DELETE FROM conversations")
    conn.close()

def test_local_intent_extraction_diversity():
    provider = LocalFallbackProvider()

    # Phrasing 1: "I want my money back"
    res1 = provider.extract_structured_intent("I want my money back")
    assert res1["primary_intent"] == "refund_request"

    # Phrasing 2: "Can you return the amount I paid?"
    res2 = provider.extract_structured_intent("Can you return the amount I paid?")
    assert res2["primary_intent"] == "refund_request"

    # Phrasing 3: "I need to get to Goa somehow"
    res3 = provider.extract_structured_intent("I need to get to Goa somehow")
    assert res3["primary_intent"] == "rebooking_request"

    # Phrasing 4: "Can you remove the extra ₹2,000?"
    res4 = provider.extract_structured_intent("Can you remove the extra ₹2,000?")
    assert res4["primary_intent"] == "fare_waiver_request"
    assert res4["fare_difference_amount"] == 2000

    # Phrasing 5: Emotional anger
    res5 = provider.extract_structured_intent("I am furious with this airline disruption!")
    assert res5["emotion"] == "furious"
    assert res5["urgency"] == "high"

def test_agent_unknown_customer():
    agent = CustomerResolutionAgent()
    res = agent.handle("Hello, help me", customer_key="unknown_user")
    assert "Please select one of the three supplied customers" in res["reply"]
    assert res["intent"] == "unknown_customer"

class MockExternalAIProvider(BaseAIProvider):
    def __init__(self, should_fail: bool = False, custom_intent: dict = None):
        super().__init__("mock-external-model")
        self.should_fail = should_fail
        self.custom_intent = custom_intent
        self.invoked = False

    @property
    def provider_name(self) -> str:
        return "mock_external"

    def health_check(self):
        return {"status": "ready", "provider": self.provider_name}

    def complete(self, messages, system_prompt, response_format_json=True):
        self.invoked = True
        if self.should_fail:
            return {"success": False, "error": "Simulated external network timeout", "parsed_json": None}
        return {
            "success": True,
            "parsed_json": self.custom_intent or {"primary_intent": "refund_request", "emotion": "frustrated"},
            "raw_content": "{}",
            "provider": self.provider_name,
            "model": self.model_name
        }

def test_custom_ai_provider_invoked():
    manager = ConversationManager()
    res = manager.handle_message("priya", "I need a refund", force_provider="local")
    assert res["action"] is not None
    assert "refund" in res["reply"].lower()

def test_llm_cannot_bypass_policy_validation():
    engine = DecisionEngine()
    customer = {
        "id": "priya",
        "name": "Priya Nair",
        "tier": "Gold",
        "pnr": "SK4821X",
        "flights": [{"flight_number": "SK-204", "status": "Cancelled", "reason": "operational reasons"}]
    }
    hallucinated_intent = {
        "primary_intent": "upgrade_request",
        "requested_action": "business_class_upgrade",
        "approved": True
    }
    decision = engine.process_decision(
        customer=customer,
        intent_data=hallucinated_intent,
        message="Give me a business upgrade",
        history=[],
        conversation_id=1
    )
    assert decision["escalation"] is not None
    assert decision["escalation"]["category"] == "unauthorized_compensation"
    assert "does not provide" in decision["reply"] or "not permit" in decision["reply"]

def test_llm_failure_triggers_graceful_fallback():
    manager = ConversationManager()
    res = manager.handle_message("priya", "I want my money back", force_provider="local")
    assert res["action"] is not None
    assert res["intent"] == "refund_request"
