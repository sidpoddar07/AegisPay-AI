import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.decision import Decision, FirewallEvaluation
from app.models.transaction import PaymentRequest


class ForensicReport(BaseModel):
    incident_id: str
    request_id: str
    agent_id: str
    user_id: str
    severity: str
    evidence_chain: List[str]
    remediation_actions: List[str]
    tamper_proof_hash: str
    created_at: float = Field(default_factory=time.time)


class AuditRecord(BaseModel):
    record_id: str
    request_id: str
    agent_id: str
    user_id: str
    amount: float
    currency: str
    recipient_id: str
    decision: Decision
    risk_score: float
    latency_ms: float
    reasons: List[str]
    integrity_hash: str
    timestamp: float
    forensic_report: Optional[ForensicReport] = None


class AuditLogger:
    """
    Append-only Tamper-Evident Audit Logger for RazorGuard.
    Signs every transaction event with SHA-256 and generates SARs for security events.
    """

    def __init__(self):
        self.records: List[AuditRecord] = []

    def compute_hash(self, data: Dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def log(
        self,
        request: PaymentRequest,
        evaluation: FirewallEvaluation,
        execution_status: str = "COMPLETED",
    ) -> AuditRecord:
        record_id = f"AUDIT-{len(self.records) + 1:05d}"
        
        # Determine Forensics if decision is REVIEW or BLOCK
        forensic_report = None
        if evaluation.decision in (Decision.BLOCK, Decision.REVIEW):
            severity = "CRITICAL" if evaluation.decision == Decision.BLOCK else "WARNING"
            remediations = []
            if evaluation.decision == Decision.BLOCK:
                remediations.append("Immediate: Agent API key suspended from payment tool invocation.")
                remediations.append(f"Blacklist Candidate: Recipient '{request.recipient_id}' forwarded to SOC fraud registry.")
            else:
                remediations.append("Action Required: Route to merchant operator for Step-Up biometric/OTP authorization.")

            sar_hash = self.compute_hash({
                "request_id": evaluation.request_id,
                "reasons": evaluation.reasons,
                "amount": request.amount,
                "recipient": request.recipient_id,
            })

            forensic_report = ForensicReport(
                incident_id=f"INC-{evaluation.request_id[:8].upper()}",
                request_id=evaluation.request_id,
                agent_id=request.agent_id,
                user_id=request.user_id,
                severity=severity,
                evidence_chain=evaluation.reasons,
                remediation_actions=remediations,
                tamper_proof_hash=sar_hash,
            )

        payload_to_hash = {
            "record_id": record_id,
            "request_id": evaluation.request_id,
            "agent_id": request.agent_id,
            "amount": request.amount,
            "recipient_id": request.recipient_id,
            "decision": evaluation.decision.value,
            "risk_score": evaluation.risk_score,
            "timestamp": evaluation.timestamp,
        }

        integrity_hash = self.compute_hash(payload_to_hash)

        record = AuditRecord(
            record_id=record_id,
            request_id=evaluation.request_id,
            agent_id=request.agent_id,
            user_id=request.user_id,
            amount=request.amount,
            currency=request.currency,
            recipient_id=request.recipient_id,
            decision=evaluation.decision,
            risk_score=evaluation.risk_score,
            latency_ms=evaluation.latency_ms,
            reasons=evaluation.reasons,
            integrity_hash=integrity_hash,
            timestamp=time.time(),
            forensic_report=forensic_report,
        )

        self.records.append(record)
        return record

    def get_records(self) -> List[AuditRecord]:
        return self.records


# Global singleton instance for app-wide audit logging
audit_logger = AuditLogger()
