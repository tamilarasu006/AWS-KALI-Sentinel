from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import logging

class RoutingDiagnostics(BaseModel):
    requested_model: str
    selected_model: Optional[str]
    selected_engine: Optional[str]
    reason: str
    fallback_used: bool

class EngineSpec(BaseModel):
    id: str
    type: str # 'kali', 'openai', 'ollama', etc.
    models: List[str]
    max_context: int
    available: bool = True
    cost_tier: str = "medium"

class KALIModelRouter:
    """
    Intelligent router for KALI variants and external models.
    Enforces strict guarantees that KALI is never silently replaced.
    """
    def __init__(self, engines: List[EngineSpec]):
        self.engines = engines
        self.logger = logging.getLogger("KALIModelRouter")

    def _find_capable_engine(self, model_name: str, context_size: int, require_availability: bool = True) -> Optional[EngineSpec]:
        """Finds an engine that supports the model and context size."""
        for engine in self.engines:
            if model_name in engine.models:
                if engine.max_context >= context_size:
                    if not require_availability or engine.available:
                        return engine
        return None

    def route(
        self, 
        requested_model: str, 
        context_size: int, 
        task_type: str = "general",
        allow_fallback: bool = False
    ) -> tuple[Optional[EngineSpec], RoutingDiagnostics]:
        
        # 1. Attempt to resolve exactly what was requested
        primary_engine = self._find_capable_engine(requested_model, context_size)
        
        if primary_engine:
            diagnostics = RoutingDiagnostics(
                requested_model=requested_model,
                selected_model=requested_model,
                selected_engine=primary_engine.id,
                reason="Primary model available and capable.",
                fallback_used=False
            )
            return primary_engine, diagnostics
            
        # 2. Handle failure. Determine WHY it failed for diagnostics.
        offline_engine = self._find_capable_engine(requested_model, context_size, require_availability=False)
        if offline_engine:
            base_reason = f"Model '{requested_model}' is available on engine '{offline_engine.id}' but it is currently offline."
        else:
            # Maybe context size exceeded
            context_engine = self._find_capable_engine(requested_model, 0, require_availability=False)
            if context_engine:
                base_reason = f"Model '{requested_model}' supports max {context_engine.max_context} context, but {context_size} requested."
            else:
                base_reason = f"Model '{requested_model}' is completely unknown."

        # 3. KALI Guarantee: Never silently replace KALI
        is_kali_request = requested_model.startswith("kali")
        
        if is_kali_request and not allow_fallback:
            diagnostics = RoutingDiagnostics(
                requested_model=requested_model,
                selected_model=None,
                selected_engine=None,
                reason=f"{base_reason} SILENT FALLBACK STRICTLY FORBIDDEN FOR KALI.",
                fallback_used=False
            )
            return None, diagnostics
            
        # 4. Handle explicit fallback if allowed (e.g. user permitted kali -> kali-mini)
        if allow_fallback:
            # Determine a suitable fallback based on task type or family
            fallback_model = "kali-mini" if is_kali_request else "gpt-3.5-turbo"
            fallback_engine = self._find_capable_engine(fallback_model, context_size)
            
            if fallback_engine:
                diagnostics = RoutingDiagnostics(
                    requested_model=requested_model,
                    selected_model=fallback_model,
                    selected_engine=fallback_engine.id,
                    reason=f"{base_reason} Fallback allowed and resolved to '{fallback_model}'.",
                    fallback_used=True
                )
                return fallback_engine, diagnostics
                
        # 5. Total failure
        diagnostics = RoutingDiagnostics(
            requested_model=requested_model,
            selected_model=None,
            selected_engine=None,
            reason=f"{base_reason} No suitable fallback available.",
            fallback_used=False
        )
        return None, diagnostics
