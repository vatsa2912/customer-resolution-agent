import pytest
from app.database import init_db, seed_initial_data
from app.agents.resolution_agent import CustomerResolutionAgent
from app.database.repositories import ConversationRepository, ActionRepository, EscalationRepository
from app.services.action_service import ActionService

@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    seed_initial_data()
    conv = ConversationRepository()
    for key in ["priya", "arvind", "meher"]:
        conv.clear_history(key)

def test_scenario_1_priya_nair():
    agent = CustomerResolutionAgent()

    # Step 1: Priya's initial prompt
    msg = "I am furious. My flight was cancelled. I want a full cash refund plus a free upgrade to business class on my return flight."
    res = agent.handle(msg, customer_key="priya")

    # 1. Professional handling of anger
    assert "frustration" in res["reply"].lower() or "sorry" in res["reply"].lower()
    # 2. Rejection of unauthorized business-class upgrade per policy
    assert "policy" in res["reply"].lower()
    assert "upgrade" in res["reply"].lower()
    # 3. Escalation of the upgrade exception request
    assert res["escalated"] is True
    assert res["escalation"] is not None
    assert res["escalation"]["category"] == "unauthorized_compensation"
    # 4. Presentation of valid refund or rebooking options
    assert "refund" in res["reply"].lower()
    # 5. Proposed action awaiting customer confirmation
    assert res["requires_confirmation"] is True
    assert res["action"] is not None
    assert res["action"]["status"] == "awaiting_confirmation"

    # Step 2: Multi-turn confirmation
    confirm_msg = "Yes, please initiate the refund."
    res2 = agent.handle(confirm_msg, customer_key="priya")

    # 6. Safe execution upon explicit confirmation
    assert "confirmed" in res2["reply"].lower() or "initiated" in res2["reply"].lower() or "thank you" in res2["reply"].lower()
    assert res2["action"]["status"] == "executed"
    assert "Simulated Execution" in res2["action"]["details"]

def test_scenario_2_arvind_kulkarni():
    agent = CustomerResolutionAgent()

    # Arvind's prompt
    msg = "My flight is delayed by 4 hours. I missed an important meeting. I want hotel accommodation."
    res = agent.handle(msg, customer_key="arvind")

    # 1. Empathetic acknowledgement of 4-hour delay and missed meeting
    assert "4" in res["reply"]
    # 2. Applies meal voucher + lounge access per >3h delay rule
    assert "meal voucher" in res["reply"].lower()
    assert "lounge access" in res["reply"].lower()
    # 3. Explains hotel accommodation is provided only for delays > 5 hours
    assert "5 hours" in res["reply"].lower()
    # 4. Action record created for delay benefits
    assert res["action"] is not None
    assert "meal voucher" in res["action"]["details"].lower()

def test_scenario_3_meher_kaur():
    agent = CustomerResolutionAgent()

    # Meher's prompt
    msg = "My flight is delayed by 6 hours. I want a full night's hotel stay. Also move me to another higher-fare flight. The fare difference is ₹2,000. I want you to waive it."
    res = agent.handle(msg, customer_key="meher")

    # 1. 6-hour delay benefits: meal voucher + lounge + hotel for delayed hours only
    assert "meal voucher" in res["reply"].lower()
    assert "lounge" in res["reply"].lower()
    assert "hotel" in res["reply"].lower()
    assert "delayed hours" in res["reply"].lower()
    # 2. Explains full night hotel stay is NOT covered
    assert "full night" in res["reply"].lower()
    # 3. Explains ₹2,000 fare difference and ₹1,500 supervisor waiver limit
    assert "1,500" in res["reply"] or "1500" in res["reply"]
    assert "2,000" in res["reply"] or "2000" in res["reply"]
    # 4. Escalates the ₹2,000 fare waiver to human supervisor
    assert res["escalated"] is True
    assert res["escalation"] is not None
    assert res["escalation"]["category"] == "fare_waiver_over_limit"
    # 5. Keeps hotel and fare waiver issues clearly separated
    assert "hotel" in res["reply"].lower() and "fare" in res["reply"].lower()

def test_legal_action_immediate_escalation():
    agent = CustomerResolutionAgent()

    msg = "I will take legal action and file a formal consumer complaint!"
    res = agent.handle(msg, customer_key="arvind")

    assert res["escalated"] is True
    assert res["escalation"]["category"] == "legal_threat"
    assert "specialist support" in res["reply"].lower() or "escalating" in res["reply"].lower()

def test_rebooking_confirmation_flow():
    agent = CustomerResolutionAgent()

    # Priya asks for rebooking
    res = agent.handle("Can you rebook me on the next flight to Goa?", customer_key="priya")
    assert res["requires_confirmation"] is True
    assert res["action"]["status"] == "awaiting_confirmation"
    assert "rebook" in res["action"]["action_type"].lower()

    # Priya confirms
    res2 = agent.handle("Yes, please confirm rebooking", customer_key="priya")
    assert res2["action"]["status"] == "executed"
    assert "Simulated Execution" in res2["action"]["details"]

def test_cancelled_action_cannot_execute():
    svc = ActionService()
    res = svc.propose_action(
        customer_key="priya",
        action_type="refund_request",
        details="Refund test",
        idempotency_key="test_cancel_cannot_exec",
        requires_confirmation=True
    )
    action_id = res["action_id"]

    # Cancel action
    canc = svc.cancel_action(action_id, reason="Customer changed mind")
    assert canc["status"] == "rejected"

    # Attempt to confirm cancelled action
    conf = svc.confirm_action(action_id)
    assert conf["success"] is False
    assert "Cannot execute action in status 'rejected'" in conf["error"]

def test_unknown_booking_reference():
    agent = CustomerResolutionAgent()

    res = agent.handle("Can you check flight status for booking XYZ999?", customer_key="priya")
    assert "XYZ999" in res["reply"]
    assert "not found" in res["reply"].lower()

def test_ambiguous_request_handling():
    agent = CustomerResolutionAgent()

    res = agent.handle("I need help with my flight.", customer_key="arvind")
    assert res["action"] is None
    assert res["escalated"] is False
    assert "flight" in res["reply"].lower()

def test_angry_customer_composure():
    agent = CustomerResolutionAgent()

    res = agent.handle("This delay is completely ridiculous and unacceptable!", customer_key="arvind")
    assert "frustration" in res["reply"].lower() or "sorry" in res["reply"].lower()
    # Does not invent compensation
    assert res["escalated"] is False
