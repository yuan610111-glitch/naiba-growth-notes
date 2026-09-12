#!/usr/bin/env python3
"""年度报告（手动触发，建议儿子生日运行）：LLM 以『18年后的你』口吻写信。"""
import datetime
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import glm

YEAR = os.environ.get("YEAR") or str(datetime.date.today().year)


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout.strip()


def collect():
    parts = []
    for p in sorted(Path("daily").rglob(f"{YEAR}-*.md")):
        parts.append(p.read_text(encoding="utf-8"))
    # 全量可能超上下文，按月采样 + 截断：每月取首尾各 2 篇
    if len(parts) > 100:
        by_month = {}
        for t in parts:
            by_month.setdefault(t[5:7] if False else t.split("-")[1], []).append(t)
        sampled = []
        for m in sorted(by_month):
            grp = by_month[m]
            sampled.extend(grp[:2] + grp[-2:] if len(grp) > 4 else grp)
        parts = sampled
    return "\n\n---\n\n".join(parts)[:60000]


def main():
    sh("git", "config", "user.name", "naiba-bot")
    sh("git", "config", "user.email", "naiba-bot@users.noreply.github.com")
    material = collect()
    if not material:
        print(f"{YEAR} 年还没有任何记录，无法生成年度报告")
        return
    letter = glm.chat(glm.ANNUAL_SYSTEM, f"以下是 {YEAR} 年他的全部成长记录：\n\n{material}", max_tokens=3000)

    path = Path(f"reviews/annual/{YEAR}.md")
    header = f"# 🎂 爸爸这一年 · {YEAR}\n\n> 来自 18 年后的你\n\n"
    path.write_text(header + letter + "\n", encoding="utf-8")
    sh("git", "add", str(path))
    sh("git", "commit", "-m", f"🎂 年度报告 {YEAR}")
    sh("git", "push")
    gh("issue", "create", "--title", f"🎂 爸爸这一年 · {YEAR}", "--body", header + letter)
    print(f"年度报告已生成: {path}")


if __name__ == "__main__":
    main()
