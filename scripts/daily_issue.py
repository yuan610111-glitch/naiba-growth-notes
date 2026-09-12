#!/usr/bin/env python3
"""每日 21:00：创建当日 Issue（附昨日一句话点评）+ 企业微信提醒。
在工作流中运行，依赖 gh CLI；GLM_API_KEY / WECOM_WEBHOOK 环境变量。"""
import datetime
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import glm
import notify

REPO = os.environ["GITHUB_REPOSITORY"]
TODAY = datetime.date.today().isoformat()
YESTERDAY = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout.strip()


def one_line_comment():
    p = Path(f"daily/{YESTERDAY}.md")
    if not p.exists():
        return "昨天还没有记录，没关系——今天写下第一行就是新的开始 🌱"
    try:
        return glm.chat(glm.ONE_LINE_SYSTEM, f"他昨天的记录：\n\n{p.read_text(encoding='utf-8')[:3000]}")
    except Exception as e:
        print(f"GLM 调用失败（不影响主流程）: {e}")
        return "昨天的事已经过去了，今天的你正在被记录 ✍️"


def wecom_push(issue_url: str):
    notify.push("🍼 奶爸成长笔记", "今天还没记录哦，回复一条就算打卡（一行也行）", issue_url)


def main():
    # 若今日已有 Issue 则不重复
    title = f"📖 记录 {TODAY}"
    existing = gh("issue", "list", "--state", "open", "--search", f'"{title}" in:title', "--json", "number")
    if json.loads(existing):
        print("今日 Issue 已存在，跳过创建")
        return

    body = "\n".join([
        f"**{TODAY} · 今天的记录**",
        "",
        "> 直接在下方回复即算打卡（一行也算数）。机器人会自动存入 `daily/{TODAY}.md` 并 commit 变绿 🟩",
        "> 敏感信息（手机号/身份证等）会自动打码。",
        "",
        "**可用字段（直接写进回复，也可自由发挥）：**",
        "```",
        "tags: [健身, 读书, 学习, 副业, 陪玩]   # 随便增删",
        "mood: 4                                # 1-5",
        "做成的一件事：…",
        "学到的东西：…",
        "和宝宝的时刻：…",
        "想对18岁的你说：…",
        "随便聊聊：…",
        "```",
        "",
        "---",
        f"💬 **昨天的一句话**：{one_line_comment()}",
    ])
    url = gh("issue", "create", "--title", title, "--body", body)
    print(f"已创建 Issue: {url}")
    wecom_push(url)


if __name__ == "__main__":
    main()
