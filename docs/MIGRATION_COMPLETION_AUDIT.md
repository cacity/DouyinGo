# DouyinGo Migration Completion Audit

Date: 2026-08-24

Branch: `migration/react-tauri-sidecar`

## Requirement Evidence

| Requirement | Status | Authoritative evidence |
| --- | --- | --- |
| Work remains isolated until merge approval | Verified | The worktree is on `migration/react-tauri-sidecar`; `main` remains at `31b0f8e` and no merge or push was performed. |
| React/Tauri replaces PyQt as the primary desktop UI | Verified | `src/`, `src-tauri/`, the release executable, and a visually inspected CSP-enabled WebView provide the product UI. PyQt is optional reference code under `requirements-legacy.txt`. |
| Tauri owns Python sidecar startup and shutdown | Verified | Dynamic-port Rust tests, occupied-port release smoke tests, parent watchdog tests, normal-close smoke tests, and process-tree checks pass. |
| FastAPI provides stable desktop contracts | Verified | Health, config, tools, models, resolve, create/list/get/cancel/delete downloads, and model-directory APIs pass `test_backend_api.py`. |
| FFmpeg, ffprobe, yt-dlp, Deno, and yt-dlp-ejs are packaged | Verified | The packaged API reports all tools; packaging now fails when FFmpeg/ffprobe are absent; current hashes are recorded in `MIGRATION_VERIFICATION_2.0.2.md`. |
| YouTube download regressions are resolved | Verified | The user-supplied URLs `k7nje82oYhI` and `COpWTc7BFro` completed through source and packaged sidecars. The latter repeatedly emitted missing speed/ETA values and completed as a 4K MP4 after the progress-hook fix. |
| Media output formats are real, not UI-only | Verified | Source and packaged contracts produce MKV audio/video, MP3 audio, JPG cover, and metadata through the API. |
| Download lifecycle is durable and cancellable | Verified | SQLite restart recovery/deletion tests pass; active download, HLS/FFmpeg, post-processing, and AI runner cancellation tests prove terminal status and process cleanup. |
| AI model architecture is executable | Verified | Manifest discovery, path containment, source/packaged runner execution, output collection, timeout, and process-tree cancellation pass. |
| Network-restricted downloads are configurable | Verified | Independent YouTube/Twitter proxy and browser-cookie settings pass API, persistence, transient-task, and browser workflow tests. |
| A reproducible Windows installer exists | Verified | `npm.cmd run tauri:build` rebuilds the sidecar before Tauri and produces the hashed NSIS artifact. |

## External Acceptance Still Required

The code-side migration is complete, but merge readiness is not yet proven for
product/data-dependent behavior:

1. Run one authorized real download each for Douyin, Twitter/X, and Koushare.
2. Select a production AI model family and validate its concrete runner against a
   real model artifact and representative media.

These checks require URLs/content rights and a product model decision that are not
present in the repository. Until they are completed or explicitly waived, keep the
branch unmerged.
