from typing import List, Tuple
from app.models.decision import CheckStatus
from app.models.transaction import PaymentRequest

# Per-agent maximum limit for a single transaction
AGENT_MAX_LIMITS = {
    "shopping-agent-01": 5000.0,
    "finance-agent-01": 10000.0,
}
DEFAULT_MAX_LIMIT = 2000.0

# Blacklisted recipients (known fraud / high-risk accounts)
BLOCKED_RECIPIENTS = {
    "darkweb-merchant-666",
    "attacker-vpa-01",
    "unverified-crypto-pool",
    "blacklisted-merchant-09",
}

# Soft threshold (triggers WARNING for human review if > 70% of max limit)
WARNING_RATIO = 0.70


def check_policy(request: PaymentRequest) -> Tuple[CheckStatus, List[str]]:
    """
    Evaluates a payment request against financial and operational policy rules.
    Returns a CheckStatus (PASS, WARNING, FAIL) and a list of reason strings.
    """
    reasons = []

    # Rule 1: Check Recipient Blacklist
    if request.recipient_id in BLOCKED_RECIPIENTS:
        reasons.append(f"Recipient '{request.recipient_id}' is on the financial fraud blacklist.")
        return CheckStatus.FAIL, reasons

    # Rule 2: Check Amount Limit
    max_limit = AGENT_MAX_LIMITS.get(request.agent_id, DEFAULT_MAX_LIMIT)
    
    if request.amount > max_limit:
        reasons.append(f"Amount ₹{request.amount:.2f} exceeds agent limit of ₹{max_limit:.2f}.")
        return CheckStatus.FAIL, reasons

    # Rule 3: High-Value Warning Threshold
    if request.amount >= (max_limit * WARNING_RATIO):
        reasons.append(f"Amount ₹{request.amount:.2f} is in the high-value review band (>= {int(WARNING_RATIO*100)}% of limit).")
        return CheckStatus.WARNING, reasons

    return CheckStatus.PASS, ["All financial policy constraints satisfied."]
