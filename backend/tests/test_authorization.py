from app.firewall.authorization import check_authorization
from app.models.decision import CheckStatus
from app.models.transaction import PaymentRequest


def test_authorized_payment_tool():
    request = PaymentRequest(
        agent_id="shopping-agent-01",
        user_id="user-101",
        tool_name="create_payment",
        amount=1500,
        currency="INR",
        recipient_id="amazon-001",
        reason="Purchase requested by user",
    )

    result = check_authorization(request)
    assert result == CheckStatus.PASS


def test_unauthorized_payment_tool():
    request = PaymentRequest(
        agent_id="finance-agent-01",
        user_id="user-101",
        tool_name="create_payment",
        amount=1500,
        currency="INR",
        recipient_id="amazon-001",
        reason="Purchase requested by user",
    )

    result = check_authorization(request)
    assert result == CheckStatus.FAIL


def test_unknown_agent():
    request = PaymentRequest(
        agent_id="unknown-agent",
        user_id="user-101",
        tool_name="create_payment",
        amount=1500,
        currency="INR",
        recipient_id="amazon-001",
        reason="Purchase requested by user",
    )

    result = check_authorization(request)
    assert result == CheckStatus.FAIL
