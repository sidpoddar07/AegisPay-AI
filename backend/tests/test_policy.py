from app.firewall.policy import check_policy
from app.models.decision import CheckStatus
from app.models.transaction import PaymentRequest


def test_policy_pass_normal_amount():
    request = PaymentRequest(
        agent_id="shopping-agent-01",
        user_id="user-101",
        tool_name="create_payment",
        amount=1200.0,
        currency="INR",
        recipient_id="amazon-001",
        reason="Purchase requested by user",
    )

    status, reasons = check_policy(request)
    assert status == CheckStatus.PASS
    assert len(reasons) > 0


def test_policy_fail_exceeds_limit():
    request = PaymentRequest(
        agent_id="shopping-agent-01",
        user_id="user-101",
        tool_name="create_payment",
        amount=5500.0,  # Limit is 5000.0
        currency="INR",
        recipient_id="amazon-001",
        reason="Large unauthorized purchase",
    )

    status, reasons = check_policy(request)
    assert status == CheckStatus.FAIL
    assert any("exceeds agent limit" in r for r in reasons)


def test_policy_fail_blocked_recipient():
    request = PaymentRequest(
        agent_id="shopping-agent-01",
        user_id="user-101",
        tool_name="create_payment",
        amount=500.0,
        currency="INR",
        recipient_id="attacker-vpa-01",
        reason="Payment to suspicious party",
    )

    status, reasons = check_policy(request)
    assert status == CheckStatus.FAIL
    assert any("blacklist" in r for r in reasons)


def test_policy_warning_high_value_band():
    request = PaymentRequest(
        agent_id="shopping-agent-01",
        user_id="user-101",
        tool_name="create_payment",
        amount=4000.0,  # 80% of 5000 limit -> WARNING band
        currency="INR",
        recipient_id="flipkart-002",
        reason="High value item order",
    )

    status, reasons = check_policy(request)
    assert status == CheckStatus.WARNING
    assert any("high-value review band" in r for r in reasons)
