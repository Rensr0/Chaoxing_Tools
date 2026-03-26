#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日志"""

from datetime import datetime


class Logger:
    def info(self, msg):
        print(f"[{datetime.now():%H:%M:%S}] {msg}")

    def error(self, msg):
        print(f"[{datetime.now():%H:%M:%S}] ❌ {msg}")

    def warning(self, msg):
        print(f"[{datetime.now():%H:%M:%S}] ⚠️  {msg}")

    def success(self, msg):
        print(f"[{datetime.now():%H:%M:%S}] ✅ {msg}")


logger = Logger()
