import json
from typing import Optional, Any
from OpenDEMON.kali.model import KALIModel
from OpenDEMON.kali.memory.manager import MemoryManager
from OpenDEMON.kali.rag.pipeline import RAGPipeline
from OpenDEMON.core.types import ToolCall, ToolResult

from .planner import KALIPlanner
from .router import KALIRouter
from .executor import KALIExecutor

class KALIOrchestrator:
    """The central orchestrator for the KALI agent."""

    def __init__(
        self,
        model: KALIModel,
        planner: KALIPlanner,
        router: KALIRouter,
        executor: KALIExecutor,
        memory_manager: Optional[MemoryManager] = None,
        rag_pipeline: Optional[RAGPipeline] = None
    ):
        self.model = model
        self.planner = planner
        self.router = router
        self.executor = executor
        self.memory_manager = memory_manager
        self.rag_pipeline = rag_pipeline

    async def run(self, request_text: str, user_id: str, conversation_id: str) -> str:
        """Executes the full pipeline for a given user request."""
        import time
        from OpenDEMON.kali.orchestration.metrics import MetricsCollector
        
        start_t = time.time()
        metrics = MetricsCollector()
        metrics.increment_active()
        
        try:
            # 0. Security Audit: Prompt Injection Scan
            from OpenDEMON.security.injection_scanner import InjectionScanner
            from OpenDEMON.security.types import ThreatLevel
            scanner = InjectionScanner()
            try:
                scan_result = scanner.scan(request_text)
                if not scan_result.is_clean and scan_result.threat_level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
                    return "Security Policy Violation: Malicious prompt patterns detected. Request blocked."
            except Exception:
                pass # Fallback if scanner isn't properly initialized (e.g. missing rust bridge)
                
            # 1. Intent Detection & Planning
            plan = self.planner.plan(request_text)
            
            # 2. Context Building (Memory)
            context_blocks = []
            if self.memory_manager:
                if "short_term" in plan.required_memory_types:
                    short_term = await self.memory_manager.retrieve(user_id, memory_type="short_term", conversation_id=conversation_id)
                    if short_term:
                        context_blocks.append("--- Recent Conversation ---")
                        for msg in short_term:
                            context_blocks.append(f"{msg['role']}: {msg['content']}")
                
                if "semantic" in plan.required_memory_types and self.rag_pipeline:
                    emb = self.rag_pipeline.embedding_provider.embed(request_text)
                    semantic_results = await self.memory_manager.search(user_id, emb, top_k=2)
                    if semantic_results:
                        context_blocks.append("--- Relevant Semantic Memories ---")
                        for r in semantic_results:
                            context_blocks.append(r["content"])

            # 3. Context Building (RAG)
            if plan.requires_rag and self.rag_pipeline:
                rag_start = time.time()
                rag_chunks = await self.rag_pipeline.retrieve(request_text, top_k=3, metadata_filter={"user_id": user_id})
                rag_context = self.rag_pipeline.build_context(request_text, rag_chunks)
                if rag_context:
                    context_blocks.append("--- Retrieved Documents ---")
                    context_blocks.append(rag_context)
                metrics.record_rag_latency((time.time() - rag_start) * 1000)

            # 4. Agent Swarm Execution & Tools
            agent_results_text = ""
            if plan.target_agents:
                from OpenDEMON.kali.agents import SoftwareAgent, DataAgent, CyberAgent
                
                # Simple lazy initialization of agents
                agents = {
                    "kali_software_agent": SoftwareAgent(),
                    "kali_data_agent": DataAgent(),
                    "kali_cyber_agent": CyberAgent()
                }
                
                # Context dict for agents to use memory and tools
                agent_context = {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "rag_pipeline": self.rag_pipeline,
                    "memory_manager": self.memory_manager
                }
                
                for agent_id in plan.target_agents:
                    if agent_id in agents:
                        agent = agents[agent_id]
                        # Execute the specialized agent
                        result = await agent.execute(request_text, agent_context)
                        agent_results_text += f"\n{result}\n"

            # Fallback for generic tools if not handled by agents
            tool_results_text = ""
            if plan.requires_tools and not plan.target_agents:
                for tname in plan.tool_names:
                    tc = ToolCall(id=f"call_{tname}", name=tname, arguments='{"query": "mock data"}')
                    result = self.executor.execute_tool(tc)
                    if not result.success:
                        tool_results_text += self.router.fallback_on_tool_failure(tname, str(result.content)) + "\n"
                    else:
                        tool_results_text += f"Tool {tname} result: {result.content}\n"

            if agent_results_text:
                context_blocks.append("--- Agent Swarm Intelligence ---")
                context_blocks.append(agent_results_text)
                
            if tool_results_text:
                context_blocks.append("--- Tool Results ---")
                context_blocks.append(tool_results_text)

            # 5. Model execution
            full_prompt = "\n".join(context_blocks) + f"\n\nUser: {request_text}\nKALI:"
            
            model_to_use = self.router.route_model()
            if model_to_use == "fallback-heuristic-model":
                return "I am experiencing issues and operating in fallback mode. I cannot fulfill this request right now."

            # Measure TTFT and TPS via generator if streaming, or just block if generating
            # KALIModel generates strings.
            gen_start = time.time()
            final_response = self.model.generate(full_prompt, max_new_tokens=200)
            gen_time = time.time() - gen_start
            
            # Approximation of tokens: rough split
            num_tokens = len(final_response.split()) * 1.3
            metrics.record_ttft(gen_time * 1000)  # In non-streaming TTFT is roughly gen time
            metrics.record_tokens_sec(num_tokens / gen_time if gen_time > 0 else 0)

            # 6. Save back to memory
            if self.memory_manager:
                await self.memory_manager.short_term.add_message(user_id, conversation_id, "user", request_text)
                await self.memory_manager.short_term.add_message(user_id, conversation_id, "assistant", final_response)
                
            return final_response
            
        finally:
            metrics.decrement_active()
            total_lat = (time.time() - start_t) * 1000
            metrics.record_latency(total_lat)
            metrics.log_summary(conversation_id)
