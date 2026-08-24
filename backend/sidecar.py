from __future__ import annotations

import argparse
import os
import threading
import time

import uvicorn

from backend.app import app as fastapi_app


def process_is_running(pid: int) -> bool:
    if pid <= 0:
        return False

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False

        try:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def start_parent_watchdog(parent_pid: int | None) -> None:
    if not parent_pid:
        return

    def watch_parent() -> None:
        while process_is_running(parent_pid):
            time.sleep(1)
        os._exit(0)

    threading.Thread(target=watch_parent, name="parent-watchdog", daemon=True).start()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="douyingo-sidecar")
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="Run the DouyinGo sidecar API server.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=int(os.getenv("DOUYINGO_BACKEND_PORT", "8765")))
    serve.add_argument("--log-level", default=os.getenv("DOUYINGO_LOG_LEVEL", "info"))
    serve.add_argument("--parent-pid", type=int)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in {None, "serve"}:
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 8765)
        start_parent_watchdog(getattr(args, "parent_pid", None))
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
