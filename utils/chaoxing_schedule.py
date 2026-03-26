#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""课表模块"""

from datetime import datetime, timedelta
from config import Config
from utils.logger import logger


class ChaoXingSchedule:
    SCHEDULE_URL = "https://kb.chaoxing.com/curriculum/getMyLessons"

    def __init__(self, session):
        self.session = session
        self.data = None
        self.time_config = []

    def get_schedule(self):
        try:
            r = self.session.get(self.SCHEDULE_URL, headers=Config.DEFAULT_HEADERS, timeout=10)
            if r.status_code != 200:
                return None
            data = r.json()
            if data.get("result") != 1:
                return None
            self.data = data.get("data", {})
            curriculum = self.data.get("curriculum", {})
            self.time_config = curriculum.get("lessonTimeConfigArray", [])
            return self.data
        except Exception as e:
            logger.error(f"获取课表失败: {e}")
            return None

    def get_today_lessons(self):
        if not self.data:
            self.get_schedule()
        if not self.data:
            return []
        today = datetime.now()
        dow = today.weekday() + 1
        current_week = self.data.get("curriculum", {}).get("currentWeek", 0)
        lessons = []
        for l in self.data.get("lessonArray", []):
            if l.get("dayOfWeek") == dow and self._in_week(l.get("weeks", ""), current_week):
                info = self._parse_lesson(l)
                if info:
                    lessons.append(info)
        lessons.sort(key=lambda x: x["begin_number"])
        return lessons

    def get_upcoming_lessons(self, minutes_ahead=20):
        if not self.data:
            self.get_schedule()
        if not self.data:
            return []
        now = datetime.now()
        dow = now.weekday() + 1
        current_week = self.data.get("curriculum", {}).get("currentWeek", 0)
        result = []
        for l in self.data.get("lessonArray", []):
            if l.get("dayOfWeek") == dow and self._in_week(l.get("weeks", ""), current_week):
                info = self._parse_lesson(l)
                if info:
                    diff = (info["start_time"] - now).total_seconds() / 60
                    if 0 < diff <= minutes_ahead:
                        result.append(info)
        return sorted(result, key=lambda x: x["start_time"])

    def _in_week(self, weeks, current):
        try:
            if "," in weeks:
                return current in [int(w.strip()) for w in weeks.split(",")]
            if "-" in weeks:
                s, e = [int(w.strip()) for w in weeks.split("-")]
                return s <= current <= e
            return int(weeks.strip()) == current
        except Exception:
            return False

    def _parse_lesson(self, lesson):
        try:
            begin = lesson.get("beginNumber", 1)
            length = lesson.get("length", 1)
            start, end = self._get_time(begin, length)
            return {
                "name": lesson.get("name", "未知"),
                "teacher": lesson.get("teacherName", ""),
                "location": lesson.get("location", ""),
                "begin_number": begin,
                "start_time": start,
                "end_time": end,
                "time_range": f"{start:%H:%M}-{end:%H:%M}",
                "course_no": lesson.get("courseNo", ""),
            }
        except Exception:
            return None

    def _get_time(self, begin, length):
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if not self.time_config or begin > len(self.time_config):
            s = today.replace(hour=8)
            return s, s + timedelta(minutes=length * 45)
        sh, sm = map(int, self.time_config[begin - 1].split("-")[0].split(":"))
        start = today.replace(hour=sh, minute=sm)
        last = self.time_config[begin + length - 2]
        eh, em = map(int, last.split("-")[1].split(":"))
        return start, today.replace(hour=eh, minute=em)
