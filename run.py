import subprocess
import sys
import threading
from pathlib import Path

from api import serve

threading.Thread(target=serve, daemon=True).start()
subprocess.run(
    [sys.executable, "-m", "streamlit", "run", str(Path(__file__).parent / "app.py")]
)
