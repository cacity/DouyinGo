#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视频缩略图提取工具
"""

import os
import subprocess


def _find_tool(name: str) -> str:
    try:
        from backend.ffmpeg_tools import find_ffmpeg, find_ffprobe

        if name == "ffmpeg":
            return find_ffmpeg() or name
        if name == "ffprobe":
            return find_ffprobe() or name
    except Exception:
        return name
    return name


def extract_thumbnail(video_path: str, output_path: str = None, time_position: str = "00:00:01") -> str:
    """
    从视频中提取缩略图

    :param video_path: 视频文件路径
    :param output_path: 输出图片路径（可选，默认为视频同目录）
    :param time_position: 提取帧的时间位置，默认第1秒
    :return: 缩略图路径，失败返回 None
    """
    try:
        # 生成输出路径
        if not output_path:
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(video_dir, f"{video_name}_thumb.jpg")

        # 检查 ffmpeg 是否可用
        try:
            subprocess.run(
                [_find_tool("ffmpeg"), "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠️ ffmpeg 未安装或不可用，无法提取缩略图")
            return None

        # 使用 ffmpeg 提取缩略图
        # -ss: 指定时间位置
        # -i: 输入文件
        # -vframes 1: 只提取一帧
        # -q:v 2: 质量（1-31，越小质量越好）
        # -vf scale=120:68: 缩放到指定大小
        cmd = [
            _find_tool("ffmpeg"),
            "-ss", time_position,
            "-i", video_path,
            "-vframes", "1",
            "-vf", "scale=120:68",
            "-q:v", "2",
            "-y",  # 覆盖已存在的文件
            output_path
        ]

        print(f"📸 正在提取缩略图...")

        # 执行命令
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )

        # 检查是否成功
        if result.returncode == 0 and os.path.exists(output_path):
            print(f"✅ 缩略图提取成功: {output_path}")
            return output_path
        else:
            print(f"⚠️ 缩略图提取失败")
            return None

    except Exception as e:
        print(f"❌ 提取缩略图异常: {e}")
        return None


def get_video_duration(video_path: str) -> float:
    """
    获取视频时长（秒）

    :param video_path: 视频文件路径
    :return: 视频时长（秒），失败返回 0
    """
    try:
        # 使用 ffprobe 获取视频时长
        cmd = [
            _find_tool("ffprobe"),
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )

        if result.returncode == 0:
            duration_str = result.stdout.decode('utf-8').strip()
            try:
                duration = float(duration_str)
                return duration
            except ValueError:
                return 0
        return 0
    except Exception as e:
        print(f"⚠️ 获取视频时长失败: {e}")
        return 0


def format_duration(seconds: float) -> str:
    """
    格式化时长为 MM:SS 或 HH:MM:SS 格式

    :param seconds: 秒数
    :return: 格式化后的时长字符串
    """
    if seconds <= 0:
        return "未知"

    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def check_ffmpeg_available() -> bool:
    """
    检查 ffmpeg 是否可用

    :return: True 如果可用，否则 False
    """
    try:
        result = subprocess.run(
            [_find_tool("ffmpeg"), "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


if __name__ == "__main__":
    # 测试
    print("检查 ffmpeg 是否可用:")
    if check_ffmpeg_available():
        print("✅ ffmpeg 可用")
    else:
        print("❌ ffmpeg 不可用")
