import os
import shutil
from pathlib import Path
from typing import Optional

from OpenDEMON.kali.workspace.models import Workspace

class WorkspaceManager:
    """
    Manages isolated physical directories for projects.
    Strictly prevents path traversal and enforces tenant boundaries.
    """
    def __init__(self, base_dir: str = "~/.opendemon/workspaces"):
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_secure_path(self, user_id: str, project_id: str) -> Path:
        """Generates a secure, non-traversable path for a workspace."""
        # Sanitize IDs to prevent traversal
        safe_user = "".join(c for c in user_id if c.isalnum() or c in "-_")
        safe_project = "".join(c for c in project_id if c.isalnum() or c in "-_")
        
        target = (self.base_dir / safe_user / safe_project).resolve()
        
        # Verify it remains under base_dir (protection against symlink/traversal tricks)
        if not str(target).startswith(str(self.base_dir)):
            raise PermissionError("Path traversal detected.")
            
        return target
        
    def create_workspace(self, user_id: str, project_id: str) -> Workspace:
        path = self._get_secure_path(user_id, project_id)
        path.mkdir(parents=True, exist_ok=True)
        
        return Workspace(
            project_id=project_id,
            user_id=user_id,
            root_path=str(path)
        )
        
    def get_workspace(self, user_id: str, project_id: str) -> Optional[Workspace]:
        path = self._get_secure_path(user_id, project_id)
        if not path.exists():
            return None
            
        return Workspace(
            project_id=project_id,
            user_id=user_id,
            root_path=str(path)
        )
        
    def delete_workspace(self, user_id: str, project_id: str) -> bool:
        path = self._get_secure_path(user_id, project_id)
        if path.exists():
            shutil.rmtree(path)
            return True
        return False
