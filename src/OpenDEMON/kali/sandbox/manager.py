"""KALI Sandbox Manager."""
import tempfile
import os
import sys
import shutil
from typing import Dict, Any, Optional
from pathlib import Path

from OpenDEMON.kali.sandbox.models import SandboxConfig, SandboxRequest, SandboxResult
from OpenDEMON.kali.sandbox.process import ProcessManager

class SandboxManager:
    """
    Coordinates secure execution of code inside temporary sandboxes.
    Routes execution to the correct language runner and enforces limits.
    """
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        
    def _get_runner_command(self, language: str, code_path: str) -> list[str]:
        """Resolves the executable command based on the requested language."""
        lang = language.lower()
        if lang in ("python", "python3", "py"):
            # Use current venv python safely
            return [sys.executable, code_path]
        elif lang in ("node", "javascript", "js"):
            return ["node", code_path]
        elif lang in ("typescript", "ts"):
            # Assume ts-node or similar is installed globally or locally
            return ["npx", "ts-node", code_path]
        elif lang in ("bash", "sh", "shell"):
            return ["bash", code_path]
        elif lang in ("powershell", "ps1"):
            return ["powershell", "-ExecutionPolicy", "Bypass", "-File", code_path]
        else:
            raise ValueError(f"Unsupported language runner: {language}")

    async def execute(self, request: SandboxRequest) -> SandboxResult:
        """
        Sets up an isolated workspace, writes the code and dependencies,
        executes it, and retrieves the results and any artifacts.
        """
        # Overrides
        limits = self.config.limits.model_copy()
        if request.timeout_override:
            limits.timeout_seconds = request.timeout_override

        # Prepare workspace manually for safer cleanup on Windows
        workspace = tempfile.mkdtemp(dir=self.config.work_dir)
        workspace_path = Path(workspace)
        
        try:
            # Write seed files
            for file_name, file_content in request.files.items():
                dest = workspace_path / file_name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(file_content, encoding="utf-8")
                
            # Write main code file
            extension = ".py" if "python" in request.language.lower() else ".js" if "node" in request.language.lower() or "javascript" in request.language.lower() else ".sh"
            if "powershell" in request.language.lower():
                extension = ".ps1"
                
            code_file = workspace_path / f"main{extension}"
            code_file.write_text(request.code, encoding="utf-8")
            
            try:
                command = self._get_runner_command(request.language, str(code_file))
            except ValueError as e:
                return SandboxResult(
                    success=False,
                    error=str(e)
                )

            # Env scoping
            env = {}
            for k in self.config.allowed_env_vars:
                if k in os.environ:
                    env[k] = os.environ[k]
                    
            if not self.config.allow_network:
                # Basic simulated offline switch where possible, 
                # true isolation requires Docker or firewall rules.
                env["HTTP_PROXY"] = "http://127.0.0.1:9999"
                env["HTTPS_PROXY"] = "http://127.0.0.1:9999"

            # Execute
            success, exit_code, stdout, stderr, duration, error = await ProcessManager.execute(
                command=command,
                cwd=workspace,
                limits=limits,
                env=env if env else None
            )
            
            # Capture modified/created artifacts (exclude the main code file)
            artifacts = {}
            for file_path in workspace_path.rglob("*"):
                if file_path.is_file() and file_path != code_file:
                    try:
                        rel_path = file_path.relative_to(workspace_path).as_posix()
                        artifacts[rel_path] = file_path.read_bytes()
                    except Exception:
                        pass
                        
            return SandboxResult(
                success=success,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                error=error,
                artifacts=artifacts
            )
        finally:
            # Cleanup safely
            try:
                shutil.rmtree(workspace, ignore_errors=True)
            except Exception:
                pass
