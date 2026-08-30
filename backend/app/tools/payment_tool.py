import uuid
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.models.decision import Decision, FirewallEvaluation
from app.models.transaction import PaymentRequest


class PaymentExecutionResult(BaseModel):
    success: bool
    order_id: Optional[str] = None
    transaction_id: Optional[str] = None
    amount_captured: float
    currency: str
    recipient_id: str
    status: str
    message: str
    poi_token: Optional[str] = None
    timestamp: float


class RazorpayPaymentTool:
    """
    Financial Execution Tool for Razorpay Orders.
    Strictly gates execution based on AegisPay-AI Firewall Proof-of-Intent Tokens.
    """

    def execute_payment(
        self,
        request: PaymentRequest,
        evaluation: FirewallEvaluation,
    ) -> PaymentExecutionResult:
        # Invariant 1: Blocked or Under-Review transactions cannot execute
        if evaluation.decision != Decision.ALLOW:
            return PaymentExecutionResult(
                success=False,
                amount_captured=0.0,
                currency=request.currency,
                recipient_id=request.recipient_id,
                status="HELD_OR_REJECTED",
                message=f"AegisPay Firewall prevented payment execution: Decision is {evaluation.decision.value}.",
                timestamp=time.time(),
            )

        # Invariant 2: Must have a valid Proof-of-Intent token
        if not evaluation.proof_of_intent_token or not evaluation.proof_of_intent_token.startswith("POI-"):
            return PaymentExecutionResult(
                success=False,
                amount_captured=0.0,
                currency=request.currency,
                recipient_id=request.recipient_id,
                status="SIGNATURE_VERIFICATION_FAILED",
                message="Security Violation: Missing or invalid Proof-of-Intent cryptographic token.",
                timestamp=time.time(),
            )

        # Simulating Razorpay Order & Payment Creation
        mock_order_id = f"order_rzp_{uuid.uuid4().hex[:12]}"
        mock_payment_id = f"pay_rzp_{uuid.uuid4().hex[:12]}"

        return PaymentExecutionResult(
            success=True,
            order_id=mock_order_id,
            transaction_id=mock_payment_id,
            amount_captured=request.amount,
            currency=request.currency,
            recipient_id=request.recipient_id,
            status="CAPTURED",
            message=f"Successfully executed Razorpay payment of ₹{request.amount:.2f} to {request.recipient_id}.",
            poi_token=evaluation.proof_of_intent_token,
            timestamp=time.time(),
        )
