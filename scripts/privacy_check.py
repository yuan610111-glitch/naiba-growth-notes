#!/usr/bin/env python3
"""隐私检测：正则扫描 + 自动打码。被多个工作流复用。"""
import re
import sys
from pathlib import Path

# (模式, 说明) —— 命中即打码
PATTERNS = [
    (re.compile(r"\b1[3-9]\d{9}\b"), "手机号"),
    (re.compile(r"\b\d{6}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b"), "身份证号"),
    (re.compile(r"\b\d{16,19}\b"), "疑似银行卡号/长数字"),
    (re.compile(r"(?:X栋|x栋|X号楼|\d+栋|\d+号楼)\s*\d*(?:单元)?\s*\d{1,4}(?:室|号)?"), "疑似门牌号"),
    (re.compile(r"(幼儿园|小学|中学|幼儿园名)[:：]?\s*[\u4e00-\u9fa5]{2,10}"), "疑似学校名称"),
]

REPLACEMENT = "🔒***"


def scan_and_mask(text: str):
    """返回 (打码后文本, 命中说明列表)"""
    hits = []
    for pat, label in PATTERNS:
        def _sub(m, label=label):
            hits.append(f"{label}: {m.group(0)[:6]}…")
            return REPLACEMENT
        text = pat.sub(_sub, text)
    return text, hits


def main():
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    masked, hits = scan_and_mask(text)
    if hits:
        path.write_text(masked, encoding="utf-8")
        print("PRIVACY_HITS=" + "|".join(hits))
        print("\n".join(f"⚠️ 已自动打码 {h}" for h in hits))
    else:
        print("PRIVACY_HITS=")


if __name__ == "__main__":
    main()
