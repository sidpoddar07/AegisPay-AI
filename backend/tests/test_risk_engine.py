from app.firewall.risk_engine import calculate_risk
from app.models.decision import Decision, CheckStatus


def test_risk_clean_transaction():
    decision, score, reasons = calculate_risk(
        auth_status=CheckStatus.PASS,
        policy_status=CheckStatus.PASS,
        policy_reasons=["Policy pass"],
        threat_status=CheckStatus.PASS,
        threat_score=5.0,
        threat_reasons=["No threats"],
    )

    assert decision == Decision.ALLOW
    assert score < 30.0


def test_risk_unauthorized_agent():
    decision, score, reasons = calculate_risk(
        auth_status=CheckStatus.FAIL,
        policy_status=CheckStatus.PASS,
        policy_reasons=["Policy pass"],
        threat_status=CheckStatus.PASS,
        threat_score=0.0,
        threat_reasons=[],
    )

    assert decision == Decision.BLOCK
    assert score == 100.0


def test_risk_review_band():
    decision, score, reasons = calculate_risk(
        auth_status=CheckStatus.PASS,
        policy_status=CheckStatus.WARNING,
        policy_reasons=["High value transaction"],
        threat_status=CheckStatus.PASS,
        threat_score=15.0,
        threat_reasons=[],
    )

    assert decision == Decision.REVIEW
    assert 30.0 <= score < 75.0


def test_risk_prompt_injection_block():
    decision, score, reasons = calculate_risk(
        auth_status=CheckStatus.PASS,
        policy_status=CheckStatus.PASS,
        policy_reasons=["Policy pass"],
        threat_status=CheckStatus.FAIL,
        threat_score=85.0,
        threat_reasons=["Prompt Injection detected"],
    )

    assert decision == Decision.BLOCK
    assert score >= 75.0
