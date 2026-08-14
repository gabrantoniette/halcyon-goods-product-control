"""Entry point for the terminal client.

    python -m halcyon_cli          # or: halcyon

The API it talks to is set with HALCYON_API_BASE_URL; writes additionally need
HALCYON_API_KEY when the API has one configured.
"""

import argparse
import sys

from . import api_client
from .menu import menu


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="halcyon",
        description="Terminal client for the Halcyon Goods product control API.",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help=f"override the API address (default {api_client.API_BASE_URL})",
    )
    args = parser.parse_args()

    if args.api_url:
        api_client.API_BASE_URL = args.api_url.rstrip("/")

    if not api_client.is_api_up():
        print(f"No API answering at {api_client.API_BASE_URL}")
        print("Start it with:  docker compose up  (or: uvicorn halcyon_api.main:app)")
        return 1

    try:
        menu()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
