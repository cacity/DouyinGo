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
  transient network-option cleanup.
- `test_core_functions.py` passes.
- React/TypeScript production build passes.
- The Vite development watcher ignores generated Python/Tauri build trees and
  remains online while `cargo test` rewrites `src-tauri/target` on Windows.
- Rust sidecar path and occupied-port lifecycle tests pass (2/2).
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
  bundled FFmpeg, ffprobe, and Deno.
- A release-desktop smoke test passes while port 8765 is occupied: Tauri selects
  port 8563, starts sidecar 2.0.1, reports bundled tools, and automatically stops
  the packaged sidecar after the desktop process exits.
- NSIS installer build succeeds.

## Artifacts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `src-tauri/target/release/bundle/nsis/DouyinGo_2.0.1_x64-setup.exe` | 149,346,279 | `01D15100C70F2DF660184D1B00A2D3C710A56CACC68D7A935AE01349E6B87DD0` |
| `src-tauri/target/release/douyingo_desktop.exe` | 11,104,768 | `5995ED36D9C5A72DEED3D19CFC24D851606713016186BA2B9D81F654851DBD73` |
| `src-tauri/binaries/douyingo-sidecar-x86_64-pc-windows-msvc.exe` | 147,026,407 | `C3CC698EE283357A594CF8A4F1739EB05AA17881B330C7F168CC113AD67BB9F3` |

## Merge Gates Still Open

- Run one authorized real download each for Douyin, Twitter/X, and Koushare.
- Install and validate a product-selected AI model runner against a real model.

The branch should remain unmerged until these product/data-dependent gates are
explicitly accepted or completed.
