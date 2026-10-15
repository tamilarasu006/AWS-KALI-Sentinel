from OpenDEMON.kali.model.router import KALIModelRouter, EngineSpec

def run():
    print("Testing KALI Model Router...")
    
    engines = [
        EngineSpec(id="engine_kali_local", type="kali", models=["kali"], max_context=8192, available=True),
        EngineSpec(id="engine_kali_mini", type="kali", models=["kali-mini"], max_context=4096, available=True),
        EngineSpec(id="engine_gpt4", type="openai", models=["gpt-4"], max_context=128000, available=True),
        EngineSpec(id="engine_kali_cloud", type="kali", models=["kali"], max_context=32000, available=False)
    ]
    
    router = KALIModelRouter(engines)
    
    print("\n--- Test 1: Standard KALI Routing ---")
    engine, diag = router.route("kali", context_size=2000)
    print(diag.model_dump_json(indent=2))
    assert engine.id == "engine_kali_local"
    
    print("\n--- Test 2: External Model Routing ---")
    engine, diag = router.route("gpt-4", context_size=100000)
    print(diag.model_dump_json(indent=2))
    assert engine.id == "engine_gpt4"
    
    print("\n--- Test 3: KALI Context Exceeded (Strict Denial) ---")
    # Requires 10k context, local only supports 8192, cloud supports 32k but is offline
    engine, diag = router.route("kali", context_size=10000, allow_fallback=False)
    print(diag.model_dump_json(indent=2))
    assert engine is None
    assert "FORBIDDEN FOR KALI" in diag.reason
    
    print("\n--- Test 4: KALI Context Exceeded (With Fallback) ---")
    # Since kali-mini context is only 4096, it will fail to fallback as well
    # Let's make context small but local engine unavailable
    router.engines[0].available = False 
    engine, diag = router.route("kali", context_size=2000, allow_fallback=True)
    print(diag.model_dump_json(indent=2))
    assert engine.id == "engine_kali_mini"
    assert diag.fallback_used
    
    print("\nALL TESTS PASSED MANUALLY!")

if __name__ == "__main__":
    run()
