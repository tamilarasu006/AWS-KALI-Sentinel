from typing import List, Dict, Any, Optional
from OpenDEMON.kali.intelligence.models import Plan, PlanStep

class TaskDecomposer:
    """
    Simulates breaking down a high-level task into actionable PlanSteps.
    In a full production KALI system, this calls an LLM to generate the JSON graph.
    For this implementation, we will allow injecting pre-computed plans or 
    provide basic decomposition heuristics if needed.
    """
    
    def parse_plan(self, goal: str, raw_plan_data: List[Dict[str, Any]]) -> Plan:
        """Parses a structured JSON list into a Plan object."""
        steps = []
        for step_data in raw_plan_data:
            step = PlanStep(
                id=step_data["id"],
                description=step_data["description"],
                dependencies=step_data.get("dependencies", []),
                assigned_agent=step_data["assigned_agent"],
                required_capabilities=step_data.get("required_capabilities", []),
                required_tools=step_data.get("required_tools", []),
                expected_outputs=step_data.get("expected_outputs", []),
                verification_criteria=step_data.get("verification_criteria", "Output exists.")
            )
            steps.append(step)
            
        return Plan(goal=goal, steps=steps)
        

class Planner:
    """
    The orchestrator that generates and validates Plans.
    Critically, the Planner never executes tools itself. It purely plans.
    """
    def __init__(self):
        self.decomposer = TaskDecomposer()
        
    def create_plan_from_json(self, goal: str, json_data: List[Dict[str, Any]]) -> Plan:
        """
        Creates a structured plan from JSON.
        Validates the DAG (Directed Acyclic Graph) of dependencies.
        """
        plan = self.decomposer.parse_plan(goal, json_data)
        
        # Validate dependencies exist
        step_ids = {s.id for s in plan.steps}
        for step in plan.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    raise ValueError(f"Step '{step.id}' depends on non-existent step '{dep}'")
                    
        return plan
