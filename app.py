"""
app.py — Single-Command Launcher for Modern AI Agent Studio.
Usage: python app.py [--port 8000] [--host 127.0.0.1] [--no-browser]
"""

import argparse
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv

# Load .env before initializing app
env_path = Path(project_root) / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

from code_helper.server import create_app


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser for studio server."""
    parser = argparse.ArgumentParser(
        description="Launch the Modern AI Agent Studio web interface for Multi-Agent Code Helper."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the web server on (default: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the default web browser on launch",
    )
    return parser


def open_browser_delayed(url: str, delay: float = 1.2) -> None:
    """Open default browser in a background thread after brief startup pause."""
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_open, daemon=True).start()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    print("=" * 60)
    print("  MODERN AI AGENT STUDIO — MULTI-AGENT CODE HELPER")
    print("=" * 60)
    print(f"[*] Studio URL       : {url}")
    print(f"[*] Root Agent       : Coordinator (5 Agents Team)")
    print(f"[*] Web UI Directory : {Path(project_root) / 'web'}")
    print("------------------------------------------------------------")

    if not args.no_browser:
        print("[*] Automatically opening browser window...")
        open_browser_delayed(url)

    print("[*] Starting Uvicorn server (Press Ctrl+C to stop)...")
    import uvicorn
    app = create_app(mock_mode=False, static_dir=str(Path(project_root) / "web"))
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
