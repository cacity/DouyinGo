# DouyinGo 2.0.1 Migration Verification

Date: 2026-08-24

Branch: `migration/react-tauri-sidecar`

## Verified

- Python modules compile successfully.
- `test_backend_api.py` passes, including URL resolution, API validation,
  runtime paths, media format contracts, metadata output, persisted settings,
  AI manifest discovery, and AI runner execution.
- `test_core_functions.py` passes.
- React/TypeScript production build passes.
- Rust sidecar path and occupied-port lifecycle tests pass (2/2).
- Browser checks pass at 1220x760 and 980x640 with no horizontal overflow,
  toolbar overlap, or console errors.
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
| `src-tauri/target/release/bundle/nsis/DouyinGo_2.0.1_x64-setup.exe` | 149,338,552 | `4E8185E7958AE1B0EBE3C049E4BF59C77B8839F7C0AFDA8CF3E91EB4C65364B9` |
| `src-tauri/target/release/douyingo_desktop.exe` | 11,104,256 | `5EE1AB4D92F8DBF02DF401179F05EAB7F34F3BADDE9DB3C360A13919AFC623C7` |
| `src-tauri/binaries/douyingo-sidecar-x86_64-pc-windows-msvc.exe` | 147,017,868 | `C4A592038C0BF462647890BBDCF2BCBC989F0F2F5EE3C72A5F3CDE255E2CA84A` |

## Merge Gates Still Open

- Run one authorized real download each for Douyin, Twitter/X, and Koushare.
- Exercise the Koushare HLS path from both source and the packaged sidecar.
- Install and validate a product-selected AI model runner against a real model.
- Decide whether in-memory task history is acceptable for 2.0.1 or SQLite
  persistence is required before merge.

The branch should remain unmerged until these product/data-dependent gates are
explicitly accepted or completed.
