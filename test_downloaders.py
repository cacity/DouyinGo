#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试下载器功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.youtube_downloader import YouTubeDownloader
from core.twitter_downloader import TwitterDownloader


def test_youtube_downloader():
    """测试YouTube下载器"""
    print("=" * 50)
    print("测试 YouTube 下载器")
    print("=" * 50)

    downloader = YouTubeDownloader()

    # 测试URL识别
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.douyin.com/video/123456"  # 非YouTube链接
    ]

    for url in test_urls:
        is_youtube = downloader.is_youtube_url(url)
        print(f"URL: {url}")
        print(f"是否为YouTube链接: {is_youtube}")
        print()

    # 测试获取视频信息（需要网络，可能会失败）
    try:
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        print(f"测试获取视频信息: {test_url}")
        info = downloader.get_video_info(test_url)
        if info:
            print("视频信息获取成功:")
            print(f"  标题: {info.get('title', 'N/A')}")
            print(f"  时长: {info.get('duration_string', 'N/A')}")
            print(f"  上传者: {info.get('uploader', 'N/A')}")
        else:
            print("无法获取视频信息（可能需要网络或YouTube限制）")
    except Exception as e:
        print(f"获取视频信息时出错: {e}")

    print()


def test_twitter_downloader():
    """测试Twitter下载器"""
    print("=" * 50)
    print("测试 Twitter/X 下载器")
    print("=" * 50)

    downloader = TwitterDownloader()

    # 测试URL识别
    test_urls = [
        "https://twitter.com/user/status/1234567890",
        "https://x.com/user/status/1234567890",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # 非Twitter链接
    ]

    for url in test_urls:
        is_twitter = downloader.is_twitter_url(url)
        print(f"URL: {url}")
        print(f"是否为Twitter/X链接: {is_twitter}")
        print()

    # 测试从文本提取URL
    test_texts = [
        "看看这个视频 https://twitter.com/user/status/1234567890 很棒",
        "分享一个推文 https://x.com/user/status/1234567890",
        "没有链接的文本"
    ]

    for text in test_texts:
        extracted_url = downloader.extract_twitter_url_from_text(text)
        print(f"文本: {text}")
        print(f"提取的URL: {extracted_url}")
        print()

    print()


def test_url_extraction():
    """测试URL提取功能"""
    print("=" * 50)
    print("测试 URL 提取功能")
    print("=" * 50)

    # 导入主窗口模块的URL提取函数
    from ui.main_window import MainWindow

    # 创建临时主窗口实例来测试URL提取
    main_window = MainWindow()

    test_cases = [
        {
            "platform": "youtube",
            "text": "看看这个YouTube视频 https://www.youtube.com/watch?v=dQw4w9WgXcQ 很有趣",
            "expected": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        },
        {
            "platform": "twitter",
            "text": "分享一个推文 https://twitter.com/user/status/1234567890",
            "expected": "https://twitter.com/user/status/1234567890"
        },
        {
            "platform": "douyin",
            "text": "抖音视频 https://v.douyin.com/abcd1234/ 真好看",
            "expected": "https://v.douyin.com/abcd1234/"
        }
    ]

    for case in test_cases:
        platform = case["platform"]
        text = case["text"]
        expected = case["expected"]

        extracted = main_window.extract_url_by_platform(text, platform)
        is_valid = main_window.validate_platform_url(extracted, platform)

        print(f"平台: {platform}")
        print(f"原始文本: {text}")
        print(f"提取的URL: {extracted}")
        print(f"预期URL: {expected}")
        print(f"URL验证: {'✓' if is_valid else '✗'}")
        print(f"提取结果: {'✓' if extracted == expected else '✗'}")
        print()


def main():
    """主函数"""
    print("VideoGo 下载器功能测试")
    print("=" * 60)
    print()

    # 测试YouTube下载器
    test_youtube_downloader()

    # 测试Twitter下载器
    test_twitter_downloader()

    # 测试URL提取功能
    test_url_extraction()

    print("=" * 60)
    print("测试完成！")
    print()
    print("注意事项:")
    print("1. 视频信息获取需要网络连接")
    print("2. 某些地区可能需要代理才能访问YouTube/Twitter")
    print("3. 实际下载功能请在GUI环境中测试")


if __name__ == "__main__":
    main()