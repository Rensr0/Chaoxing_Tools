#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局配置
"""

import os


class Config:
    USER_DIR = "user"

    BASE_URL = "https://www.chaoxing.com"
    PASSPORT_URL = "https://passport2.chaoxing.com"
    I_CHAOXING_URL = "https://i.chaoxing.com"

    LOGIN_PAGE_URL = f"{PASSPORT_URL}/login?fid=&newversion=true&refer=https%3A%2F%2Fi.chaoxing.com"
    QRCODE_URL = f"{PASSPORT_URL}/createqr"
    AUTH_STATUS_URL = f"{PASSPORT_URL}/getauthstatus/v2"

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
    }

    LOGIN_TIMEOUT = 120
    CHECK_INTERVAL = 3
    QRCODE_FILENAME = "qrcode.png"

    @staticmethod
    def ensure_dirs():
        os.makedirs(Config.USER_DIR, exist_ok=True)
