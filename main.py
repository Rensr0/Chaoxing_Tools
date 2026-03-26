#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习通自动化工具 - 一键启动，持续运行
"""

import os
import sys
import time
import json
import signal

from config import Config
from utils.logger import logger

running = True


def signal_handler(sig, frame):
    global running
    logger.info("收到退出信号，正在关闭...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def load_config():
    """加载配置文件"""
    config_path = os.path.join(Config.USER_DIR, "config.json")
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return None


def ensure_config():
    """确保配置文件存在，不存在则引导创建"""
    Config.ensure_dirs()
    config_path = os.path.join(Config.USER_DIR, "config.json")

    if os.path.exists(config_path):
        return load_config()

    print("=" * 60)
    print("  学习通自动化工具 - 首次运行配置")
    print("=" * 60)
    print()

    config = {}

    print("【登录方式】")
    print("  1. 账号密码登录（推荐）")
    print("  2. 扫码登录")
    mode = input("请选择 [1/2，默认1]: ").strip() or "1"

    if mode == "1":
        config["login_mode"] = "password"
        config["username"] = input("学号/手机号: ").strip()
        config["password"] = input("密码: ").strip()
        schoolid = input("学校ID（不知道直接回车）: ").strip()
        if schoolid:
            config["schoolid"] = schoolid
    else:
        config["login_mode"] = "scan"

    print()
    print("【消息推送（可选，直接回车跳过）】")
    print("  NotifyX 可将提醒推送到微信/钉钉/邮件等")
    print("  申请地址: https://www.notifyx.cn/help")
    notifyx_key = input("NotifyX API Key: ").strip()
    if notifyx_key:
        config["notifyx_key"] = notifyx_key

    print()
    print("【天气（可选）】")
    location = input('所在地区（如芜湖，回车跳过）: ').strip()
    if location:
        config["location"] = location

    print()
    print("【运行设置】")
    print("  检测间隔越短越及时，但请求更频繁")
    print("  推荐 5 分钟（300秒）")
    interval = input("检测间隔秒数 [默认300]: ").strip()
    config["check_interval"] = int(interval) if interval else 300

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print()
    print(f"配置已保存到 {config_path}")
    print("如需修改，直接编辑此文件即可。")
    print()

    return config


def do_login(config, login_module):
    """执行登录"""
    login_mode = config.get("login_mode", "password")

    # 尝试 cookie 登录
    login_info = config.get("login_info", {})
    cookies = login_info.get("cookies", {})
    if cookies:
        logger.info("尝试 Cookie 登录...")
        if login_module.login_with_cookie(cookies):
            return True
        logger.info("Cookie 已过期")

    if login_mode == "password":
        username = config.get("username", "")
        password = config.get("password", "")
        schoolid = config.get("schoolid", "")
        if not username or not password:
            logger.error("配置中缺少账号或密码")
            return False
        return login_module.login_with_password(username, password, schoolid)
    else:
        return login_module.login()


def run_check_cycle(session, config, state):
    """执行一次完整的检测周期"""
    from utils.chaoxing_work import ChaoXingWork
    from utils.chaoxing_schedule import ChaoXingSchedule
    from utils.chaoxing_sign import ChaoXingSign
    from utils.chaoxing_course import ChaoXingCourse
    from utils.notifyx import NotifyX
    from utils.weather import Weather

    notifyx_key = config.get("notifyx_key")
    location = config.get("location", "")
    notifyx = NotifyX(notifyx_key) if notifyx_key else None

    # 1. 检查作业
    logger.info("检查作业...")
    work = ChaoXingWork(session)
    work_list = work.get_work_list()

    if work_list:
        unsubmitted = work.get_unsubmitted_works(work_list)
        urgent = work.get_urgent_works(unsubmitted)

        if urgent:
            logger.warning(f"紧急作业 {len(urgent)} 个！")

        # 发送通知
        if notifyx and (urgent or unsubmitted):
            should_notify = False
            for w in unsubmitted:
                hours = work.get_hours_remaining(w.get("remaining_time", ""))
                if hours is not None and hours <= 12:
                    should_notify = True
                    break

            if should_notify:
                # 避免重复通知
                work_hash = hash(str([(w["name"], w["status"]) for w in work_list]))
                if state.get("last_work_hash") != work_hash:
                    notifyx.send_work_notification(urgent, unsubmitted)
                    state["last_work_hash"] = work_hash
                    logger.info("作业通知已发送")

    # 2. 检查签到
    logger.info("检查签到...")
    sign = ChaoXingSign(session)
    activities = sign.scan_all_courses_for_sign()

    if activities:
        logger.info(f"发现 {len(activities)} 个签到活动，自动签到...")
        for act in activities:
            result = sign.do_sign(act)
            course_name = act.get("course_name", "未知")
            sign_type = act.get("sign_type", "未知")
            if result["status"] == "success":
                logger.info(f"  ✓ {course_name} 签到成功")
                if notifyx:
                    notifyx.send_sign_result_notification(course_name, sign_type, True)
            else:
                logger.error(f"  ✗ {course_name} 签到失败: {result.get('message', '')}")
                if notifyx:
                    notifyx.send_sign_result_notification(course_name, sign_type, False)

    # 3. 检查课表提醒（每节课前20分钟）
    logger.info("检查课表...")
    schedule = ChaoXingSchedule(session)
    today_lessons = schedule.get_today_lessons()

    if today_lessons:
        now_minutes = __import__("datetime").datetime.now().hour * 60 + __import__("datetime").datetime.now().minute

        for lesson in today_lessons:
            lesson_key = f"{lesson.get('course_no', '')}_{lesson.get('time_range', '')}"
            start_time = lesson.get("start_time")
            if start_time:
                start_minutes = start_time.hour * 60 + start_time.minute
                diff = start_minutes - now_minutes

                # 课前20分钟提醒
                if 0 < diff <= 20:
                    reminder_key = f"reminder_{lesson_key}_{__import__('datetime').datetime.now().strftime('%Y%m%d')}"
                    if not state.get(reminder_key):
                        if notifyx:
                            notifyx.send_upcoming_lesson_notification(lesson)
                            state[reminder_key] = True
                            logger.info(f"课前提醒已发送: {lesson['name']}")

    # 4. 检查考试
    logger.info("检查考试...")
    course = ChaoXingCourse(session)
    exams = course.get_exam_list()

    if exams:
        exam_hash = hash(str([e.get("name", "") for e in exams]))
        if state.get("last_exam_hash") != exam_hash:
            logger.info(f"发现 {len(exams)} 个考试/测验")
            if notifyx:
                notifyx.send_exam_notification(exams)
                state["last_exam_hash"] = exam_hash


def main():
    global running

    # 确保配置
    config = ensure_config()
    if not config:
        return

    print()
    print("=" * 60)
    print("  学习通自动化工具 已启动")
    print("  按 Ctrl+C 退出")
    print("=" * 60)
    print()

    from utils.chaoxing_login import ChaoXingLogin

    # 登录
    login = ChaoXingLogin()
    if not do_login(config, login):
        logger.error("登录失败，请检查配置后重试")
        return

    logger.info("登录成功！开始自动监控...")
    print()

    interval = config.get("check_interval", 300)
    state = {}

    # 主循环
    while running:
        try:
            run_check_cycle(login.session, config, state)

            # 保存 cookie
            from utils.session_manager import SessionManager
            cookies = {c.name: c.value for c in login.session.cookies}
            if cookies:
                config["login_info"] = {
                    "cookies": cookies,
                    "timestamp": __import__("time").strftime("%Y-%m-%d %H:%M:%S")
                }
                config_path = os.path.join(Config.USER_DIR, "config.json")
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)

            logger.info(f"本轮检查完成，{interval} 秒后进行下一轮...")
            print()

            # 等待（可被信号中断）
            for _ in range(interval):
                if not running:
                    break
                time.sleep(1)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"运行出错: {e}")
            time.sleep(30)  # 出错后等待30秒再重试

    logger.info("程序已退出")


if __name__ == "__main__":
    main()
