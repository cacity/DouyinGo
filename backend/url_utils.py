from __future__ import annotations

import re
from dataclasses import dataclass

from backend.schemas import Platform, ResolvedUrl


@dataclass(frozen=True)
class PlatformPatterns:
    platform: Platform
    patterns: tuple[str, ...]
    fallback_hosts: tuple[str, ...]


PLATFORM_PATTERNS: tuple[PlatformPatterns, ...] = (
    PlatformPatterns(
        Platform.DOUYIN,
        (
            r"https?://v\.douyin\.com/[a-zA-Z0-9]+/?",
            r"https?://www\.douyin\.com/video/\d+",
            r"https?://www\.iesdouyin\.com/share/video/\d+",
            r"https?://dy\.tt/[a-zA-Z0-9]+",
        ),
        ("douyin.com", "dy.tt"),
    ),
    PlatformPatterns(
        Platform.YOUTUBE,
        (
            r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+",
            r"https?://youtu\.be/[\w-]+",
            r"https?://(?:www\.)?youtube\.com/embed/[\w-]+",
            r"https?://(?:www\.)?youtube\.com/v/[\w-]+",
            r"https?://(?:www\.)?youtube\.com/shorts/[\w-]+",
        ),
        ("youtube.com", "youtu.be"),
    ),
    PlatformPatterns(
        Platform.TWITTER,
        (
            r"https?://(?:www\.)?twitter\.com/\w+/status/\d+",
            r"https?://(?:www\.)?x\.com/\w+/status/\d+",
            r"https?://(?:www\.)?twitter\.com/i/web/status/\d+",
            r"https?://(?:www\.)?x\.com/i/web/status/\d+",
            r"https?://t\.co/[a-zA-Z0-9]+",
        ),
        ("twitter.com", "x.com", "t.co"),
    ),
    PlatformPatterns(
        Platform.KOUSHARE,
        (
            r"https?://(?:www\.)?koushare\.com/live/details/\d+\?(?:[^\s]*&)?(?:vid|videoId)=\d+[^\s]*",
            r"https?://(?:www\.)?koushare\.com/video/details/\d+[^\s]*",
            r"https?://(?:www\.)?koushare\.com/video/videodetail/\d+[^\s]*",
        ),
        ("koushare.com",),
    ),
)


def extract_url(text: str, preferred_platform: Platform | None = None) -> ResolvedUrl:
    raw = (text or "").strip()
    platforms = list(PLATFORM_PATTERNS)

    if preferred_platform and preferred_platform != Platform.UNKNOWN:
        platforms.sort(key=lambda item: item.platform != preferred_platform)

    for platform_patterns in platforms:
        for pattern in platform_patterns.patterns:
            match = re.search(pattern, raw)
            if match:
                return ResolvedUrl(
                    url=match.group(0),
                    platform=platform_patterns.platform,
                    supported=True,
                )

    first_token = raw.split()[0] if raw else ""
    if first_token.startswith(("http://", "https://")):
        detected = detect_platform(first_token)
        return ResolvedUrl(
            url=first_token,
            platform=detected,
            supported=detected != Platform.UNKNOWN,
        )

    return ResolvedUrl(url=raw, platform=Platform.UNKNOWN, supported=False)


def detect_platform(url: str) -> Platform:
    lowered = (url or "").lower()
    for platform_patterns in PLATFORM_PATTERNS:
        if any(host in lowered for host in platform_patterns.fallback_hosts):
            return platform_patterns.platform
    return Platform.UNKNOWN


def default_output_dir(platform: Platform) -> str:
    mapping = {
        Platform.DOUYIN: "douyin_downloads",
        Platform.YOUTUBE: "youtube_downloads",
        Platform.TWITTER: "twitter_downloads",
        Platform.KOUSHARE: "koushare_downloads",
    }
    return mapping.get(platform, "downloads")
