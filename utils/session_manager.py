#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""会话管理"""

import requests
from config import Config


class SessionManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(Config.DEFAULT_HEADERS)

    def set_cookies(self, cookies):
        self.session.cookies.clear()
        for name, value in cookies.items():
            self.session.cookies.set(name=name, value=value, domain=".chaoxing.com", path="/")

    def parse_and_set_cookie(self, cookie_header):
        self.session.cookies.clear()
        for cookie in cookie_header.split(","):
            parts = cookie.strip().split(";")
            if not parts:
                continue
            nv = parts[0].strip()
            if "=" in nv:
                name, value = nv.split("=", 1)
                self.session.cookies.set(name=name.strip(), value=value.strip(), domain=".chaoxing.com", path="/")

    def get_cookies_dict(self):
        return {c.name: c.value for c in self.session.cookies}

    def init_domains(self):
        try:
            self.session.get(Config.I_CHAOXING_URL, allow_redirects=True)
        except Exception:
            pass
