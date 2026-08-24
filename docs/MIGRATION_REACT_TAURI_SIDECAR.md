# DouyinGo React/Tauri + Python Sidecar Migration

This branch keeps the legacy PyQt entry point in place and adds the new desktop architecture beside it.

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

## API Surface

- `GET /health`
- `GET /api/config`
- `GET /api/tools`
- `GET /api/models`
- `POST /api/resolve`
- `POST /api/downloads`
- `GET /api/downloads`
- `GET /api/downloads/{job_id}`
- `POST /api/downloads/{job_id}/cancel`

The current API stores jobs in memory. A later merge-ready iteration should persist task history to SQLite if task history must survive app restarts.

## Development

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

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

Run Tauri in development:

```powershell
npm.cmd run tauri:dev
```

During early development, if the PyInstaller sidecar has not been built yet, the React UI uses `http://127.0.0.1:8765`. Start the backend manually with `python -m backend.sidecar serve`.

The packaged desktop app prefers port `8765`. If another local service already owns that port, Tauri selects an available loopback port, starts the sidecar there, and returns the actual URL to React.

Tauri also passes its process ID to the packaged sidecar. A watchdog exits the Python service when the owning desktop process disappears, including crash and forced-close cases where PyInstaller's child process would otherwise be orphaned.

## Packaging

Build the Python sidecar for the current Rust target:

```powershell
npm.cmd run package:sidecar
```

This runs PyInstaller, embeds `ffmpeg.exe`/`ffprobe.exe` when present, bundles the
official Deno runtime plus the matching `yt-dlp-ejs` challenge solver, and copies
the output to:

```text
src-tauri/binaries/douyingo-sidecar-<target-triple>.exe
```

The build guard requires `yt-dlp 2026.08.19` or newer. This avoids packaging the
known-broken July 2026 YouTube client behavior that can return HTTP 403 for media
URLs even when metadata extraction succeeds.

Then build the desktop app:

```powershell
npm.cmd run tauri:build
```

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

## Migration Gates

Before merging this branch back to `main`, verify:

1. Python compile and smoke tests pass.
2. Sidecar health, tool inventory (including Deno and `yt-dlp-ejs`), and invalid-request API tests pass.
3. React build passes after `npm.cmd install`.
4. `npm.cmd run package:sidecar` produces the suffixed binary under `src-tauri/binaries/`.
5. `npm.cmd run tauri:dev` starts the UI and can connect to the sidecar.
6. At least one real download per platform is manually tested with legal test URLs.
7. FFmpeg-dependent Koushare and thumbnail flows work from both source and packaged sidecar.
8. AI model discovery is pointed at a real model directory through `DOUYINGO_MODELS_DIR` or `models/`.

## Known Follow-Ups

- Add persistent job history.
- Add explicit per-platform cookies/proxy settings for yt-dlp.
- Implement real AI post-processing once the model type is chosen.
- Add front-end integration tests after the UI stabilizes.
- Replace direct stdout logs with structured sidecar events if fine-grained progress streaming is needed.
