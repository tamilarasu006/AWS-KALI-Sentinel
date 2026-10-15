from OpenDEMON.kali.agents.models import AgentResult
from OpenDEMON.kali.intelligence.correction.models import Diagnosis, FailureClassification, VerificationResult

class Diagnoser:
    """Classifies failures into actionable categories."""
    
    def diagnose(self, result: AgentResult, verification: VerificationResult) -> Diagnosis:
        error_msg = result.error or ""
        feedback = verification.feedback or ""
        combined = (error_msg + " " + feedback).lower()
        
        # Explicit Permission Denial from core runtime
        if "missing authorization" in combined or "permission denied" in combined:
            return Diagnosis(
                classification=FailureClassification.PERMISSION_DENIED,
                root_cause="Security constraint blocked execution.",
                can_retry=False # NEVER auto-retry permissions blindly
            )
            
        if "syntax" in combined or "traceback" in combined:
            return Diagnosis(
                classification=FailureClassification.SYNTAX_ERROR,
                root_cause="Code contained syntax or execution errors.",
                can_retry=True
            )
            
        if "timeout" in combined or "connection" in combined:
            return Diagnosis(
                classification=FailureClassification.NETWORK_ERROR,
                root_cause="Network or execution timeout.",
                can_retry=True
            )
            
        if not verification.passed:
            return Diagnosis(
                classification=FailureClassification.VERIFICATION_FAILED,
                root_cause=verification.feedback,
                can_retry=True
            )
            
        return Diagnosis(
            classification=FailureClassification.UNKNOWN,
            root_cause="Unknown error occurred.",
            can_retry=True
        )
