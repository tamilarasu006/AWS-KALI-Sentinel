from typing import Dict, List, Set
from .errors import CircularDependencyError

class TaskDAGNode:
    """Represents a node in the Task DAG for dependency resolution."""
    def __init__(self, task_id: str, dependencies: List[str]):
        self.task_id = task_id
        self.dependencies = dependencies

class TaskValidator:
    @staticmethod
    def check_circular_dependencies(tasks: Dict[str, TaskDAGNode]) -> None:
        """
        Validates a dictionary of TaskDAGNodes to ensure no circular dependencies exist.
        Uses depth-first search (DFS) with a visited set and recursion stack.
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = tasks.get(node_id)
            if node:
                for dep in node.dependencies:
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        return True

            rec_stack.remove(node_id)
            return False

        for task_id in tasks:
            if task_id not in visited:
                if dfs(task_id):
                    raise CircularDependencyError(f"Circular dependency detected starting from task: {task_id}")
