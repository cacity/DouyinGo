# DouyinGo 2.0.1 Migration Verification

Date: 2026-08-24

Branch: `migration/react-tauri-sidecar`

## Verified

- Python modules compile successfully.
- `test_backend_api.py` passes, including URL resolution, API validation,
  runtime paths, media format contracts, metadata output, persisted settings,
  AI manifest discovery, AI runner execution, SQLite task persistence, restart
  interruption recovery, terminal-history deletion, loopback-only CORS,
  model-directory creation, proxy validation, browser-cookie selection, and
  transient network-option cleanup. Active cancellation remains `cancelled`,
  clears its error field, and promptly stops FFmpeg post-processing and AI runner
  process trees; AI timeout also stops its runner process.
- `test_core_functions.py` passes.
- React/TypeScript production build passes.
- The Vite development watcher ignores generated Python/Tauri build trees and
  remains online while `cargo test` rewrites `src-tauri/target` on Windows.
- Rust sidecar path and occupied-port lifecycle tests pass (2/2).
- The production Tauri CSP permits only application assets, IPC, and loopback
  sidecar connections. The release WebView renders normally with the CSP active.
- Browser checks pass at 1220x760 and 980x640 with no horizontal overflow,
  toolbar overlap, dialog clipping, or console errors. UI deletion was exercised
  against a recovered SQLite fixture and removed the API/database record without
  touching output files. The 980x640 settings workflow also persisted and cleared
  independent YouTube/Twitter proxy and browser-cookie selections.
- Download history persists in the application-data `jobs.sqlite3` database.
  The newest 500 terminal records are retained; unfinished records recover as
  cancelled after restart and are never resumed implicitly.
- The packaged sidecar reports version 2.0.1 and bundled FFmpeg, ffprobe, Deno,
  yt-dlp 2026.08.19, and yt-dlp-ejs 0.8.0.
- Source YouTube cover (`JPG`) and audio (`M4A`) downloads succeed for the user
  supplied URL `https://www.youtube.com/watch?v=k7nje82oYhI`.
- The packaged API downloads the same URL at best quality to a 61,108,571-byte
  MP4 and writes a 169,405-byte metadata JSON file.
- Bundled ffprobe validates the packaged result as 3840x2160 AV1 video plus AAC
  audio with a duration of 209.002812 seconds.
- The deterministic local Koushare HLS contract passes through both source and
  packaged sidecars: MKV is 172,488 bytes with audio/video streams, MP3 is 10,083
  bytes with an audio stream, and JPG is 11,304 bytes with an image stream.
  Metadata output is required for every case, and the packaged run confirms
  bundled FFmpeg, ffprobe, and Deno. Both modes also cancel an active slow HLS
  transfer as `cancelled`, remove the partial MP4, execute an AI manifest runner,
  and cancel a slow AI runner with verified process cleanup.
- A release-desktop smoke test passes while port 8765 is occupied: Tauri selects
  port 8563, starts sidecar 2.0.1, reports bundled tools, and automatically stops
  the packaged sidecar after the desktop process exits.
- A second release smoke test verifies the CSP-enabled WebView, online sidecar,
  complete tool inventory, normal window close, and full PyInstaller process-tree
  shutdown.
- The canonical `npm.cmd run tauri:build` command first rebuilds the sidecar,
  requires FFmpeg and ffprobe, then produces the NSIS installer successfully.

## Artifacts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `src-tauri/target/release/bundle/nsis/DouyinGo_2.0.1_x64-setup.exe` | 149,351,479 | `8E50CE880DC046F678628D21880A830758255DF3EA1E48953463038A8EBEE5F2` |
| `src-tauri/target/release/douyingo_desktop.exe` | 11,078,144 | `A464C08C46A52249A09BFB33F8812224FB96737E800656E87CA851F9ED574319` |
| `src-tauri/binaries/douyingo-sidecar-x86_64-pc-windows-msvc.exe` | 147,031,465 | `EAE5B48CE29BE132BB39FF32A2B277A2C66C31255E6E23BA8DE6A296A2657D6A` |

## Merge Gates Still Open

- Run one authorized real download each for Douyin, Twitter/X, and Koushare.
- Install and validate a product-selected AI model runner against a real model.

The branch should remain unmerged until these product/data-dependent gates are
explicitly accepted or completed.
