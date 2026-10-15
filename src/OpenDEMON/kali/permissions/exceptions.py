class PermissionError(Exception):
    """Base exception for permission issues."""
    pass

class PermissionDeniedError(PermissionError):
    """Raised when an action is explicitly denied by policy."""
    pass

class ApprovalRequiredError(PermissionError):
    """Raised when an action requires human approval before proceeding."""
    def __init__(self, approval_id: str, message: str):
        super().__init__(message)
        self.approval_id = approval_id

class AuthorizationError(PermissionError):
    """Raised when a tool is executed outside its authorized scope."""
    pass
