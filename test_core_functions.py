#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试核心功能（不需要GUI环境）
"""

import sys
import os
import re

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.youtube_downloader import YouTubeDownloader
from core.twitter_downloader import TwitterDownloader


def test_url_recognition():
    """测试URL识别功能"""
    print("=" * 50)
    print("测试 URL 识别功能")
    print("=" * 50)

    youtube_downloader = YouTubeDownloader()
    twitter_downloader = TwitterDownloader()

    test_urls = {
        "YouTube": [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.douyin.com/video/123456"  # 非YouTube链接
        ],
        "Twitter/X": [
            "https://twitter.com/user/status/1234567890",
            "https://x.com/user/status/1234567890",
            "https://www.twitter.com/i/web/status/1234567890",
            "https://www.x.com/i/web/status/1234567890",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # 非Twitter链接
        ]
    }

    for platform, urls in test_urls.items():
        print(f"\n{platform} URL 测试:")
        for url in urls:
            if platform == "YouTube":
                is_valid = youtube_downloader.is_youtube_url(url)
            else:
                is_valid = twitter_downloader.is_twitter_url(url)

            print(f"  {url}")
            print(f"    识别结果: {'✓' if is_valid else '✗'}")


def test_url_extraction():
    """测试URL提取功能"""
    print("\n" + "=" * 50)
    print("测试 URL 提取功能")
    print("=" * 50)

    # 定义URL提取正则表达式（从主窗口代码复制）
    def extract_youtube_url(text: str) -> str:
        patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://youtu\.be/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/embed/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/v/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        text = text.strip()
        if text.startswith('http') and ('youtube.com' in text or 'youtu.be' in text):
            return text.split()[0]

        return text

    def extract_twitter_url(text: str) -> str:
        patterns = [
            r'https?://(?:www\.)?twitter\.com/\w+/status/\d+',
            r'https?://(?:www\.)?x\.com/\w+/status/\d+',
            r'https?://(?:www\.)?twitter\.com/i/web/status/\d+',
            r'https?://(?:www\.)?x\.com/i/web/status/\d+',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        text = text.strip()
        if text.startswith('http') and ('twitter.com' in text or 'x.com' in text):
            return text.split()[0]

        return text

    def extract_douyin_url(text: str) -> str:
        patterns = [
            r'https?://v\.douyin\.com/[a-zA-Z0-9]+/?',
            r'https?://www\.douyin\.com/video/\d+',
            r'https?://www\.iesdouyin\.com/share/video/\d+',
            r'https?://dy\.tt/[a-zA-Z0-9]+'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        text = text.strip()
        if text.startswith('http') and ('douyin.com' in text or 'dy.tt' in text):
            return text.split()[0]

        return text

    test_cases = [
        {
            "platform": "YouTube",
            "text": "看看这个YouTube视频 https://www.youtube.com/watch?v=dQw4w9WgXcQ 很有趣",
            "extractor": extract_youtube_url
        },
        {
            "platform": "YouTube",
            "text": "https://youtu.be/dQw4w9WgXcQ 这个也不错",
            "extractor": extract_youtube_url
        },
        {
            "platform": "Twitter/X",
            "text": "分享一个推文 https://twitter.com/user/status/1234567890 真不错",
            "extractor": extract_twitter_url
        },
        {
            "platform": "Twitter/X",
            "text": "看看这个 https://x.com/user/status/1234567890",
            "extractor": extract_twitter_url
        },
        {
            "platform": "抖音",
            "text": "抖音视频 https://v.douyin.com/abcd1234/ 真好看",
            "extractor": extract_douyin_url
        },
        {
            "platform": "抖音",
            "text": "这个也不错 https://www.douyin.com/video/1234567890",
            "extractor": extract_douyin_url
        }
    ]

    for case in test_cases:
        platform = case["platform"]
        text = case["text"]
        extractor = case["extractor"]

        extracted = extractor(text)
        print(f"\n平台: {platform}")
        print(f"原始文本: {text}")
        print(f"提取的URL: {extracted}")
        print(f"提取成功: {'✓' if extracted and 'http' in extracted else '✗'}")


def test_downloader_initialization():
    """测试下载器初始化"""
    print("\n" + "=" * 50)
    print("测试下载器初始化")
    print("=" * 50)

    try:
        # 测试YouTube下载器
        youtube_downloader = YouTubeDownloader("test_youtube_downloads")
        print("✓ YouTube下载器初始化成功")
        print(f"  下载目录: {youtube_downloader.download_dir}")

        # 测试Twitter下载器
        twitter_downloader = TwitterDownloader("test_twitter_downloads")
        print("✓ Twitter下载器初始化成功")
        print(f"  下载目录: {twitter_downloader.download_dir}")

        # 检查目录是否创建
        if os.path.exists("test_youtube_downloads"):
            print("✓ YouTube下载目录创建成功")
        if os.path.exists("test_twitter_downloads"):
            print("✓ Twitter下载目录创建成功")

    except Exception as e:
        print(f"✗ 下载器初始化失败: {e}")


def test_format_selection():
    """测试格式选择功能"""
    print("\n" + "=" * 50)
    print("测试格式选择功能")
    print("=" * 50)

    youtube_downloader = YouTubeDownloader()
    twitter_downloader = TwitterDownloader()

    qualities = ["best", "worst", "1080p", "720p", "480p"]

    print("YouTube格式选择:")
    for quality in qualities:
        format_selector = youtube_downloader._get_format_selector(quality)
        print(f"  {quality}: {format_selector}")

    print("\nTwitter/X格式选择:")
    for quality in qualities:
        format_selector = twitter_downloader._get_format_selector(quality)
        print(f"  {quality}: {format_selector}")


def main():
    """主函数"""
    print("VideoGo 核心功能测试")
    print("=" * 60)
    print("注意：此测试不需要GUI环境")
    print()

    # 测试URL识别功能
    test_url_recognition()

    # 测试URL提取功能
    test_url_extraction()

    # 测试下载器初始化
    test_downloader_initialization()

    # 测试格式选择功能
    test_format_selection()

    print("\n" + "=" * 60)
    print("核心功能测试完成！")
    print()
    print("下一步:")
    print("1. 在GUI环境中运行完整程序")
    print("2. 测试实际的下载功能")
    print("3. 验证用户界面的交互")
    print()
    print("注意：实际下载功能需要网络连接和有效的URL")


if __name__ == "__main__":
    main()