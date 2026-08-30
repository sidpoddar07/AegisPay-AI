from app.models.decision import CheckStatus
from app.models.transaction import PaymentRequest


ALLOWED_TOOLS = {
    "shopping-agent-01": {
        "create_payment",
        "get_payment_status",
    },
    "finance-agent-01": {
        "get_payment_status",
    },
}


def check_authorization(request: PaymentRequest) -> CheckStatus:
    """
    Check whether the agent is allowed to call the requested tool.
    """
    allowed_tools = ALLOWED_TOOLS.get(request.agent_id)

    if allowed_tools is None:
        return CheckStatus.FAIL

    if request.tool_name not in allowed_tools:
        return CheckStatus.FAIL

    return CheckStatus.PASS
