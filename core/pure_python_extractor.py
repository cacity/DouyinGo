#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
纯 Python 实现的抖音视频提取器
不依赖 douyinVd 服务，使用正则表达式解析网页
"""

import re
import os
import json
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any
import requests
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

try:
    from thumbnail_extractor import extract_thumbnail
except ImportError:
    # 如果导入失败，定义一个空函数
    def extract_thumbnail(*args, **kwargs):
        return None


class DouyinVideoInfo:
    """抖音视频信息"""

    def __init__(self):
        self.aweme_id: Optional[str] = None
        self.comment_count: Optional[int] = None
        self.digg_count: Optional[int] = None
        self.share_count: Optional[int] = None
        self.collect_count: Optional[int] = None
        self.nickname: Optional[str] = None
        self.signature: Optional[str] = None
        self.desc: Optional[str] = None
        self.create_time: Optional[str] = None
        self.video_url: Optional[str] = None
        self.type: Optional[str] = None
        self.image_url_list: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "aweme_id": self.aweme_id,
            "comment_count": self.comment_count,
            "digg_count": self.digg_count,
            "share_count": self.share_count,
            "collect_count": self.collect_count,
            "nickname": self.nickname,
            "signature": self.signature,
            "desc": self.desc,
            "create_time": self.create_time,
            "video_url": self.video_url,
            "type": self.type,
            "image_url_list": self.image_url_list,
        }


class PurePythonExtractor:
    """纯 Python 抖音视频提取器"""

    # 正则表达式
    VIDEO_PATTERN = re.compile(r'"video":{"play_addr":{"uri":"([a-z0-9]+)"')
    VIDEO_URL_TEMPLATE = "https://www.iesdouyin.com/aweme/v1/play/?video_id=%s&ratio=1080p&line=0"

    STATS_REGEX = re.compile(r'"statistics"\s*:\s*\{([\s\S]*?)\},')
    NICKNAME_SIGNATURE_REGEX = re.compile(r'"nickname":\s*"([^"]+)",\s*"signature":\s*"([^"]+)"')
    CREATE_TIME_REGEX = re.compile(r'"create_time":\s*(\d+)')
    DESC_REGEX = re.compile(r'"desc":\s*"([^"]+)"')

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36"
        })

    def _extract_thumbnail(self, video_path: str) -> Optional[str]:
        """
        从视频中提取缩略图
        :param video_path: 视频文件路径
        :return: 缩略图路径，失败返回 None
        """
        try:
            # 生成缩略图路径
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            thumbnail_path = os.path.join(video_dir, f"{video_name}_thumb.jpg")

            # 使用 extract_thumbnail 函数
            result = extract_thumbnail(video_path, thumbnail_path, "00:00:01")
            return result

        except Exception as e:
            print(f"⚠️ 提取缩略图失败: {e}")
            return None

    def format_date(self, timestamp: int) -> str:
        """格式化时间戳"""
        date = datetime.fromtimestamp(timestamp)
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def parse_img_list(self, body: str) -> List[str]:
        """解析图片列表"""
        content = body.replace(r"\u002F", "/").replace("/", "/")

        img_regex = re.compile(
            r'{"uri":"[^\s"]+","url_list":\["(https://p\d{1,2}-sign\.douyinpic\.com/[^"]+)"'
        )
        url_ret_regex = re.compile(r'"uri":"([^\s"]+)","url_list":')

        first_urls = img_regex.findall(content)
        url_list = url_ret_regex.findall(content)
        url_set = set(url_list)

        r_list = []
        for url_set_key in url_set:
            t = next((item for item in first_urls if url_set_key in item), None)
            if t:
                r_list.append(t)

        # 过滤掉包含 /obj/ 的 URL
        filtered_r_list = [url for url in r_list if "/obj/" not in url]

        print(f"📷 找到 {len(filtered_r_list)} 张图片")
        return filtered_r_list

    def get_video_info(self, url: str) -> Optional[DouyinVideoInfo]:
        """
        获取视频信息
        :param url: 抖音视频链接
        :return: 视频信息对象
        """
        try:
            print(f"🔍 正在解析: {url}")

            # 请求页面
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            body = resp.text

            # 判断类型（视频或图片）
            video_type = "video"
            img_list: List[str] = []
            video_url = ""

            match = self.VIDEO_PATTERN.search(body)
            if not match:
                video_type = "img"
                print("📸 检测到图片类型")
            else:
                video_url = self.VIDEO_URL_TEMPLATE % match.group(1)
                print(f"🎬 检测到视频类型")
                print(f"📺 视频链接: {video_url}")

            if video_type == "img":
                img_list = self.parse_img_list(body)

            # 解析其他信息
            au_match = self.NICKNAME_SIGNATURE_REGEX.search(body)
            ct_match = self.CREATE_TIME_REGEX.search(body)
            desc_match = self.DESC_REGEX.search(body)
            stats_match = self.STATS_REGEX.search(body)

            if not stats_match:
                print("⚠️ 未找到统计信息")
                return None

            inner_content = stats_match.group(0)

            # 提取统计数据
            aweme_id_match = re.search(r'"aweme_id"\s*:\s*"([^"]+)"', inner_content)
            comment_count_match = re.search(r'"comment_count"\s*:\s*(\d+)', inner_content)
            digg_count_match = re.search(r'"digg_count"\s*:\s*(\d+)', inner_content)
            share_count_match = re.search(r'"share_count"\s*:\s*(\d+)', inner_content)
            collect_count_match = re.search(r'"collect_count"\s*:\s*(\d+)', inner_content)

            # 构建视频信息对象
            douyin_video_info = DouyinVideoInfo()
            douyin_video_info.aweme_id = aweme_id_match.group(1) if aweme_id_match else None
            douyin_video_info.comment_count = int(comment_count_match.group(1)) if comment_count_match else 0
            douyin_video_info.digg_count = int(digg_count_match.group(1)) if digg_count_match else 0
            douyin_video_info.share_count = int(share_count_match.group(1)) if share_count_match else 0
            douyin_video_info.collect_count = int(collect_count_match.group(1)) if collect_count_match else 0
            douyin_video_info.video_url = video_url
            douyin_video_info.type = video_type
            douyin_video_info.image_url_list = img_list

            if au_match:
                douyin_video_info.nickname = au_match.group(1)
                douyin_video_info.signature = au_match.group(2)

            if ct_match:
                timestamp = int(ct_match.group(1))
                douyin_video_info.create_time = self.format_date(timestamp)

            if desc_match:
                douyin_video_info.desc = desc_match.group(1)

            print(f"✅ 解析成功: {douyin_video_info.desc[:50] if douyin_video_info.desc else 'N/A'}")
            return douyin_video_info

        except Exception as e:
            print(f"❌ 解析失败: {e}")
            return None

    def download_video(self, url: str, output_dir: str, progress_callback=None) -> Dict[str, Any]:
        """
        下载视频
        :param url: 抖音视频链接
        :param output_dir: 输出目录
        :param progress_callback: 进度回调函数 callback(progress, message)
        :return: 下载结果
        """
        try:
            # 获取视频信息
            video_info = self.get_video_info(url)
            if not video_info:
                return {"success": False, "error": "无法获取视频信息"}

            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)

            downloaded_files = []

            # 下载视频
            if video_info.type == "video" and video_info.video_url:
                # 生成文件名
                title = video_info.desc or f"douyin_{video_info.aweme_id}"
                # 清理文件名中的非法字符
                title = re.sub(r'[\\/:*?"<>|]', '_', title)
                title = title[:100]  # 限制长度

                video_filename = f"{title}_no_watermark.mp4"
                video_path = os.path.join(output_dir, video_filename)

                print(f"📥 开始下载视频: {video_filename}")

                # 下载视频文件
                response = self.session.get(video_info.video_url, stream=True, timeout=30)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                last_progress = 0  # 记录上次报告的进度

                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                current_progress = int(progress)

                                # 只在进度变化至少1%时更新（避免过于频繁）
                                if current_progress != last_progress:
                                    print(f"\r📊 进度: {progress:.1f}%", end="", flush=True)

                                    # 调用进度回调
                                    if progress_callback:
                                        progress_callback(current_progress, f"下载中 {progress:.1f}%")

                                    last_progress = current_progress

                print(f"\n✅ 视频下载完成: {video_path}")

                # 提取视频缩略图
                thumbnail_path = self._extract_thumbnail(video_path)

                downloaded_files.append({
                    "type": "video",
                    "path": video_path,
                    "size": os.path.getsize(video_path),
                    "is_no_watermark": True,
                    "thumbnail": thumbnail_path  # 添加缩略图路径
                })

            # 下载图片
            elif video_info.type == "img" and video_info.image_url_list:
                title = video_info.desc or f"douyin_{video_info.aweme_id}"
                title = re.sub(r'[\\/:*?"<>|]', '_', title)
                title = title[:100]

                for i, img_url in enumerate(video_info.image_url_list, 1):
                    img_filename = f"{title}_{i}.jpg"
                    img_path = os.path.join(output_dir, img_filename)

                    print(f"📥 下载图片 {i}/{len(video_info.image_url_list)}: {img_filename}")

                    response = self.session.get(img_url, timeout=30)
                    response.raise_for_status()

                    with open(img_path, 'wb') as f:
                        f.write(response.content)

                    downloaded_files.append({
                        "type": "image",
                        "path": img_path,
                        "size": os.path.getsize(img_path)
                    })

                print(f"✅ 所有图片下载完成")

            # 保存元数据（可选，通过参数控制）
            # 注释掉，用户不需要 JSON 文件
            # metadata_filename = f"{title}_metadata.json"
            # metadata_path = os.path.join(output_dir, metadata_filename)
            #
            # with open(metadata_path, 'w', encoding='utf-8') as f:
            #     json.dump(video_info.to_dict(), f, ensure_ascii=False, indent=2)
            #
            # downloaded_files.append({
            #     "type": "metadata",
            #     "path": metadata_path,
            #     "size": os.path.getsize(metadata_path)
            # })

            return {
                "success": True,
                "video_info": video_info.to_dict(),
                "downloaded_files": downloaded_files
            }

        except Exception as e:
            print(f"❌ 下载失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}


# 测试代码
if __name__ == "__main__":
    extractor = PurePythonExtractor()

    # 测试 URL
    test_url = "https://v.douyin.com/vmyiIsBev5Y/"

    print("=" * 60)
    print("测试纯 Python 抖音视频提取器")
    print("=" * 60)

    # 获取视频信息
    info = extractor.get_video_info(test_url)
    if info:
        print("\n视频信息:")
        print(json.dumps(info.to_dict(), ensure_ascii=False, indent=2))

        # 下载视频
        # result = extractor.download_video(test_url, "test_downloads")
        # print(f"\n下载结果: {result}")
