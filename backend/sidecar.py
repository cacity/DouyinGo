from __future__ import annotations

import argparse
import os

import uvicorn

from backend.app import app as fastapi_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="douyingo-sidecar")
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="Run the DouyinGo sidecar API server.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=int(os.getenv("DOUYINGO_BACKEND_PORT", "8765")))
    serve.add_argument("--log-level", default=os.getenv("DOUYINGO_LOG_LEVEL", "info"))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in {None, "serve"}:
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 8765)
        print(f"READY http://{host}:{port}", flush=True)
        uvicorn.run(
            fastapi_app,
            host=host,
            port=port,
            log_level=getattr(args, "log_level", "info"),
            reload=False,
        )
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
