# DouyinGo 2.0.2 Migration Verification

Date: 2026-08-24

Branch: `migration/react-tauri-sidecar`

## Regression Fixed

- yt-dlp may emit `speed=None` and `eta=None` while downloading and merging
  segmented media. YouTube and Twitter/X progress hooks now normalize missing,
  malformed, non-finite, and non-positive metrics before comparing them.
- The regression test reproduces the original 95% callback payload and verifies
  both downloaders continue with `下载中 95%` instead of raising
  `'>' not supported between instances of 'NoneType' and 'int'`.

## Verification

- `python test_backend_api.py` passes.
- `python test_core_functions.py` passes.
- `python -m compileall -q backend core test_backend_api.py` passes.
- `npm.cmd run build` passes for version 2.0.2.
- `cargo test --manifest-path src-tauri/Cargo.toml` passes (2/2).
- `npm.cmd run verify:media` passes in source and packaged modes for MKV, MP3,
  JPG, active HLS cancellation, AI manifest execution, and AI cancellation.
- `npm.cmd run tauri:build` rebuilds the sidecar and creates the 2.0.2 NSIS
  installer successfully.
- The packaged sidecar reports version 2.0.2 with Python, FFmpeg, ffprobe,
  yt-dlp, yt-dlp-ejs, and Deno available.
- The user-supplied YouTube URL `https://www.youtube.com/watch?v=COpWTc7BFro`
  completed at best quality through both source and packaged sidecars. The live
  transfer repeatedly emitted unknown speed/ETA values, including near 95%, and
  no longer failed.
- The packaged result is a 501,737,770-byte MP4 with SHA-256
  `3A258BC1FAC426BF08E3DA1B91B735BF609B6C7F3D7F4BC8642A547A4E25381C`.
  Bundled ffprobe validates 3840x2160 AV1 video, AAC audio, and a duration of
  336.689342 seconds.

## Artifacts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `src-tauri/target/release/bundle/nsis/DouyinGo_2.0.2_x64-setup.exe` | 149,350,130 | `677C6B8E7389ED80492182D9CD96C3946981BAB97A14B6B5260DAC46E8B80977` |
| `src-tauri/target/release/douyingo_desktop.exe` | 11,078,144 | `11FC916ED915D48AB67F0472F4C6131B5BB6614B07C1B34049B0C275E1AC3D82` |
| `src-tauri/binaries/douyingo-sidecar-x86_64-pc-windows-msvc.exe` | 147,032,104 | `B4236755CBFDD14A5043839212142B009EFA39BCA8A6FFE25E229B9B788DB79C` |

## Merge Gates Still Open

- Run one authorized real download each for Douyin, Twitter/X, and Koushare.
- Install and validate a product-selected AI model runner against a real model.

The migration branch remains unmerged until these external acceptance gates are
completed or explicitly waived.
