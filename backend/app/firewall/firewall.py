import time
import uuid
import hmac
import hashlib
from app.models.decision import Decision, CheckStatus, FirewallEvaluation
from app.models.transaction import PaymentRequest
from app.firewall.authorization import check_authorization
from app.firewall.policy import check_policy
from app.firewall.threat_detection import check_threat
from app.firewall.risk_engine import calculate_risk

SECRET_KEY = "razorpay_buildathon_aegispay_secret_2026"


def generate_poi_token(request_id: str, request: PaymentRequest) -> str:
    """
    Generates an HMAC-SHA256 Proof-of-Intent (PoI) token binding request parameters
    to prevent Man-in-the-Middle (MITM) parameter tampering.
    """
    payload = f"{request_id}:{request.agent_id}:{request.user_id}:{request.recipient_id}:{request.amount:.2f}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"POI-{signature[:24]}"


class AegisPayFirewall:
    """
    The Central Orchestrator for the AegisPay-AI Security Mesh.
    Evaluates Agent requests through Authorization, Policy, Threat Detection, and Risk engines.
    """

    def evaluate(self, request: PaymentRequest) -> FirewallEvaluation:
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())

        # Stage 1: Authorization (RBAC)
        auth_status = check_authorization(request)

        # Stage 2: Financial Policy Engine
        policy_status, policy_reasons = check_policy(request)

        # Stage 3: Threat Detection (Injection, Entropy, Intent Divergence)
        threat_status, threat_score, threat_reasons = check_threat(request)

        # Stage 4: Composite Multi-Signal Risk Engine
        decision, composite_risk, reasons = calculate_risk(
            auth_status=auth_status,
            policy_status=policy_status,
            policy_reasons=policy_reasons,
            threat_status=threat_status,
            threat_score=threat_score,
            threat_reasons=threat_reasons,
        )

        # Stage 5: Cryptographic Proof-of-Intent (PoI) Token generation if ALLOWED
        poi_token = generate_poi_token(request_id, request) if decision == Decision.ALLOW else None

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

        return FirewallEvaluation(
            request_id=request_id,
            decision=decision,
            risk_score=composite_risk,
            latency_ms=elapsed_ms,
            authorization_status=auth_status,
            policy_status=policy_status,
            threat_status=threat_status,
            reasons=reasons,
            proof_of_intent_token=poi_token,
        )


# Backward compatibility alias
RazorGuardFirewall = AegisPayFirewall
