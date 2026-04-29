import sys
import os

# Add root and backend to path so imports work on Vercel
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "backend"))

from backend.main import app

# Vercel needs the app object
handler = app
