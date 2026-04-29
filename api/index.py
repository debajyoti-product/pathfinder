import sys
import os

# Add root to path so backend can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

# Vercel needs the app object
handler = app
