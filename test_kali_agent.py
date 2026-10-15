import asyncio
from OpenDEMON.core.config import load_config
from OpenDEMON.engine import get_engine
from OpenDEMON.agents.kali_agent import KALIAgent

async def main():
    config = load_config()
    
    # We will try to get a dummy engine or whatever is configured locally.
    # Note: KALI Planner generates JSON, so it requires an engine that can respond.
    # If there is no local engine, we might hit an error, but let's try.
    print("Loading engine...")
    res = get_engine(config, None, model=None)
    if not res:
        print("No engine available for testing. Mocking engine.")
        class MockEngine:
            def generate(self, messages, **kwargs):
                return {
                    "content": "```json\n{\n  \"plan\": [\n    {\n      \"step_name\": \"Test capability\",\n      \"capability\": \"WEB_SEARCH\",\n      \"tool\": \"auth_recon\",\n      \"inputs\": {\"target\": \"example.com\"}\n    }\n  ]\n}\n```"
                }
        engine_name = "mock"
        engine = MockEngine()
        model_name = "mock_model"
    else:
        engine_name, engine = res
        model_name = config.intelligence.default_model

    print(f"Instantiating KALIAgent with {engine_name}...")
    agent = KALIAgent(engine=engine, model=model_name)
    
    print("Running KALI agent on prompt 'Scan example.com for vulnerabilities'...")
    try:
        # Note: auth_recon requires authorization scope usually, but let's see how it behaves.
        result = await agent.run_async("Scan example.com for vulnerabilities")
        print("\n=== Result Content ===")
        print(result.content)
        print("\n=== Tool Results ===")
        for tr in result.tool_results:
            print(f"Tool: {tr.tool_name}, Args: {tr.arguments}, Output: {tr.output}")
    except Exception as e:
        print(f"Execution Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
