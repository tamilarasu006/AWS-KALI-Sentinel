from OpenDEMON.kali.agents.models import AgentResult
from OpenDEMON.kali.intelligence.models import PlanStep
from OpenDEMON.kali.intelligence.correction.models import VerificationResult

class Verifier:
    """Verifies if an agent's execution met the step's criteria."""
    
    def verify(self, result: AgentResult, step: PlanStep) -> VerificationResult:
        """
        In a full LLM system, this would prompt a Critic model.
        Here we use heuristic stubs for the system architecture.
        """
        if not result.success:
            return VerificationResult(
                passed=False,
                feedback=f"Execution failed natively: {result.error}"
            )
            
        # Basic heuristic string matching
        criteria = step.verification_criteria.lower()
        if "must contain" in criteria:
            expected = criteria.split("must contain")[-1].strip().strip("'\"")
            if expected not in result.output.lower():
                return VerificationResult(
                    passed=False,
                    feedback=f"Output did not contain required element: '{expected}'"
                )
                
        return VerificationResult(passed=True)

class Critic:
    """Analyzes output for logic errors, incompleteness, etc."""
    pass # Hook for future LLM integration
