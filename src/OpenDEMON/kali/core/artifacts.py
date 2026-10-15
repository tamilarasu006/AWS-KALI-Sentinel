import os
import uuid
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field

from OpenDEMON.kali.workspace.manager import WorkspaceManager

class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    project_id: str
    task_id: str
    name: str
    type: str
    reference: str  # The secure path relative to the workspace
    size: int = 0
    checksum: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ArtifactManager:
    """
    Manages the lifecycle, storage, and checksumming of artifacts.
    Integrates directly with WorkspaceManager for physical storage isolation.
    """
    def __init__(self, workspace_manager: WorkspaceManager):
        self.workspace_manager = workspace_manager
        # In memory DB for the demo implementation
        self._db: Dict[str, Artifact] = {}
        
    def _calculate_checksum(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def _guess_type(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        mapping = {
            ".py": "source", ".js": "source", ".ts": "source",
            ".png": "image", ".jpg": "image",
            ".csv": "dataset", ".json": "dataset",
            ".pdf": "document", ".docx": "document",
            ".txt": "log", ".md": "report"
        }
        return mapping.get(ext, "unknown")
        
    def create(self, user_id: str, project_id: str, task_id: str, name: str, content: bytes, metadata: dict = None) -> Artifact:
        """Creates an artifact, saving its contents into the secure workspace."""
        workspace = self.workspace_manager.get_workspace(user_id, project_id)
        if not workspace:
            workspace = self.workspace_manager.create_workspace(user_id, project_id)
            
        secure_ws_path = Path(workspace.root_path)
        
        # Ensure 'name' doesn't contain path traversals
        safe_name = Path(name).name
        
        # We can store inside a task_id subfolder to keep things organized
        task_dir = secure_ws_path / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        target_file = task_dir / safe_name
        
        # Write file
        target_file.write_bytes(content)
        
        # Analyze
        checksum = self._calculate_checksum(target_file)
        size = target_file.stat().st_size
        type_str = self._guess_type(safe_name)
        
        # Store relative reference
        reference = target_file.relative_to(secure_ws_path).as_posix()
        
        artifact = Artifact(
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            name=safe_name,
            type=type_str,
            reference=reference,
            size=size,
            checksum=checksum,
            metadata=metadata or {}
        )
        
        self._db[artifact.id] = artifact
        return artifact
        
    def read(self, artifact_id: str) -> Optional[Artifact]:
        return self._db.get(artifact_id)
        
    def download(self, artifact_id: str) -> Optional[bytes]:
        artifact = self.read(artifact_id)
        if not artifact:
            return None
            
        workspace = self.workspace_manager.get_workspace(artifact.user_id, artifact.project_id)
        if not workspace:
            return None
            
        target_file = Path(workspace.root_path) / artifact.reference
        if target_file.exists():
            return target_file.read_bytes()
        return None
        
    def list_artifacts(self, user_id: str, project_id: str) -> List[Artifact]:
        return [a for a in self._db.values() if a.user_id == user_id and a.project_id == project_id]
        
    def delete(self, artifact_id: str) -> bool:
        artifact = self.read(artifact_id)
        if not artifact:
            return False
            
        workspace = self.workspace_manager.get_workspace(artifact.user_id, artifact.project_id)
        if workspace:
            target_file = Path(workspace.root_path) / artifact.reference
            if target_file.exists():
                target_file.unlink()
                
        del self._db[artifact_id]
        return True
