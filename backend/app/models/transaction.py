from pydantic import BaseModel, Field
from typing import Optional


class PaymentRequest(BaseModel):
    agent_id: str
    user_id: str
    tool_name: str
    amount: float = Field(gt=0)
    currency: str = "INR"
    recipient_id: str
    reason: str
    user_prompt: Optional[str] = None
