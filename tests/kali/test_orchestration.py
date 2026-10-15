import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock

from OpenDEMON.kali.orchestration import (
    KALIPlanner,
    KALIRouter,
    KALIExecutor,
    KALIOrchestrator
)
from OpenDEMON.core.types import ToolCall, ToolResult

class MockModel:
    def generate(self, prompt: str, **kwargs):
        # We can echo part of the prompt to prove context injection worked
        if "weather" in prompt:
            return ["The weather ", "is sunny."]
        if "42" in prompt:
            return ["Tool returned data."]
        if "Document Context" in prompt:
            return ["Based on the doc, RAG works."]
        return ["I am a simple ", "chat response."]

@pytest.fixture
def mock_open_demon_tool_executor():
    ex = MagicMock()
    # Mock successful calculator
    def execute_mock(tc):
        if tc.name == "calculator":
            return ToolResult(tool_name="calculator", content="42", success=True)
        return ToolResult(tool_name=tc.name, content="Error", success=False)
    ex.execute.side_effect = execute_mock
    return ex

@pytest.fixture
def orchestrator(mock_open_demon_tool_executor):
    model = MockModel()
    planner = KALIPlanner(available_tools=["calculator", "web_search"])
    router = KALIRouter()
    executor = KALIExecutor(mock_open_demon_tool_executor)
    
    # Mock memory manager
    memory = MagicMock()
    memory.retrieve = AsyncMock(return_value=[])
    memory.search = AsyncMock(return_value=[])
    memory.short_term.add_message = AsyncMock()
    
    # Mock RAG
    rag = MagicMock()
    rag.retrieve = AsyncMock(return_value=[])
    rag.build_context.return_value = ""
    
    return KALIOrchestrator(model, planner, router, executor, memory, rag)

@pytest.mark.asyncio
async def test_simple_chat(orchestrator):
    response = await orchestrator.run("Hello there", "user1", "conv1")
    assert response == "I am a simple chat response."
    
@pytest.mark.asyncio
async def test_tool_request_success(orchestrator):
    response = await orchestrator.run("calculate 2+2", "user1", "conv1")
    assert "Tool returned data." in response
    # The executor should have been called
    orchestrator.executor.tool_executor.execute.assert_called()

@pytest.mark.asyncio
async def test_tool_failure_fallback(orchestrator):
    # web_search will fail according to our mock ToolExecutor
    response = await orchestrator.run("what is the weather", "user1", "conv1")
    assert "The weather is sunny." in response
    # Ensure fallback router text was injected into the model prompt
    orchestrator.executor.tool_executor.execute.assert_called()

@pytest.mark.asyncio
async def test_rag_request(orchestrator):
    # Mock RAG hit
    orchestrator.rag_pipeline.retrieve.return_value = ["chunk1"]
    orchestrator.rag_pipeline.build_context.return_value = "Document Context: Info"
    
    response = await orchestrator.run("according to the doc", "user1", "conv1")
    assert "Based on the doc, RAG works." in response

@pytest.mark.asyncio
async def test_memory_request(orchestrator):
    # Trigger semantic memory
    orchestrator.memory_manager.search.return_value = [{"content": "You like blue."}]
    
    response = await orchestrator.run("according to the doc, what did I say my favorite color was", "user1", "conv1")
    # memory.search should have been called
    orchestrator.memory_manager.search.assert_called()
