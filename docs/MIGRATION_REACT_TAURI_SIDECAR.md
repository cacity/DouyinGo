# DouyinGo React/Tauri + Python Sidecar Migration

The React/Tauri application is the primary desktop product on this branch. The
legacy PyQt entry point remains only as migration-reference code and uses the
optional `requirements-legacy.txt` dependency set.

## Target Architecture

```
React/Vite UI
  -> Tauri commands
  -> Python sidecar FastAPI backend
  -> existing Python downloaders
  -> yt-dlp / FFmpeg / local AI model hooks
```

### Boundaries

- `src/`: React desktop UI for tasks, progress, tool inventory, and model selection.
- `src-tauri/`: Tauri 2 shell, sidecar launcher, and native file reveal command.
- `backend/`: Python FastAPI sidecar that wraps existing downloaders and exposes stable HTTP APIs.
- `core/`: existing platform downloader code, preserved as the media implementation layer.
- `scripts/build_sidecar.py`: PyInstaller build that creates the Tauri sidecar binary with the required target triple suffix.
- `scripts/verify_media_contract.py`: deterministic source/packaged HLS, FFmpeg,
  cancellation, and AI-runner contract verification.

## API Surface

- `GET /health`
- `GET /api/config`
- `PUT /api/config`
- `GET /api/tools`
- `GET /api/models`
- `POST /api/models/directory`
- `POST /api/resolve`
- `POST /api/downloads`
- `GET /api/downloads`
- `DELETE /api/downloads`
- `GET /api/downloads/{job_id}`
- `DELETE /api/downloads/{job_id}`
- `POST /api/downloads/{job_id}/cancel`

Download jobs are persisted in `jobs.sqlite3`. User defaults are persisted
separately in `sidecar-config.json`; the legacy PyQt `config.json` is not
overwritten.

The desktop settings expose independent proxy URLs and browser-cookie sources for
YouTube and Twitter/X. Supported proxy schemes are `http`, `https`, `socks4`,
`socks4a`, `socks5`, and `socks5h`; supported browsers are Chrome, Edge, Firefox,
Brave, and Chromium. These credentials are passed to yt-dlp only while a job is
running. They are never copied into task records, metadata JSON, or
`jobs.sqlite3`.

CORS is restricted to Tauri origins and loopback Vite development origins. The
sidecar does not accept browser requests from arbitrary web origins. The Tauri
WebView also uses an explicit production CSP that permits only application assets,
IPC, and loopback sidecar connections.

## Media Contract

- Video: `MP4`, `MKV`, or `MOV`.
- Audio: `MP3`, `M4A`, or `WAV`.
- Cover: `JPG`.
- YouTube and Twitter/X use native yt-dlp media and post-processing options.
- Douyin and Koushare download their native media first, then use the bundled
  FFmpeg for audio extraction, cover extraction, or container remuxing.
- `save_metadata` writes a stable UTF-8 JSON sidecar with the source URL,
  selected options, downloaded files, and sanitized platform metadata.

Unsupported type/format pairs and unavailable AI runners are rejected before a
job is queued. Successful jobs only report final files that exist on disk. Active
cancel requests remain `cancelled` rather than being rewritten as download errors;
FFmpeg processes are stopped and partial outputs are removed.

## AI Model Runners

Raw `.gguf`, `.onnx`, `.safetensors`, `.pt`, `.pth`, and `.bin` files are model
artifacts, not executable integrations. They remain visible as disabled until a
runner manifest named `douyingo-model.json` is placed beside the model:

```json
{
  "id": "local-captioner",
  "name": "Local captioner",
  "provider": "command",
  "capabilities": ["postprocess"],
  "command": ["runner.exe", "--input", "{input}", "--output", "{output_dir}"],
  "timeout_seconds": 3600
}
```

The runner receives a versioned job JSON document on standard input. Supported
command placeholders are `{input}`, `{output_dir}`, `{metadata}`, and
`{model_dir}`. It may print a JSON object with a `downloaded_files` array; every
reported path must exist inside the task output directory. Commands are launched
directly without a shell.

Runner execution is polled while active. Cancellation and timeout terminate the
runner process tree, including child processes created by a runner.

The AI panel's folder button creates and reveals the configured model directory.
This gives model artifacts and `douyingo-model.json` manifests a stable install
location without exposing arbitrary filesystem creation through the API.

## Development

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

The default requirements contain only sidecar/runtime/build dependencies. Install
`requirements-legacy.txt` only when intentionally running the old PyQt reference UI.

