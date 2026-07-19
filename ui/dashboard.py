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

from pydantic import BaseModel

class ChatRequest(BaseModel):
    text: str

@app.post("/api/chat")
async def post_chat(req: ChatRequest):
    """Processes a text message from the web UI."""
    if not _brain or not _buffer:
        return {"response": "Error: Brain or Buffer not initialized.", "status": "error"}
        
    try:
        user_input = req.text.strip()
        history = _buffer.get_history()
        
        # We can simulate the state changing to 'thinking' by triggering the state manager or we just let it be blocking
        # But `brain.think` is synchronous and blocks the async endpoint. It's okay for a local prototype.
        response = _brain.think(user_input, history)
        
        # Update buffer
        _buffer.add("user", user_input)
        _buffer.add("assistant", response)
        
        # Speak the response using ElevenLabs
        from core.tts import TTSManager
        import threading
        def speak_async():
            tts = TTSManager(_settings)
            tts.speak(response, block=True)
            
        threading.Thread(target=speak_async, daemon=True).start()
        
        return {"response": response, "status": "success"}
    except Exception as e:
        logger.error(f"API Chat Error: {e}", exc_info=True)
        return {"response": f"I encountered an error: {e}", "status": "error"}

from fastapi import WebSocket, WebSocketDisconnect
from core.state import get_state, subscribe_events
import asyncio

# Global set of active websocket queues
_active_ws_queues = set()

def _on_telemetry_event(event: dict):
    # This is called from the synchronous thread (e.g. Brain or VoiceLoop)
    # We must put it into all active asyncio queues safely
    for q, loop in _active_ws_queues:
        asyncio.run_coroutine_threadsafe(q.put(event), loop)

subscribe_events(_on_telemetry_event)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Queue for this specific connection
    event_queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    
    queue_ref = (event_queue, loop)
    _active_ws_queues.add(queue_ref)
    
    last_state = None
    
    async def poll_state():
        nonlocal last_state
        while True:
            current_state = get_state()
            if current_state["status"] != last_state:
                await event_queue.put({"type": "state", "state": current_state["status"]})
                last_state = current_state["status"]
            await asyncio.sleep(0.5)
            
    poll_task = asyncio.create_task(poll_state())
    
    try:
        while True:
            event = await event_queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        poll_task.cancel()
        _active_ws_queues.remove(queue_ref)


_buffer = None

def serve(settings, brain, buffer, host="127.0.0.1", port=8000):
    """Entry point to start the dashboard in a background thread."""
    global _settings, _brain, _buffer
    _settings = settings
    _brain = brain
    _buffer = buffer
    
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
