import re
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.models.decision import Decision, FirewallEvaluation
from app.models.transaction import PaymentRequest
from app.firewall.firewall import RazorGuardFirewall
from app.tools.payment_tool import RazorpayPaymentTool, PaymentExecutionResult
from app.audit.audit_logger import audit_logger


class AgentExecutionResponse(BaseModel):
    agent_id: str
    user_prompt: str
    tool_call: Optional[Dict[str, Any]] = None
    firewall_decision: str
    risk_score: float
    order_id: Optional[str] = None
    status: str
    response_to_user: str
    latency_ms: float


class ShoppingAgent:
    """
    Autonomous AI Shopping Agent capable of parsing human natural language intents,
    formulating structured tool calls, and interacting with payment tools via RazorGuard.
    """

    def __init__(
        self,
        agent_id: str = "shopping-agent-01",
        firewall: Optional[RazorGuardFirewall] = None,
        payment_tool: Optional[RazorpayPaymentTool] = None,
    ):
        self.agent_id = agent_id
        self.firewall = firewall or RazorGuardFirewall()
        self.payment_tool = payment_tool or RazorpayPaymentTool()

    def parse_intent(self, user_prompt: str, user_id: str = "user-101") -> PaymentRequest:
        """
        Parses human prompt into a structured tool-call payload (PaymentRequest).
        In a full LLM deployment, this uses OpenAI/Gemini structured function calling.
        """
        prompt = user_prompt.strip()

        # Extract amount
        numbers = re.findall(r"[\d,]+(?:\.\d+)?", prompt)
        amount = 1500.0  # default baseline
        if numbers:
            try:
                amount = float(numbers[0].replace(",", ""))
            except ValueError:
                pass

        # Extract recipient
        recipient = "amazon-001"
        if "flipkart" in prompt.lower():
            recipient = "flipkart-001"
        elif "nike" in prompt.lower():
            recipient = "nike-official"
        elif "attacker" in prompt.lower() or "darkweb" in prompt.lower():
            recipient = "attacker-vpa-01"

        return PaymentRequest(
            agent_id=self.agent_id,
            user_id=user_id,
            tool_name="create_payment",
            amount=amount,
            currency="INR",
            recipient_id=recipient,
            reason=f"Agent executing user request: '{prompt}'",
            user_prompt=prompt,
        )

    def process_user_request(self, user_prompt: str, user_id: str = "user-101") -> AgentExecutionResponse:
        """
        End-to-end agent decision loop:
        1. Parse natural language intent into structured tool call.
        2. Submit to RazorGuard Firewall.
        3. Execute or halt tool based on Firewall decision.
        4. Synthesize friendly human response.
        """
        start_time = time.perf_counter()

        # 1. Intent Formulation
        request = self.parse_intent(user_prompt, user_id=user_id)

        # 2. Intercept via RazorGuard
        evaluation = self.firewall.evaluate(request)

        # 3. Gated Tool Execution
        execution = self.payment_tool.execute_payment(request, evaluation)

        # 4. Audit Log
        audit_logger.log(request, evaluation, execution_status=execution.status)

        # 5. Formulate Agent Response
        if evaluation.decision == Decision.ALLOW and execution.success:
            user_msg = f"✅ Payment Successful! Razorpay Order ID: {execution.order_id}. Captured ₹{execution.amount_captured:.2f} to {execution.recipient_id}."
            final_status = "COMPLETED"
        elif evaluation.decision == Decision.REVIEW:
            user_msg = f"⚠️ Payment Held for Review (Risk Score: {evaluation.risk_score}). Reasons: {'; '.join(evaluation.reasons)}. Please confirm via 2FA."
            final_status = "HELD_IN_REVIEW"
        else:
            user_msg = f"⛔ Payment Blocked by RazorGuard Firewall (Risk Score: {evaluation.risk_score}). Policy/Threat Violation: {'; '.join(evaluation.reasons)}."
            final_status = "SECURITY_BLOCKED"

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

        return AgentExecutionResponse(
            agent_id=self.agent_id,
            user_prompt=user_prompt,
            tool_call={
                "tool": request.tool_name,
                "amount": request.amount,
                "recipient": request.recipient_id,
                "reason": request.reason,
            },
            firewall_decision=evaluation.decision.value,
            risk_score=evaluation.risk_score,
            order_id=execution.order_id,
            status=final_status,
            response_to_user=user_msg,
            latency_ms=elapsed_ms,
        )
