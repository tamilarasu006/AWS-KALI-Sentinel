from typing import Dict, Any, List
from .docker_sandbox import DockerSandbox

class SandboxTools:
    """Provides tools that strictly execute within the KALI Sandbox."""
    
    def __init__(self):
        self.sandbox = DockerSandbox(network_disabled=True)
        self.cyber_sandbox = DockerSandbox(image="kalilinux/kali-rolling", network_disabled=False) # Cyber tools need network but are isolated
        
    def execute_python(self, code: str) -> Dict[str, Any]:
        """Safely executes python code."""
        return self.sandbox.execute_code(code)
        
    def run_nmap(self, target: str) -> Dict[str, Any]:
        """Safely runs nmap against a target from within the isolated cyber sandbox."""
        if not self.cyber_sandbox.client:
            return {"success": False, "output": "Sandbox offline."}
            
        try:
            # Install nmap and run
            command = f"apt-get update && apt-get install -y nmap && nmap {target}"
            container = self.cyber_sandbox.client.containers.run(
                self.cyber_sandbox.image,
                command=["bash", "-c", command],
                detach=True
            )
            result = container.wait(timeout=30)
            logs = container.logs().decode("utf-8")
            container.remove(force=True)
            return {"success": result.get("StatusCode") == 0, "output": logs}
        except Exception as e:
            return {"success": False, "output": str(e)}
