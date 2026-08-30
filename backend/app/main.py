import time
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.models.decision import Decision, FirewallEvaluation
from app.models.transaction import PaymentRequest
from app.firewall.firewall import AegisPayFirewall
from app.tools.payment_tool import RazorpayPaymentTool, PaymentExecutionResult
from app.audit.audit_logger import audit_logger, AuditRecord
from app.agent.agent import ShoppingAgent, AgentExecutionResponse

# Core singletons
firewall = AegisPayFirewall()
payment_tool = RazorpayPaymentTool()
agent = ShoppingAgent(firewall=firewall, payment_tool=payment_tool)
start_timestamp = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Server Warm-up on boot:
    Pre-warms Python regex automata, JIT caches, and HMAC routines
    so the very first user transaction has sub-0.05ms latency.
    """
    warmup_req = PaymentRequest(
        agent_id="shopping-agent-01",
        user_id="warmup-user",
        tool_name="create_payment",
        amount=1000.0,
        currency="INR",
        recipient_id="amazon-001",
        reason="Warmup routine on boot",
        user_prompt="Warmup",
    )
    for _ in range(5):
        firewall.evaluate(warmup_req)
    yield


# Initialize FastAPI application with Lifespan Warmup
app = FastAPI(
    title="AegisPay-AI Agent Firewall API",
    description="Zero-Trust In-Flight Security Mesh & Proof-of-Intent Gatekeeper for Autonomous AI Agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend dashboard communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PayResponse(BaseModel):
    evaluation: FirewallEvaluation
    execution: PaymentExecutionResult
    audit_record_id: str


class AgentChatRequest(BaseModel):
    prompt: str
    user_id: str = "user-101"


@app.get("/api/v1/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """Returns the operational status, version, and uptime of AegisPay."""
    return {
        "status": "HEALTHY",
        "service": "AegisPay-AI Agent Firewall",
        "version": "1.0.0",
        "architecture": "Deterministic In-Flight Mesh (Zero-RAG, Sub-1ms)",
        "uptime_seconds": round(time.time() - start_timestamp, 2),
        "engines": {
            "authorization": "ACTIVE",
            "policy": "ACTIVE",
            "threat_detection": "ACTIVE",
            "risk_engine": "ACTIVE",
            "audit_logger": "ACTIVE",
            "ai_agent": "ACTIVE",
        },
    }


@app.post("/api/v1/firewall/evaluate", response_model=FirewallEvaluation, tags=["Firewall"])
async def evaluate_transaction(request: PaymentRequest) -> FirewallEvaluation:
    """Evaluates an AI Agent's payment request through the multi-stage AegisPay Firewall."""
    return firewall.evaluate(request)


@app.post("/api/v1/firewall/pay", response_model=PayResponse, tags=["Firewall"])
async def execute_gated_payment(request: PaymentRequest) -> PayResponse:
    """Complete in-flight payment execution route gated by Proof-of-Intent."""
    evaluation = firewall.evaluate(request)
    execution = payment_tool.execute_payment(request, evaluation)
    record = audit_logger.log(request, evaluation, execution_status=execution.status)

    return PayResponse(
        evaluation=evaluation,
        execution=execution,
        audit_record_id=record.record_id,
    )


@app.post("/api/v1/agent/chat", response_model=AgentExecutionResponse, tags=["AI Agent"])
async def agent_chat(chat: AgentChatRequest) -> AgentExecutionResponse:
    """Takes a natural language user prompt, has the AI Agent formulate tool calls, and routes through AegisPay."""
    return agent.process_user_request(chat.prompt, user_id=chat.user_id)


@app.get("/api/v1/audit/records", response_model=List[AuditRecord], tags=["Audit & Forensics"])
async def get_audit_records() -> List[AuditRecord]:
    """Retrieves all signed audit ledger records and regulatory SAR forensic packets."""
    return audit_logger.get_records()


@app.get("/api/v1/metrics", tags=["System"])
async def get_metrics() -> Dict[str, Any]:
    """Calculates live firewall security benchmarks."""
    records = audit_logger.get_records()
    total = len(records)
    if total == 0:
        return {
            "total_transactions": 0,
            "allowed_count": 0,
            "reviewed_count": 0,
            "blocked_count": 0,
            "mean_latency_ms": 0.0,
            "threat_interception_rate": "100%",
        }

    allowed = sum(1 for r in records if r.decision == Decision.ALLOW)
    reviewed = sum(1 for r in records if r.decision == Decision.REVIEW)
    blocked = sum(1 for r in records if r.decision == Decision.BLOCK)
    avg_latency = round(sum(r.latency_ms for r in records) / total, 3)

    return {
        "total_transactions": total,
        "allowed_count": allowed,
        "reviewed_count": reviewed,
        "blocked_count": blocked,
        "mean_latency_ms": avg_latency,
        "threat_interception_rate": f"{(blocked / max(1, blocked + reviewed)) * 100:.1f}%",
    }
