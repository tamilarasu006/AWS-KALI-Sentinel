"""Process isolation and execution mechanisms."""

import asyncio
import os
import sys
import time
from typing import Dict, Optional, Tuple

from OpenDEMON.kali.sandbox.models import ResourceLimits

class ProcessManager:
    """
    Manages process execution, streams, timeouts, and soft resource limits.
    Since Windows does not natively support strict Linux cgroups/resource module limits easily in Python,
    this uses soft monitoring and strict stream truncation.
    """
    
    @staticmethod
    async def execute(
        command: list[str],
        cwd: str,
        limits: ResourceLimits,
        env: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, Optional[int], str, str, float, Optional[str]]:
        """
        Executes a command with resource restrictions.
        Returns: (success, exit_code, stdout, stderr, duration, error_msg)
        """
        start_time = time.time()
        
        # Scrub environment if not explicitly provided
        # By default we pass minimal safe vars if env is empty
        safe_env = {}
        if env is not None:
            safe_env = env
        else:
            # Typical safe minimums for Windows/Linux
            for k in ["PATH", "SystemRoot", "USERPROFILE", "TMP", "TEMP"]:
                if k in os.environ:
                    safe_env[k] = os.environ[k]

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                env=safe_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout_data = bytearray()
            stderr_data = bytearray()
            
            async def read_stream(stream, out_buffer, max_bytes):
                while True:
                    chunk = await stream.read(4096)
                    if not chunk:
                        break
                    out_buffer.extend(chunk)
                    if len(out_buffer) > max_bytes:
                        out_buffer.extend(b"\n[OUTPUT TRUNCATED: Max size exceeded]")
                        break

            # Run with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        read_stream(process.stdout, stdout_data, limits.max_output_size_bytes),
                        read_stream(process.stderr, stderr_data, limits.max_output_size_bytes),
                        process.wait()
                    ),
                    timeout=limits.timeout_seconds
                )
                
                duration = time.time() - start_time
                success = process.returncode == 0
                
                return (
                    success,
                    process.returncode,
                    stdout_data.decode("utf-8", errors="replace"),
                    stderr_data.decode("utf-8", errors="replace"),
                    duration,
                    None
                )
                
            except asyncio.TimeoutError:
                # Terminate the process tree
                try:
                    process.kill()
                except OSError:
                    pass
                
                duration = time.time() - start_time
                return (
                    False,
                    -1,
                    stdout_data.decode("utf-8", errors="replace"),
                    stderr_data.decode("utf-8", errors="replace"),
                    duration,
                    f"Execution timed out after {limits.timeout_seconds}s"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return False, -1, "", "", duration, str(e)
