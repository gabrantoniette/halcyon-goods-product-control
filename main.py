"""Entry point for the Halcyon Goods internal product control system.

Running this single file starts the records API, serves the web front-end and
opens it in the browser:

    python main.py

The interface is reachable at http://halcyongoods.test, which requires one line
in the system hosts file pointing that name at this machine (see HOSTS_LINE
below). Without it the client still runs and falls back to the loopback address.

The same client is also available as a terminal menu:

    python main.py --cli
"""

import argparse
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

import uvicorn

from client.backend import api_client
from client.backend.menu import menu
from client.backend.server import app as client_app

# This file sits at the project root, so the API package is importable from here
# and paths never depend on the directory the command was run from.
PROJECT_DIR = Path(__file__).resolve().parent

# Friendly name for the UI. The .test suffix is reserved by RFC 6761 for local
# development, so it can never clash with a real domain on the internet.
CLIENT_HOSTNAME = "halcyongoods.test"
CLIENT_BIND = "127.0.0.1"
DEFAULT_PORT = 80

HOSTS_PATH = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "drivers" / "etc" / "hosts"
HOSTS_LINE = f"{CLIENT_BIND}   {CLIENT_HOSTNAME}"

# How long to wait for the API subprocess to accept connections.
API_STARTUP_TIMEOUT = 15


def api_address():
    """Host and port the API should listen on, taken from API_BASE_URL."""
    parsed = urlparse(api_client.API_BASE_URL)
    return parsed.hostname or "127.0.0.1", parsed.port or 8000


def start_api():
    """Launch the API in a subprocess and wait until it answers."""
    host, port = api_address()
    # flush so the banner is not held in the buffer when stdout is not a terminal
    print(f"Starting the API on http://{host}:{port} ...", flush=True)

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", host, "--port", str(port)],
        cwd=PROJECT_DIR,
    )

    deadline = time.monotonic() + API_STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if api_client.is_api_up():
            return process
        if process.poll() is not None:
            raise RuntimeError("The API process stopped before it was ready.")
        time.sleep(0.3)

    process.terminate()
    raise RuntimeError(f"The API did not respond within {API_STARTUP_TIMEOUT}s.")


def ensure_api():
    """Return the API subprocess we started, or None if one was already running."""
    if api_client.is_api_up():
        print(f"API already running at {api_client.API_BASE_URL}", flush=True)
        return None
    return start_api()


def hostname_points_here():
    """True when CLIENT_HOSTNAME resolves to this machine."""
    try:
        return socket.gethostbyname(CLIENT_HOSTNAME) == CLIENT_BIND
    except OSError:
        return False


def port_is_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        return probe.connect_ex((CLIENT_BIND, port)) != 0


def build_url(host, port):
    """Port 80 is the http default, so it is left out of the address."""
    return f"http://{host}" if port == 80 else f"http://{host}:{port}"


def serve_web(port):
    if not port_is_free(port):
        raise RuntimeError(
            f"Port {port} is already in use.\n"
            f"Stop whatever is using it, or run: python main.py --port 8501"
        )

    if hostname_points_here():
        url = build_url(CLIENT_HOSTNAME, port)
    else:
        url = build_url(CLIENT_BIND, port)
        print(
            f"\nNote: '{CLIENT_HOSTNAME}' does not point at this machine yet.\n"
            f"To use that address, add this line to {HOSTS_PATH} as administrator:\n"
            f"    {HOSTS_LINE}"
        )

    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    print(f"\n  Product control  ->  {url}")
    print(f"  Records API      ->  {api_client.API_BASE_URL}")
    print("\n  Press Ctrl+C to stop.\n", flush=True)

    uvicorn.run(client_app, host=CLIENT_BIND, port=port, log_level="warning")


def main():
    parser = argparse.ArgumentParser(description="Halcyon Goods internal product control client.")
    parser.add_argument("--cli", action="store_true", help="use the terminal menu instead of the web UI")
    parser.add_argument("--no-api", action="store_true", help="do not start the API, expect it to be running")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT,
        help=f"port for the web UI (default {DEFAULT_PORT})",
    )
    args = parser.parse_args()

    api_process = None
    try:
        if not args.no_api:
            api_process = ensure_api()
        elif not api_client.is_api_up():
            print(f"Warning: no API answering at {api_client.API_BASE_URL}")

        if args.cli:
            menu()
        else:
            serve_web(args.port)
    except KeyboardInterrupt:
        print("\nStopping...")
    except RuntimeError as error:
        print(f"\n{error}")
        return 1
    finally:
        if api_process is not None:
            api_process.terminate()
            api_process.wait(timeout=5)

    return 0


if __name__ == "__main__":
    sys.exit(main())
