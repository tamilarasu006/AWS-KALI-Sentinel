# KALI Model Router (STEP 30)

## Overview
The `KALIModelRouter` acts as an intelligent dispatch layer between KALI's core intelligence system and the actual inference engines (e.g., local KALI weights, cloud models, or third-party engines). It evaluates the requested model against the available `EngineSpec` configurations, validating context limits and availability.

## Strict KALI Guarantee
One of the most critical security guarantees of the router is: **Never silently replace KALI.** 
If a user or an internal agent specifically requests the `"kali"` model, and the local KALI engine is either offline, unavailable, or the context limits are exceeded, the router will **hard fail** rather than silently falling back to a model like `gpt-4` or `llama`. 

This guarantees that security-critical operations are deterministically executed by the known KALI model, preventing scenarios where a third-party model accidentally bypasses or misinterprets strict sandbox constraints.

## Fallback Logic
If `allow_fallback=True` is explicitly passed (e.g., during non-critical chat tasks), the router is permitted to downgrade `"kali"` to `"kali-mini"`, or fallback to other model families. However, whenever a fallback is used, the `RoutingDiagnostics` object will explicitly flag `fallback_used = True` and document the exact reason for the fallback, preserving the audit trail.

## Integration
The router evaluates factors such as:
- `task_type` (for potential capability matching)
- `context_size` (to prevent sending 30k tokens to an 8k limit engine)
- `available` (health checks on inference engines)
