from enum import Enum
from typing import Optional
from pydantic import BaseModel

class FailureClassification(str, Enum):
    SYNTAX_ERROR = "SYNTAX_ERROR"
    LOGIC_ERROR = "LOGIC_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    UNKNOWN = "UNKNOWN"

class VerificationResult(BaseModel):
    passed: bool
    feedback: str = ""
    is_partial: bool = False

class Diagnosis(BaseModel):
    classification: FailureClassification
    root_cause: str
    can_retry: bool

class RepairPlan(BaseModel):
    modified_prompt: str
    risk_increased: bool = False
    target_changed: bool = False
    tool_changed: bool = False
    
class RetryPolicy(BaseModel):
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
