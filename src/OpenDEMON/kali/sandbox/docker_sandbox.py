try:
    import docker
    HAS_DOCKER = True
except ImportError:
    HAS_DOCKER = False
    
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DockerSandbox:
    """Provides a secure execution environment via ephemeral Docker containers."""
    
    def __init__(self, image: str = "python:3.11-slim", network_disabled: bool = True):
        self.image = image
        self.network_disabled = network_disabled
        self.client = None
        if HAS_DOCKER:
            try:
                self.client = docker.from_env()
            except Exception as e:
                logger.warning(f"Failed to connect to Docker daemon: {e}")
        else:
            logger.warning("Docker module not found. Sandbox offline.")

    def execute_code(self, code: str, timeout: int = 10) -> Dict[str, Any]:
        """Executes arbitrary python code within the sandbox."""
        if not self.client:
            return {"success": False, "output": "Docker daemon not accessible. Sandbox offline."}
            
        try:
            # Command to run python code directly
            command = ["python", "-c", code]
            
            # Run container
            container = self.client.containers.run(
                self.image,
                command=command,
                network_disabled=self.network_disabled,
                mem_limit="128m",
                cpus=0.5,
                detach=True
            )
            
            try:
                result = container.wait(timeout=timeout)
                logs = container.logs().decode("utf-8")
                success = result.get("StatusCode", 1) == 0
                return {"success": success, "output": logs}
            except Exception as e:
                return {"success": False, "output": f"Timeout or execution error: {e}"}
            finally:
                container.remove(force=True)
                
        except Exception as e:
            return {"success": False, "output": f"Sandbox error: {e}"}

    def health(self) -> bool:
        """Check if sandbox is available."""
        return self.client is not None
