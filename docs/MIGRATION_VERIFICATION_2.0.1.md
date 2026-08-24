# DouyinGo 2.0.1 Migration Verification

Date: 2026-08-24

Branch: `migration/react-tauri-sidecar`

## Verified

- Python modules compile successfully.
- `test_backend_api.py` passes, including URL resolution, API validation,
  runtime paths, media format contracts, metadata output, persisted settings,
  AI manifest discovery, AI runner execution, SQLite task persistence, restart
  interruption recovery, and terminal-history deletion.
- `test_core_functions.py` passes.
- React/TypeScript production build passes.
- The Vite development watcher ignores generated Python/Tauri build trees and
  remains online while `cargo test` rewrites `src-tauri/target` on Windows.
- Rust sidecar path and occupied-port lifecycle tests pass (2/2).
- Browser checks pass at 1220x760 and 980x640 with no horizontal overflow,
  toolbar overlap, dialog clipping, or console errors. UI deletion was exercised
  against a recovered SQLite fixture and removed the API/database record without
  touching output files.
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
- NSIS installer build succeeds.

## Artifacts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `src-tauri/target/release/bundle/nsis/DouyinGo_2.0.1_x64-setup.exe` | 149,346,518 | `AFC52CB28B2EB4AAD1215927E9A7B44693B2579C69AE7331C1CD50CA54FA3FBD` |
| `src-tauri/target/release/douyingo_desktop.exe` | 11,104,256 | `B1541F0EB730105FA45CFF1CCD3BD423FDA24295FE28627E87CE2FD031478287` |
| `src-tauri/binaries/douyingo-sidecar-x86_64-pc-windows-msvc.exe` | 147,025,424 | `F7DDD273E1A969C207C53C066E0A7AE392B8A4A2A2D30B19825A61EF74E1901B` |

## Merge Gates Still Open

- Run one authorized real download each for Douyin, Twitter/X, and Koushare.
- Exercise the Koushare HLS path from both source and the packaged sidecar.
- Install and validate a product-selected AI model runner against a real model.

The branch should remain unmerged until these product/data-dependent gates are
explicitly accepted or completed.
