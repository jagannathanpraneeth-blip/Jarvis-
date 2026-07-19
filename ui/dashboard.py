import os
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from core.logger import get_logger
from core.state import get_state

logger = get_logger("ui.dashboard")

app = FastAPI(title="JARVIS Dashboard")

# Global reference to settings and state
_settings = None
_brain = None

def get_log_file() -> str:
    """Gets the path to the most recent log file."""
    if not _settings:
        return ""
    log_dir = Path(_settings.log_dir_path)
    if not log_dir.exists():
        return ""
    # Get all .log files, sort by modified time
    log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return str(log_files[0]) if log_files else ""


@app.get("/api/status")
async def get_status():
    """Returns the current status of JARVIS."""
    # This could be hooked up to real state later
    return {
        "status": "online",
        "muted": getattr(_settings.voice, 'muted', False) if _settings and hasattr(_settings, 'voice') else False,
        "god_mode": getattr(_settings.plugins, 'god_mode', False) if _settings and hasattr(_settings, 'plugins') else False,
        "model": getattr(_settings.brain, 'model', 'unknown') if _settings and hasattr(_settings, 'brain') else "unknown",
        "active_agents": [] # Would hook into Swarm state
    }

@app.get("/api/state")
async def api_get_state():
    """Returns the current system state."""
    return get_state()

@app.get("/api/logs")
async def get_logs(lines: int = 50):
    """Returns the last N lines of the current log file."""
    log_path = get_log_file()
    if not log_path or not os.path.exists(log_path):
        return {"logs": ["No logs available."]}
        
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return {"logs": [line.strip() for line in all_lines[-lines:]]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {e}"]}


def serve(settings, brain, host="127.0.0.1", port=8000):
    """Entry point to start the dashboard in a background thread."""
    global _settings, _brain
    _settings = settings
    _brain = brain
    
    # Ensure static dir exists
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def index():
        index_path = static_dir / "index.html"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return "<h1>JARVIS Dashboard</h1><p>index.html not found in static folder.</p>"

    logger.info(f"Starting JARVIS Web Dashboard on http://{host}:{port}")
    # uvicorn must be run programmatically
    # We disable access_log so it doesn't spam JARVIS's own logs
    uvicorn.run(app, host=host, port=port, log_level="warning")
