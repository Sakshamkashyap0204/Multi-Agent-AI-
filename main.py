import os
import sys
from pathlib import Path

# Add directories to sys.path so all backend modules and root modules resolve seamlessly
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Expose app attribute so "main:app" resolves cleanly
from backend.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    # Must pass "main:app" string because Render sets WEB_CONCURRENCY
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=1)
