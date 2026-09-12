#!/usr/bin/env python3
"""自动更新 README 的数据看板：连续天数、本月记录率、标签统计、近15周热力图。
由 stats.yml 工作流在每次 push daily/** 后及每周日调用。"""
import collections
import datetime
import re
from pathlib import Path

TODAY = datetime.date.today()
DAYS_BACK = 15 * 7  # 近15周

BEGIN = "<!-- DASHBOARD:BEGIN -->"
END = "<!-- DASHBOARD:END -->"


def recorded_dates() -> set:
    return {p.stem for p in Path("daily").glob("????-??-??.md")}


def parse_date(s):
    return datetime.date.fromisoformat(s)


def streak(dates):
    """宽松规则：允许断1天，连断2天才计断（连漏3天=断已在宪章定义，此处统计展示用）。"""
    if not dates:
        return 0
    d = TODAY
    ds = set(dates)
    gap = 0
    count = 0
    while True:
        if d.isoformat() in ds:
            count += 1
            gap = 0
        else:
            gap += 1
            if gap >= 2:
                break
        d -= datetime.timedelta(days=1)
    return count


def tag_stats(dates):
    c = collections.Counter()
    for s in dates:
        p = Path(f"daily/{s}.md")
        t = p.read_text(encoding="utf-8")
        if m := re.search(r"tags\s*:\s*\[(.*?)\]", t):
            c.update(x.strip() for x in m.group(1).split(",") if x.strip())
    return c


def heatmap(dates):
    """近15周 GitHub 风格热力图（周一开头行）。"""
    ds = set(dates)
    weeks = []
    # 对齐到周一
    start = TODAY - datetime.timedelta(days=DAYS_BACK - 1)
    start -= datetime.timedelta(days=start.weekday())
    wk = []
    d = start
    while d <= TODAY:
        if d > TODAY:
            wk.append("⬜")
        elif d.isoformat() in ds:
            wk.append("🟩")
        else:
            wk.append("⬜")
        if d.weekday() == 6:
            weeks.append("".join(wk))
            wk = []
        d += datetime.timedelta(days=1)
    if wk:
        weeks.append("".join(wk))
    return "\n".join(weeks)


def render() -> str:
    dates = recorded_dates()
    this_month = [s for s in dates if s.startswith(TODAY.strftime("%Y-%m"))]
    month_rate = len(this_month) / TODAY.day * 100
    st = streak(dates)
    tags = tag_stats(sorted(dates)[-90:])  # 近90天标签
    tag_line = "  ".join(f"`{k}` ×{v}" for k, v in tags.most_common(8)) or "（还没有标签数据）"
    return "\n".join([
        BEGIN,
        f"## 📊 成长看板（自动更新：{TODAY.isoformat()}）",
        "",
        f"🔥 **连续记录 {st} 天** ｜ 📅 本月记录率 **{month_rate:.0f}%**（{len(this_month)}/{TODAY.day} 天） ｜ 📚 累计 **{len(dates)}** 篇",
        "",
        f"**近 90 天标签**：{tag_line}",
        "",
        "**近 15 周**（左→右为时间，🟩=已记录）：",
        "",
        "```",
        heatmap(dates),
        "```",
        "",
        END,
    ])


def main():
    p = Path("README.md")
    text = p.read_text(encoding="utf-8")
    if BEGIN in text and END in text:
        pre, rest = text.split(BEGIN, 1)
        _, post = rest.split(END, 1)
        text = pre + render() + post
    else:
        text += "\n\n" + render() + "\n"
    p.write_text(text, encoding="utf-8")
    print(render())


if __name__ == "__main__":
    main()
