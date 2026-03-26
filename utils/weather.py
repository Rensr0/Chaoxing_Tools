#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""天气模块（30分钟缓存）"""

import time
import requests
from utils.logger import logger


class Weather:
    _cache = {}
    TTL = 1800

    def __init__(self, location):
        self.location = location
        self.data = None

    def get_weather(self):
        cached = self._cache.get(self.location)
        if cached and time.time() - cached["ts"] < self.TTL:
            self.data = cached["data"]
            return self.data
        try:
            r = requests.get(f"https://60s.viki.moe/v2/weather?query={self.location}", timeout=10)
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == 200:
                    self.data = d.get("data", {})
                    self._cache[self.location] = {"data": self.data, "ts": time.time()}
                    return self.data
        except Exception as e:
            logger.error(f"获取天气失败: {e}")
        return None

    def get_summary(self):
        if not self.data:
            return None
        w = self.data.get("weather", {})
        aq = self.data.get("air_quality", {})
        return {
            "condition": w.get("condition", ""),
            "temperature": w.get("temperature", 0),
            "aqi": aq.get("aqi", 0),
            "quality": aq.get("quality", ""),
        }

    @staticmethod
    def get_emoji(condition):
        for key, emoji in {"晴": "☀️", "多云": "⛅", "阴": "☁️", "雨": "🌧️", "雪": "❄️", "雾": "🌫️"}.items():
            if key in condition:
                return emoji
        return "🌤️"

    @staticmethod
    def get_aqi_emoji(aqi):
        if aqi <= 50:
            return "🟢"
        if aqi <= 100:
            return "🟡"
        if aqi <= 150:
            return "🟠"
        return "🔴"
