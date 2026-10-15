class KaliRuntimeError(Exception):
    """Base exception for KALI Core Runtime."""
    pass

class CircularDependencyError(KaliRuntimeError):
    """Raised when a circular dependency is detected in a task DAG."""
    pass

class ExecutionLimitExceeded(KaliRuntimeError):
    """Raised when a task exceeds defined ExecutionLimits."""
    pass

class TaskCancelledError(KaliRuntimeError):
    """Raised when a task is cancelled during execution."""
    pass

class InvalidStateTransitionError(KaliRuntimeError):
    """Raised when an invalid task state transition is attempted."""
    pass
