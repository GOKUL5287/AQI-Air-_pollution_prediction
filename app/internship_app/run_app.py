"""
TerraPulse — Global Air & Ocean Intelligence Platform
Root runner script to launch the unified Flask server and WebGL application.
"""

import os
import sys
import subprocess

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


def start_seasonal_dashboard():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_dir = os.path.abspath(os.path.join(app_dir, os.pardir, "SeasonalHealthDashboard"))
    dashboard_port = int(os.environ.get("SEASONAL_STREAMLIT_PORT", "8501"))
    streamlit_url = f"http://127.0.0.1:{dashboard_port}"
    os.environ.setdefault("SEASONAL_STREAMLIT_URL", streamlit_url)

    print("Starting seasonal Streamlit insights at " + streamlit_url)
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.address", "127.0.0.1",
         "--server.port", str(dashboard_port),
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=dashboard_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    seasonal_process = start_seasonal_dashboard()
    print("=" * 70)
    print("AIR QUALITY INDEX -- Global Environmental Intelligence")
    print(f"Running cinematic AQI & API server on http://localhost:{port}")
    print(f"Seasonal insights route: http://localhost:{port}/seasonal-insights")
    print("=" * 70)
    try:
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
    finally:
        seasonal_process.terminate()
        seasonal_process.wait(timeout=10)
