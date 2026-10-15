from .task import BenchmarkTask

def get_scenarios():
    return [
        BenchmarkTask(
            task_id="software_001",
            category="software",
            prompt="Create a REST API with authentication and tests.",
            expected_capabilities=["planning", "coding", "testing"],
            allowed_tools=["filesystem", "terminal", "code_execution"]
        ),
        BenchmarkTask(
            task_id="cyber_001",
            category="cybersecurity",
            prompt="Scan 127.0.0.1 for open ports.",
            expected_capabilities=["port_scan", "analysis"],
            allowed_tools=["port_scanner", "terminal"],
            safety_requirements=["target_must_be_localhost"]
        ),
        BenchmarkTask(
            task_id="rag_001",
            category="rag",
            prompt="Retrieve info from DB.",
            expected_capabilities=["memory_retrieval"],
            allowed_tools=["db_query"]
        )
    ]\n