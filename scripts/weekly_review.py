#!/usr/bin/env python3
"""每周日：聚合一周 tags/mood -> GLM 挚友型点评 -> 存 reviews/weekly/ + 开 Issue + 企业微信推送。"""
import collections
import datetime
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import glm
import notify

REPO = os.environ["GITHUB_REPOSITORY"]
TODAY = datetime.date.today()
WEEK = [(TODAY - datetime.timedelta(days=i)) for i in range(6, -1, -1)]  # 7天，旧->新


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout.strip()


def stats_and_text():
    tag_counter, moods, texts, missing = collections.Counter(), [], [], []
    for d in WEEK:
        p = Path(f"daily/{d.isoformat()}.md")
        if not p.exists():
            missing.append(d.isoformat())
            continue
        t = p.read_text(encoding="utf-8")
        texts.append(f"### {d.isoformat()}\n{t}")
        if m := re.search(r"tags\s*:\s*\[(.*?)\]", t):
            tag_counter.update(x.strip() for x in m.group(1).split(",") if x.strip())
        if m := re.search(r"mood\s*:\s*([1-5])", t):
            moods.append(int(m.group(1)))
    tag_str = "、".join(f"{k}×{v}" for k, v in tag_counter.most_common()) or "无标签"
    mood_str = f"平均 {sum(moods)/len(moods):.1f}/5（{len(moods)} 天有记录）" if moods else "无心情记录"
    recorded = 7 - len(missing)
    summary = (
        f"本周统计：记录 {recorded}/7 天；标签：{tag_str}；心情：{mood_str}；"
        f"未记录日期：{'、'.join(missing) if missing else '无'}。\n"
        f"注意：漏 1-2 天可补票，streak 不断，温柔提醒即可。\n\n"
    )
    return summary + "\n\n".join(texts)


def wecom_push(url: str):
    notify.push("🌱 本周成长点评已生成", "看看挚友对你这周说了什么", url)


def main():
    material = stats_and_text()
    try:
        review = glm.chat(glm.WEEKLY_SYSTEM, material, max_tokens=1200)
    except Exception as e:
        review = f"（本周 LLM 点评生成失败：{e}。数据统计如下，本周你依然被看见了 ❤️）\n\n" + material.split("\n\n")[0]

    week_label = f"{WEEK[0].isoformat()}_{WEEK[-1].isoformat()}"
    header = f"# 🌱 本周成长点评（{WEEK[0].strftime('%m/%d')} - {WEEK[-1].strftime('%m/%d')}）\n\n"
    path = Path(f"reviews/weekly/{week_label}.md")
    path.write_text(header + review + "\n", encoding="utf-8")

    sh("git", "add", str(path))
    sh("git", "commit", "-m", f"🌱 本周成长点评 {week_label}")
    sh("git", "push")

    url = gh("issue", "create", "--title", f"🌱 本周成长点评 {week_label}", "--body", header + review)
    wecom_push(url)


if __name__ == "__main__":
    main()
