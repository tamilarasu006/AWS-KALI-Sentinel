"""Production Entry Point — runs migrations then starts Uvicorn."""

import os
import sys
import logging
import subprocess
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# Setup initial logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KALI.Deploy")

def run_migrations():
    """Run Alembic database migrations."""
    logger.info("Executing database migrations...")
    try:
        # Run alembic upgrade head
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Migrations completed successfully.")
        logger.debug(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e.stderr}")
        logger.warning("Continuing without migrations (database may be unavailable).")
    except FileNotFoundError:
        # Fallback if uv is not in PATH or if we are in standard docker with global alembic
        logger.warning("'uv' not found. Falling back to global alembic.")
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Migrations completed successfully via global alembic.")
            logger.debug(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Migration failed: {e.stderr}")
            logger.warning("Continuing without migrations (database may be unavailable).")

def start_server():
    """Start the FastAPI application."""
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    workers = int(os.environ.get("WORKERS", 1))
    
    logger.info(f"Starting KALI Server on {host}:{port} with {workers} workers.")
    
    # Using render_start module as the ASGI app wrapper but without the render fallback behavior
    uvicorn.run("render_start:app", host=host, port=port, workers=workers, log_level="info")

if __name__ == "__main__":
    if os.environ.get("SKIP_MIGRATIONS", "false").lower() != "true":
        run_migrations()
    else:
        logger.info("Skipping database migrations (SKIP_MIGRATIONS=true).")
        
    start_server()
