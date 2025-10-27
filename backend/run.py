#!/usr/bin/env python3
"""Convenience launcher for the PV Power Forecasting backend."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import uvicorn

APP_PATH = 'app.main:app'
BASE_DIR = Path(__file__).resolve().parent


def str_to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    return normalized in {'1', 'true', 'yes', 'on'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the FastAPI backend via Uvicorn.')
    parser.add_argument('--host', default=os.environ.get('API_HOST', '0.0.0.0'), help='Host interface to bind.')
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.environ.get('API_PORT', '8000')),
        help='Port to expose the API on.',
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        default=None,
        help='Enable autoreload (useful during development).',
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of worker processes (ignored when reload is on).',
    )
    return parser.parse_args()


def resolve_reload(requested: Optional[bool]) -> bool:
    env_default = str_to_bool(os.environ.get('API_RELOAD'), default=False)
    return env_default if requested is None else requested


def resolve_workers(requested: Optional[int], reload_enabled: bool) -> int:
    if reload_enabled:
        return 1
    env_workers = os.environ.get('API_WORKERS')
    if requested:
        return requested
    if env_workers:
        try:
            return max(1, int(env_workers))
        except ValueError:
            pass
    return 1


def ensure_backend_on_path() -> None:
    # Since we're now running from backend directory, add current directory to path
    if str(BASE_DIR) not in sys.path:
        sys.path.append(str(BASE_DIR))


def main() -> None:
    args = parse_args()
    reload_enabled = resolve_reload(args.reload)
    workers = resolve_workers(args.workers, reload_enabled)

    ensure_backend_on_path()

    uvicorn.run(
        APP_PATH,
        host=args.host,
        port=args.port,
        reload=reload_enabled,
        workers=workers,
        log_level=os.environ.get('API_LOG_LEVEL', 'info'),
    )


if __name__ == '__main__':
    main()
