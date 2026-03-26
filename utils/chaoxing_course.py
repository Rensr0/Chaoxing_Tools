#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""课程与考试模块"""

from bs4 import BeautifulSoup
from config import Config
from utils.logger import logger


class ChaoXingCourse:
    EXAM_URL = "https://mooc1-api.chaoxing.com/mooc-ans/examList"

    def __init__(self, session):
        self.session = session

    def get_exam_list(self):
        try:
            r = self.session.get(self.EXAM_URL, headers=Config.DEFAULT_HEADERS, timeout=10)
            if r.status_code != 200:
                return []
            soup = BeautifulSoup(r.text, "html.parser")
            exams = []
            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    exams.append({
                        "name": cells[0].get_text(strip=True),
                        "status": cells[1].get_text(strip=True),
                        "detail": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                    })
            return [e for e in exams if e["name"]]
        except Exception as e:
            logger.error(f"获取考试列表失败: {e}")
            return []
