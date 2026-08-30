from typing import List, Tuple
from app.models.decision import Decision, CheckStatus


def calculate_risk(
    auth_status: CheckStatus,
    policy_status: CheckStatus,
    policy_reasons: List[str],
    threat_status: CheckStatus,
    threat_score: float,
    threat_reasons: List[str],
) -> Tuple[Decision, float, List[str]]:
    """
    Computes a composite multi-signal risk score (0-100) and produces the final Decision.
    
    Decision Bands:
      - 0 <= Score < 30 : ALLOW
      - 30 <= Score < 75 : REVIEW
      - Score >= 75     : BLOCK
    """
    all_reasons = []

    # 1. Hard Authorization Failure
    if auth_status == CheckStatus.FAIL:
        return Decision.BLOCK, 100.0, ["CRITICAL: Agent is not authorized to call payment tools."]

    # 2. Hard Threat Detection Failure (Prompt Injection / Attack)
    if threat_status == CheckStatus.FAIL:
        all_reasons.extend(threat_reasons)
        final_score = round(max(85.0, threat_score), 2)
        return Decision.BLOCK, final_score, all_reasons

    # 3. Hard Policy Failure (Limit Exceeded / Blacklisted Recipient)
    if policy_status == CheckStatus.FAIL:
        all_reasons.extend(policy_reasons)
        final_score = round(max(90.0, threat_score), 2)
        return Decision.BLOCK, final_score, all_reasons

    # 4. Calculate Risk Signals for Warnings / Benign Checks
    if policy_status == CheckStatus.WARNING:
        policy_risk = 50.0
    else:
        policy_risk = 0.0

    threat_risk = threat_score

    # Composite score for warnings
    composite_score = (threat_risk * 0.5) + (policy_risk * 0.7)
    composite_score = round(min(100.0, max(0.0, composite_score)), 2)

    # Collect reason notes
    all_reasons.extend([r for r in policy_reasons if "satisfied" not in r])
    all_reasons.extend([r for r in threat_reasons if "No active" not in r])

    # Determine Decision based on thresholds
    if composite_score >= 75.0:
        decision = Decision.BLOCK
    elif composite_score >= 30.0 or policy_status == CheckStatus.WARNING or threat_status == CheckStatus.WARNING:
        decision = Decision.REVIEW
        # Ensure score is in the review band (30-74)
        composite_score = max(35.0, composite_score)
    else:
        decision = Decision.ALLOW

    if not all_reasons:
        all_reasons.append("All security, policy, and threat checks passed cleanly.")

    return decision, composite_score, all_reasons
