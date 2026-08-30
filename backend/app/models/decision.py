import time
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Decision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class FirewallEvaluation(BaseModel):
    request_id: str
    decision: Decision
    risk_score: float
    latency_ms: float
    authorization_status: CheckStatus
    policy_status: CheckStatus
    threat_status: CheckStatus
    reasons: List[str]
    timestamp: float = Field(default_factory=time.time)
    proof_of_intent_token: Optional[str] = None
