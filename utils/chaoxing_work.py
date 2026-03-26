#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""作业模块"""

import re
from bs4 import BeautifulSoup
from config import Config
from utils.logger import logger


class ChaoXingWork:
    WORK_URL = "https://mooc1-api.chaoxing.com/mooc-ans/work/stu-work"

    def __init__(self, session):
        self.session = session

    def get_work_list(self):
        try:
            r = self.session.get(self.WORK_URL, headers=Config.DEFAULT_HEADERS, timeout=10)
            if r.status_code != 200:
                return []
            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.find_all("li", onclick="goTask(this);")
            return [w for w in (self._parse_item(i) for i in items) if w]
        except Exception as e:
            logger.error(f"获取作业失败: {e}")
            return []

    def _parse_item(self, item):
        try:
            url = item.get("data", "")
            if url and url.startswith("/"):
                url = f"https://mooc1-api.chaoxing.com{url}"
            name_tag = item.find("p", {"aria-hidden": "true"})
            name = name_tag.text.strip() if name_tag else "未知"
            spans = item.find_all("span", {"aria-hidden": "true"})
            status = spans[0].text.strip() if spans else "未知"
            course = spans[1].text.strip() if len(spans) > 1 else "未知"
            time_tag = item.find("span", class_="fr")
            remaining = time_tag.text.strip() if time_tag else ""
            return {"name": name, "status": status, "course": course,
                    "remaining_time": remaining, "url": url,
                    "is_urgent": self._is_urgent(remaining)}
        except Exception:
            return None

    def _is_urgent(self, text):
        try:
            m = re.search(r"剩余(\d+)小时", text)
            if m:
                return int(m.group(1)) < 24
            return "分钟" in text
        except Exception:
            return False

    def get_hours_remaining(self, text):
        try:
            m = re.search(r"剩余(\d+)小时", text)
            if m:
                return int(m.group(1))
            m = re.search(r"剩余(\d+)分钟", text)
            if m:
                return int(m.group(1)) / 60
            return None
        except Exception:
            return None

    def get_unsubmitted_works(self, works):
        return [w for w in works if w["status"] == "未提交"]

    def get_urgent_works(self, works):
        return [w for w in works if w["is_urgent"]]
