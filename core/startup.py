"""
JARVIS Persistence Module

Handles injecting JARVIS into the Windows Startup sequence so it runs on boot.
"""

import os
import sys
import subprocess
from pathlib import Path
from core.logger import get_logger

logger = get_logger("core.startup")


def ensure_startup():
    """
    Checks if a JARVIS shortcut exists in the Windows Startup folder.
    If not, it generates a VBScript to create one.
    """
    if sys.platform != "win32":
        logger.info("Startup persistence is only supported on Windows.")
        return

    # Find the shell:startup folder
    startup_dir = Path(os.getenv("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    shortcut_path = startup_dir / "JARVIS.lnk"
    
    if shortcut_path.exists():
        return
        
    logger.info("Injecting JARVIS into Windows Startup sequence...")
    
    # We need to run main.py using the virtual environment python
    # This assumes JARVIS is run from the project root
    jarvis_root = Path(os.getcwd()).absolute()
    python_exe = jarvis_root / "venv" / "Scripts" / "pythonw.exe"  # pythonw to hide console on boot
    
    # If pythonw doesn't exist (e.g. some uv setups), fallback to python.exe
    if not python_exe.exists():
        python_exe = jarvis_root / "venv" / "Scripts" / "python.exe"
        
    main_script = jarvis_root / "main.py"
    
    # Create a temporary VBScript to generate the .lnk
    vbs_path = jarvis_root / "temp" / "create_shortcut.vbs"
    os.makedirs(jarvis_root / "temp", exist_ok=True)
    
    vbs_content = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{python_exe}"
oLink.Arguments = "{main_script}"
oLink.WorkingDirectory = "{jarvis_root}"
oLink.Description = "JARVIS Autonomous AI"
oLink.WindowStyle = 7 ' Minimized
oLink.Save
"""
    try:
        vbs_path.write_text(vbs_content, encoding="utf-8")
        subprocess.run(["cscript.exe", "//Nologo", str(vbs_path)], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        logger.info(f"Startup shortcut created successfully at {shortcut_path}")
    except Exception as e:
        logger.error(f"Failed to create startup shortcut: {e}")
    finally:
        if vbs_path.exists():
            try:
                vbs_path.unlink()
            except Exception:
                pass