Install frontend dependencies:

```powershell
npm.cmd install
```

Run the backend only:

```powershell
python -m backend.sidecar serve
```

Run the React UI only:

```powershell
npm.cmd run dev
```

Build the sidecar once, then run Tauri in development:

```powershell
npm.cmd run package:sidecar
npm.cmd run tauri:dev
```

During early development, if the PyInstaller sidecar has not been built yet, the React UI uses `http://127.0.0.1:8765`. Start the backend manually with `python -m backend.sidecar serve`.

The packaged desktop app prefers port `8765`. If another local service already owns that port, Tauri selects an available loopback port, starts the sidecar there, and returns the actual URL to React.

Tauri also passes its process ID to the packaged sidecar. A watchdog exits the
Python service when the owning desktop process disappears, including crash and
forced-close cases where PyInstaller's child process would otherwise be orphaned.
Explicit close, retry, and startup-timeout paths terminate the full Windows
PyInstaller process tree.

## Packaging

Build the Python sidecar for the current Rust target:

```powershell
npm.cmd run package:sidecar
```

This runs PyInstaller, requires and embeds `ffmpeg.exe`/`ffprobe.exe`, bundles the
official Deno runtime plus the matching `yt-dlp-ejs` challenge solver, and copies
the output to:

```text
src-tauri/binaries/douyingo-sidecar-<target-triple>.exe
```

The build guard requires `yt-dlp 2026.08.19` or newer. This avoids packaging the
known-broken July 2026 YouTube client behavior that can return HTTP 403 for media
URLs even when metadata extraction succeeds.

Build the complete desktop app:

```powershell
npm.cmd run tauri:build
```

`tauri:build` always runs `package:sidecar` first, so a backend change cannot be
silently shipped with a stale sidecar executable.

Tauri requires `externalBin` sidecars to use a target-triple suffix. The target triple can be inspected with:

```powershell
rustc -vV
```

Packaged downloads prefer `~/Downloads/DouyinGo/<platform>_downloads`. If the
Downloads folder is not writable, the sidecar falls back to the application-data
folder under `DouyinGo/downloads`. Sandboxed environments that deny both locations
use the stable `%TEMP%/DouyinGo/downloads` folder as a last resort; the random
PyInstaller `_MEI` extraction directory is never used for user output.
Configuration and local model discovery use the platform application-data folder.
Development runs retain the project-relative directories. These locations can be
overridden with `DOUYINGO_DOWNLOADS_DIR`, `DOUYINGO_DATA_DIR`, and
`DOUYINGO_MODELS_DIR`.

`DOUYINGO_KOUSHARE_API_BASE` exists only for deterministic test injection. Normal
source and packaged runs use Koushare's production API endpoint.

Download task history is stored in `jobs.sqlite3` under the same application-data
folder. The sidecar keeps the newest 500 terminal tasks. A queued, resolving, or
downloading task found after a sidecar restart is retained and marked cancelled
with an interruption message; it is never resumed implicitly. The UI can remove
one terminal record or clear all terminal records. These actions only remove task
history and never delete downloaded media or metadata files.

## Migration Gates

Before merging this branch back to `main`, verify:

1. Python compile and smoke tests pass.
2. Sidecar health, tool inventory (including Deno and `yt-dlp-ejs`), and invalid-request API tests pass.
3. SQLite history survives a service restart, interrupted tasks recover as cancelled, and terminal history can be deleted without deleting output files.
4. React build passes after `npm.cmd install`.
5. `npm.cmd run tauri:build` rebuilds the suffixed sidecar and produces the NSIS installer.
6. `npm.cmd run tauri:dev` starts the UI and can connect to the sidecar.
7. At least one real download per platform is manually tested with legal test URLs.
8. FFmpeg-dependent Koushare and thumbnail flows work from both source and packaged sidecar.
9. AI model discovery is pointed at a real model directory through `DOUYINGO_MODELS_DIR` or `models/`.

The FFmpeg/Koushare contract can be exercised without external media or accounts:

```powershell
npm.cmd run verify:media
```

This generates a local HLS fixture and drives both the source and packaged
sidecars through video/MKV, audio/MP3, cover/JPG, metadata, ffprobe, active HLS
cancellation, AI manifest execution, and AI runner process-tree cancellation.

## Known Follow-Ups

- Ship and validate a concrete model runner for the model family selected by the product owner.
- Add front-end integration tests after the UI stabilizes.
- Replace direct stdout logs with structured sidecar events if fine-grained progress streaming is needed.
