from OpenDEMON.kali.intelligence.models import PlanStep
from OpenDEMON.kali.intelligence.correction.models import Diagnosis, RepairPlan

class RepairPlanner:
    """Generates modifications to prompts/parameters to fix issues."""
    
    def create_repair_plan(self, step: PlanStep, original_prompt: str, diagnosis: Diagnosis) -> RepairPlan:
        """
        Creates a new prompt guiding the agent to fix the mistake.
        Crucially tracks if the risk profile changes.
        """
        # If an LLM were used, it might decide to change tools or targets here.
        # We simulate a simple prompt augment.
        new_prompt = original_prompt + f"\n\n[SYSTEM FEEDBACK]: Previous attempt failed. {diagnosis.root_cause}. Please correct this."
        
        # In a real system, we analyze if the new prompt attempts to hit a new IP or use a new tool.
        # For our architecture demo, we assume the target/tool didn't change unless explicitly flagged.
        return RepairPlan(
            modified_prompt=new_prompt,
            risk_increased=False,
            target_changed=False,
            tool_changed=False
        )
