#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""签到模块"""

import re
from bs4 import BeautifulSoup
from config import Config
from utils.logger import logger


class ChaoXingSign:
    COURSE_URL = "http://mooc1-2.chaoxing.com/visit/interaction"
    ACTIVITY_URL = "https://mobilelearn.chaoxing.com/widget/pcpick/stu/index"
    PRE_SIGN_URL = "https://mobilelearn.chaoxing.com/widget/sign/pcStuSignController/preSign"
    SIGN_URL = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax"

    def __init__(self, session):
        self.session = session

    def get_course_list(self):
        try:
            r = self.session.get(self.COURSE_URL, headers=Config.DEFAULT_HEADERS, timeout=10)
            if r.status_code != 200:
                return []
            soup = BeautifulSoup(r.text, "html.parser")
            courses = []
            for li in soup.find_all("li", style=True):
                cid = li.find("input", {"name": "courseId"})
                clid = li.find("input", {"name": "classId"})
                if cid and clid:
                    link = li.find("a", target="_blank")
                    courses.append({
                        "course_id": cid.get("value"),
                        "class_id": clid.get("value"),
                        "name": link.get_text(strip=True) if link else "",
                    })
            return courses
        except Exception as e:
            logger.error(f"获取课程失败: {e}")
            return []

    def scan_all_courses_for_sign(self):
        courses = self.get_course_list()
        activities = []
        for c in courses:
            try:
                url = f"{self.ACTIVITY_URL}?courseId={c['course_id']}&jclassId={c['class_id']}"
                r = self.session.get(url, headers=Config.DEFAULT_HEADERS, timeout=10, verify=False)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                for div in soup.find_all("div", class_="Mct"):
                    onclick = div.get("onclick", "")
                    m = re.search(r"activeDetail\((\d+),", onclick)
                    if m:
                        atype = div.find("a", shape="rect")
                        atype_text = atype.get_text(strip=True) if atype else ""
                        if "签到" in atype_text:
                            activities.append({
                                "active_id": m.group(1),
                                "sign_type": atype_text,
                                "course_id": c["course_id"],
                                "class_id": c["class_id"],
                                "course_name": c["name"],
                            })
            except Exception:
                continue
        return activities

    def do_sign(self, activity):
        aid = activity["active_id"]
        cid = activity.get("class_id", "")
        coid = activity.get("course_id", "")
        stype = activity.get("sign_type", "")
        try:
            pre = f"{self.PRE_SIGN_URL}?activeId={aid}&classId={cid}&fid=&courseId={coid}"
            r = self.session.get(pre, headers=Config.DEFAULT_HEADERS, timeout=10, verify=False)
            if "签到成功" in r.text:
                return {"status": "success", "type": "pre_sign"}

            params = {
                "name": "", "activeId": aid, "uid": "", "clientip": "",
                "useragent": "", "latitude": "-1", "longitude": "-1",
                "fid": "", "appType": "15",
            }
            if "位置" in stype:
                params.update({"address": "中国", "ifTiJiao": "1"})
            r = self.session.get(self.SIGN_URL, params=params, headers=Config.DEFAULT_HEADERS, timeout=10, verify=False)
            if "success" in r.text.lower() or "签到成功" in r.text:
                return {"status": "success", "type": stype}
            return {"status": "failed", "message": r.text[:200]}
        except Exception as e:
            return {"status": "failed", "message": str(e)}
