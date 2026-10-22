"""
TerraPulse — Global Air & Ocean Intelligence Platform
Root runner script to launch the unified Flask server and WebGL application.
"""

import os
import sys

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure backend directory is in sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 70)
    print("AIR QUALITY INDEX -- Global Environmental Intelligence")
    print(f"Running cinematic AQI & API server on http://localhost:{port}")
    print("=" * 70)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
