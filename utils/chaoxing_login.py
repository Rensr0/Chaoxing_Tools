#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""登录模块"""

import time
import base64
import re
from bs4 import BeautifulSoup
from config import Config
from utils.logger import logger
from utils.session_manager import SessionManager


class ChaoXingLogin:
    def __init__(self):
        self.session_manager = SessionManager()
        self.session = self.session_manager.session
        self.uuid = None
        self.enc = None

    def get_login_page(self):
        try:
            r = self.session.get(Config.LOGIN_PAGE_URL)
            if r.status_code != 200:
                return False
            soup = BeautifulSoup(r.text, "html.parser")
            uuid_input = soup.find("input", {"id": "uuid"})
            if not uuid_input:
                return False
            self.uuid = uuid_input.get("value")
            enc_input = soup.find("input", {"id": "enc"})
            if enc_input:
                self.enc = enc_input.get("value")
            return True
        except Exception as e:
            logger.error(f"获取登录页失败: {e}")
            return False

    def get_qrcode(self):
        if not self.uuid:
            return False
        try:
            r = self.session.get(f"{Config.QRCODE_URL}?uuid={self.uuid}&fid=-1")
            if r.status_code == 200:
                with open(Config.QRCODE_FILENAME, "wb") as f:
                    f.write(r.content)
                logger.info(f"二维码已保存: {Config.QRCODE_FILENAME}")
                return True
            return False
        except Exception as e:
            logger.error(f"获取二维码失败: {e}")
            return False

    def check_login_status(self):
        if not self.uuid:
            return False
        logger.info("等待扫码登录...")
        start = time.time()
        while time.time() - start < Config.LOGIN_TIMEOUT:
            try:
                r = self.session.post(Config.AUTH_STATUS_URL, data={
                    "enc": self.enc, "uuid": self.uuid,
                    "doubleFactorLogin": "0", "forbidotherlogin": "0"
                }, allow_redirects=False)
                if r.status_code == 200:
                    result = r.json()
                    if result.get("status"):
                        self.session_manager.init_domains()
                        return True
                    if result.get("type") == "4":
                        logger.info("已扫码，请在APP确认")
                    if result.get("type") == "2":
                        logger.error("二维码已过期")
                        return False
            except Exception:
                pass
            time.sleep(Config.CHECK_INTERVAL)
        logger.error("登录超时")
        return False

    def login(self):
        self.session.get(Config.BASE_URL)
        if not self.get_login_page():
            return False
        if not self.get_qrcode():
            return False
        return self.check_login_status()

    def login_with_password(self, username, password, schoolid=""):
        try:
            url = f"{Config.PASSPORT_URL}/api/login?name={username}&pwd={password}&schoolid={schoolid}&verify=0"
            r = self.session.get(url, headers=Config.DEFAULT_HEADERS, timeout=10)
            if r.status_code != 200:
                logger.error("登录请求失败")
                return False
            try:
                result = r.json()
                if not result.get("result", False):
                    logger.error(f"登录失败: {result.get('errorMsg', '未知错误')}")
                    return False
            except ValueError:
                pass
            cookie = r.headers.get("Set-Cookie")
            if not cookie:
                logger.error("未获取到Cookie")
                return False
            self.session_manager.parse_and_set_cookie(cookie)
            self.session_manager.init_domains()
            return True
        except Exception as e:
            logger.error(f"登录出错: {e}")
            return False

    def login_with_cookie(self, cookies):
        try:
            self.session_manager.set_cookies(cookies)
            r = self.session.get(Config.I_CHAOXING_URL, allow_redirects=True)
            if r.status_code == 200 and any(k in r.text for k in ["个人空间", "课程", "应用中心"]):
                return True
            return False
        except Exception:
            return False
