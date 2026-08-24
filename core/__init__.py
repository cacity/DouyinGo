#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
核心功能模块
"""

__all__ = [
    'DownloadManager',
    'DownloadWorker',
    'KoushareDownloader'
]


def __getattr__(name):
    if name in {'DownloadManager', 'DownloadWorker'}:
        from core.downloader import DownloadManager, DownloadWorker

        return {'DownloadManager': DownloadManager, 'DownloadWorker': DownloadWorker}[name]

    if name == 'KoushareDownloader':
        from core.koushare_downloader import KoushareDownloader

        return KoushareDownloader

    raise AttributeError(name)
