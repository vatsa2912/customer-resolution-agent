import pytest
from app.database import init_db, seed_initial_data
from app.database.connection import get_db_connection
from app.services.action_service import ActionService
from app.database.repositories import ActionRepository

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    seed_initial_data()
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM actions")
    conn.close()

def test_action_lifecycle_and_confirmation():
    svc = ActionService()
    idemp_key = "test_priya_refund_123"

    # 1. Propose action requiring confirmation
    proposed = svc.propose_action(
        customer_key="priya",
        action_type="refund_request",
        details="Full refund for flight SK-204",
        idempotency_key=idemp_key,
        requires_confirmation=True
    )
    assert proposed["status"] == "awaiting_confirmation"
    assert proposed["requires_confirmation"] is True
    action_id = proposed["action_id"]

    # Check pending
    pending = svc.get_pending_action("priya")
    assert pending is not None
    assert pending["id"] == action_id

    # 2. Confirm action
    confirmed = svc.confirm_action(action_id)
    assert confirmed["success"] is True
    assert confirmed["status"] == "executed"
    assert "Simulated Execution" in confirmed["details"]

    # 3. Check no more pending
    assert svc.get_pending_action("priya") is None

    # 4. Idempotency test: Proposing again with same key returns existing executed action
    duplicate = svc.propose_action(
        customer_key="priya",
        action_type="refund_request",
        details="Duplicate refund attempt",
        idempotency_key=idemp_key,
        requires_confirmation=True
    )
    assert duplicate["already_executed"] is True
    assert duplicate["status"] == "executed"
    assert duplicate["action_id"] == action_id

def test_action_cancellation():
    svc = ActionService()
    idemp_key = "test_cancel_action_456"

    proposed = svc.propose_action(
        customer_key="arvind",
        action_type="hotel_accommodation",
        details="Hotel accommodation request",
        idempotency_key=idemp_key,
        requires_confirmation=True
    )
    action_id = proposed["action_id"]

    # Customer declines
    cancelled = svc.cancel_action(action_id, reason="Customer decided to stay at airport")
    assert cancelled["success"] is True
    assert cancelled["status"] == "rejected"
