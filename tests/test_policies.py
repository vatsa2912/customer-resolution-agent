import pytest
from app.policies.policy_engine import PolicyEngine

def test_cancellation_evaluation():
    # Cancelled flight
    flight = {"status": "Cancelled (operational reasons)", "reason": "operational reasons"}
    res = PolicyEngine.evaluate_cancellation(flight, tier="Gold")
    assert res["eligible"] is True
    assert "free_rebooking_24h" in res["options"]
    assert "full_refund" in res["options"]
    assert res["refund_payment_method"] == "original_payment_method_only"
    assert res["priority_rebooking"] is True
    assert "POL-CANCEL-01" in res["applicable_policies"]

    # Non-cancelled flight
    flight_ok = {"status": "On-time", "reason": ""}
    res_ok = PolicyEngine.evaluate_cancellation(flight_ok, tier="Silver")
    assert res_ok["eligible"] is False

def test_delay_benefits_under_3_hours():
    res = PolicyEngine.evaluate_delay_benefits(2.5, tier="Silver")
    assert "₹500 meal voucher" in res["benefits"]
    assert "lounge access" not in res["benefits"]
    assert res["hotel_eligible"] is False
    assert "POL-DELAY-01" in res["applicable_policies"]

def test_delay_benefits_between_3_and_5_hours():
    res = PolicyEngine.evaluate_delay_benefits(4.0, tier="Silver")
    assert "meal voucher" in res["benefits"]
    assert "lounge access" in res["benefits"]
    assert res["hotel_eligible"] is False
    assert "POL-DELAY-02" in res["applicable_policies"]

def test_delay_benefits_over_5_hours():
    res = PolicyEngine.evaluate_delay_benefits(6.0, tier="Platinum")
    assert "meal voucher" in res["benefits"]
    assert "lounge access" in res["benefits"]
    assert res["hotel_eligible"] is True
    assert res["hotel_scope"] == "delayed_hours_only"
    assert "POL-DELAY-03" in res["applicable_policies"]
    assert "POL-LOYALTY-01" in res["applicable_policies"]

def test_fare_waiver_threshold():
    # Under agent limit <= 1500
    res_under = PolicyEngine.evaluate_fare_waiver(1200)
    assert res_under["can_agent_waive"] is True
    assert res_under["requires_supervisor"] is False

    # Over agent limit > 1500
    res_over = PolicyEngine.evaluate_fare_waiver(2000)
    assert res_over["can_agent_waive"] is False
    assert res_over["requires_supervisor"] is True
    assert "POL-PROHIBIT-01" in res_over["applicable_policies"]

def test_upgrade_request_restriction():
    res = PolicyEngine.evaluate_upgrade_request(tier="Gold")
    assert res["allowed"] is False
    assert res["requires_escalation"] is True
    assert "POL-LOYALTY-01" in res["applicable_policies"]
    assert "POL-PROHIBIT-01" in res["applicable_policies"]

def test_hotel_request_policy():
    # 4h delay asks for hotel -> not eligible
    res_4h = PolicyEngine.evaluate_hotel_request(4.0, full_night_requested=False)
    assert res_4h["eligible"] is False
    assert res_4h["requires_escalation"] is False

    # 6h delay asks for full night -> eligible for delayed hours only, full night requires escalation
    res_6h = PolicyEngine.evaluate_hotel_request(6.0, full_night_requested=True)
    assert res_6h["eligible"] is True
    assert res_6h["full_night_allowed"] is False
    assert res_6h["requires_escalation"] is True
