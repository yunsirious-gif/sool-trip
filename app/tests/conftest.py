import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

os.environ.setdefault("STREAMLIT_HOME", str(APP_DIR / ".streamlit"))
