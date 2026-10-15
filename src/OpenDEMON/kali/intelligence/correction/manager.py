import asyncio
from typing import Optional, Callable, Awaitable
from OpenDEMON.kali.agents.models import AgentContext, AgentResult
from OpenDEMON.kali.intelligence.models import PlanStep
from OpenDEMON.kali.intelligence.correction.models import RetryPolicy, VerificationResult
from OpenDEMON.kali.intelligence.correction.verifier import Verifier
from OpenDEMON.kali.intelligence.correction.diagnoser import Diagnoser
from OpenDEMON.kali.intelligence.correction.repair import RepairPlanner

class RetryManager:
    """
    Orchestrates the Verify -> Diagnose -> Repair -> Retry loop.
    Enforces security constraints on retries.
    """
    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()
        self.verifier = Verifier()
        self.diagnoser = Diagnoser()
        self.repair_planner = RepairPlanner()
        
    async def execute_with_retry(
        self, 
        step: PlanStep, 
        initial_prompt: str, 
        context: AgentContext,
        agent_executor: Callable[[str, AgentContext], Awaitable[AgentResult]]
    ) -> AgentResult:
        
        current_prompt = initial_prompt
        attempts = 0
        last_result = None
        
        while attempts <= self.policy.max_retries:
            attempts += 1
            
            # Execute
            result = await agent_executor(current_prompt, context)
            last_result = result
            
            # Verify
            verification = self.verifier.verify(result, step)
            if verification.passed:
                return result
                
            # Diagnose
            diagnosis = self.diagnoser.diagnose(result, verification)
            
            # Security Hard-Stop
            if not diagnosis.can_retry:
                return AgentResult(
                    agent_id=result.agent_id,
                    success=False,
                    output=result.output,
                    error=f"Hard Stop: {diagnosis.root_cause} (Retries disabled for this classification)"
                )
                
            if attempts > self.policy.max_retries:
                break
                
            # Repair
            repair_plan = self.repair_planner.create_repair_plan(step, current_prompt, diagnosis)
            
            # Ensure repair didn't escalate permissions silently
            if repair_plan.risk_increased or repair_plan.target_changed or repair_plan.tool_changed:
                return AgentResult(
                    agent_id=result.agent_id,
                    success=False,
                    output=result.output,
                    error="Security Exception: Repair plan altered scope/risk. Requires new human approval."
                )
                
            current_prompt = repair_plan.modified_prompt
            
            # Wait before retry
            await asyncio.sleep(self.policy.retry_delay_seconds)
            
        # Max retries exhausted
        if last_result:
            last_result.success = False
            last_result.error = "Max retries exhausted. " + (last_result.error or "")
        return last_result
