#!/usr/bin/env python3
"""Issue 回复 -> 自动保存为 daily/YYYY-MM-DD.md 并 commit。
在 issue_comment 工作流中运行。环境变量：
  ISSUE_TITLE / ISSUE_NUMBER / ISSUE_AUTHOR / COMMENT_BODY / COMMENT_AUTHOR
宽松规则：作者自己的回复即记录；补票允许（按 Issue 日期而非今天）。"""
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from privacy_check import scan_and_mask

DATE_RE = re.compile(r"📖 记录 (\d{4}-\d{2}-\d{2})")


def sh(*args, **kw):
    return subprocess.run(args, capture_output=True, text=True, check=True, **kw).stdout.strip()


def build_markdown(raw: str) -> str:
    """把回复文本解析为模板结构：识别 tags:/mood: 头字段，其余按小节关键词归类，剩余进『随便聊聊』。"""
    lines = raw.strip().splitlines()
    tags, mood = "[]", ""
    sections = {"做成": [], "学到": [], "宝宝": [], "18岁": [], "聊": []}
    # 关键词 -> 小节；行首出现关键词即切换当前小节
    keymap = [("做成", "做成"), ("学到", "学到"), ("宝宝", "宝宝"), ("18岁", "18岁"),
              ("想对", "18岁"), ("聊", "聊")]
    current = None
    for ln in lines:
        s = ln.strip()
        if m := re.match(r"tags?\s*[:：]\s*(.+)", s, re.I):
            tags = m.group(1).strip()
            continue
        if m := re.match(r"mood\s*[:：]\s*(\d)", s, re.I):
            mood = m.group(1)
            continue
        if s and not s.startswith(("#", ">", "**")):
            prefix = s.split("：", 1)[0].split(":", 1)[0]  # 冒号前的引导语
            for kw, sec in keymap:
                if kw in prefix and len(prefix) <= 12:
                    # "做成的一件事：xxx" —— 冒号后的内容算本节正文
                    after = s.split("：", 1)[-1].split(":", 1)[-1].strip()
                    if after and after != s:
                        sections[sec].append(after)
                    current = sec
                    break
            else:
                (sections[current] if current else sections["聊"]).append(s)
        elif s:
            (sections[current] if current else sections["聊"]).append(s)
    fill = lambda k: ("\n".join(sections[k]) + "\n") if sections[k] else "（今天没写这节，没关系）\n"
    out = [
        "---",
        f"date: {os.environ.get('ENTRY_DATE')}",
        f"tags: {tags}",
        f"mood: {mood}" if mood else "# mood 未填",
        "---",
        "",
        "## 今天做成的一件事", "", fill("做成"),
        "## 学到的东西", "", fill("学到"),
        "## 和宝宝的时刻 👶", "", fill("宝宝"),
        "## 想对18岁的你说", "", fill("18岁"),
        "## 随便聊聊", "", fill("聊"),
    ]
    return "\n".join(out)


def main():
    sh("git", "config", "user.name", "naiba-bot")
    sh("git", "config", "user.email", "naiba-bot@users.noreply.github.com")
    title = os.environ["ISSUE_TITLE"]
    m = DATE_RE.search(title)
    entry_date = m.group(1) if m else datetime.date.today().isoformat()
    os.environ["ENTRY_DATE"] = entry_date

    body = build_markdown(os.environ["COMMENT_BODY"])
    body, hits = scan_and_mask(body)
    if hits:
        print("PRIVACY_HITS=" + "|".join(hits))

    path = Path(f"daily/{entry_date}.md")
    if path.exists():  # 补票/重写：追加
        path.write_text(path.read_text(encoding="utf-8") + f"\n---\n\n（{os.environ['COMMENT_AUTHOR']} 于今日补记）\n\n{body}\n", encoding="utf-8")
        msg = f"📝 更新 {entry_date} 成长记录"
    else:
        path.write_text(body, encoding="utf-8")
        msg = f"📝 记录 {entry_date} 成长日记"

    sh("git", "add", str(path))
    sh("git", "commit", "-m", msg)
    sh("git", "push")

    # 回评 + 关闭 Issue
    comment = "🟩 已记录并 commit，今天的格子绿了！"
    if hits:
        comment += "\n\n⚠️ **隐私自查提示**：检测到疑似敏感信息，已自动打码为 🔒***：\n" + "\n".join(f"- {h}" for h in hits) + "\n\n请确认是否还有遗漏（参考 PRIVACY.md），必要时直接编辑文件修改。"
    sh("gh", "issue", "comment", os.environ["ISSUE_NUMBER"], "--body", comment)
    sh("gh", "issue", "close", os.environ["ISSUE_NUMBER"])
    print("DONE")


if __name__ == "__main__":
    main()
