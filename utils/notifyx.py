#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""消息推送模块"""

import requests
from utils.logger import logger


class NotifyX:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = f"https://www.notifyx.cn/api/v1/send/{api_key}"

    def send(self, title, content, description=None):
        try:
            payload = {"title": title, "content": content}
            if description:
                payload["description"] = description
            r = requests.post(self.api_url, json=payload, timeout=10)
            if r.status_code in (200, 202) and r.json().get("status") == "queued":
                logger.info(f"通知已发送: {title}")
                return True
            logger.error(f"通知发送失败: {r.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"通知出错: {e}")
            return False

    def send_work_notification(self, urgent, unsubmitted):
        parts = []
        if urgent:
            parts.append(f"🔴 **紧急作业** ({len(urgent)}个)<br><br>")
            for i, w in enumerate(urgent, 1):
                parts.append(f"{i}. {w['name']}<br>&nbsp;&nbsp;📚 {w['course']}<br>&nbsp;&nbsp;⏰ {w['remaining_time']}<br><br>")
        if unsubmitted:
            parts.append(f"📝 **未提交** ({len(unsubmitted)}个)<br><br>")
            for i, w in enumerate(unsubmitted, 1):
                parts.append(f"{i}. {w['name']}<br>&nbsp;&nbsp;📚 {w['course']}<br>&nbsp;&nbsp;⏰ {w['remaining_time']}<br><br>")
        title = f"🔴 {len(urgent)}个紧急作业" if urgent else f"📝 {len(unsubmitted)}个未提交作业"
        return self.send(title, "".join(parts))

    def send_sign_result_notification(self, course, sign_type, success):
        icon = "✅" if success else "❌"
        status = "签到成功" if success else "签到失败"
        return self.send(f"{icon} {status} - {course}", f"📚 {course}<br>📌 {sign_type}<br>{icon} {status}")

    def send_upcoming_lesson_notification(self, lesson):
        content = f"📚 {lesson['name']}<br>👨‍🏫 {lesson['teacher']}<br>📍 {lesson['location']}<br>⏰ {lesson['time_range']}"
        return self.send(f"🔔 {lesson['name']} 即将开始", content)

    def send_exam_notification(self, exams):
        parts = [f"📋 **考试/测验** ({len(exams)}个)<br><br>"]
        for i, e in enumerate(exams, 1):
            parts.append(f"{i}. {e['name']}")
            if e.get("status"):
                parts.append(f"<br>&nbsp;&nbsp;📌 {e['status']}")
            parts.append("<br><br>")
        return self.send(f"📋 {len(exams)}个考试/测验", "".join(parts))
