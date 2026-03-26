# 学习通自动化工具

一键启动，持续运行。自动完成签到、作业提醒、课表提醒、考试提醒。

## 快速开始

```bash
pip install -r requirements.txt
python main.py
```

首次运行会引导你完成配置（账号密码、推送Key、天气地区），之后每次 `python main.py` 即可。

## 功能

| 功能 | 说明 |
|------|------|
| 🔐 自动登录 | 账号密码/扫码，Cookie 自动续期 |
| ✅ 自动签到 | 检测签到活动并自动完成（普通/手势/位置/拍照） |
| 📝 作业提醒 | 未提交作业定时提醒，紧急作业优先推送 |
| 📅 课表提醒 | 课前20分钟推送上课提醒 |
| 📋 考试提醒 | 检测考试/测验并推送通知 |
| 🌤️ 天气 | 每日课程提醒附带天气信息 |
| 💬 消息推送 | 支持 NotifyX 推送到微信/钉钉/邮件等 |

## 运行方式

```bash
# 直接启动（后台持续运行，每5分钟检测一次）
python main.py

# 按 Ctrl+C 退出
```

启动后自动执行：登录 → 检查签到 → 检查作业 → 检查课表 → 检查考试 → 等待 → 循环

## 配置文件

配置保存在 `user/config.json`，首次运行自动生成，也可手动修改：

```json
{
  "login_mode": "password",
  "username": "你的学号",
  "password": "你的密码",
  "notifyx_key": "NotifyX密钥（可选）",
  "location": "芜湖（可选）",
  "check_interval": 300
}
```

- `check_interval`：检测间隔秒数，默认300（5分钟）

## 消息推送

支持 [NotifyX](https://www.notifyx.cn/help) 推送到：

- 企业微信
- 钉钉
- 飞书
- 邮件
- 其他渠道

## 定时运行（可选）

如果不想手动启动，可以用 cron：

```bash
# 每小时运行一次
0 * * * * cd /path/to/Chaoxing_Tools && python main.py &
```

或用 `nohup python main.py &` 后台运行。

## 免责声明

本工具仅供学习交流使用，使用者需遵守学习通的使用条款。
