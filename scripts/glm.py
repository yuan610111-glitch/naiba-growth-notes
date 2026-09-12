#!/usr/bin/env python3
"""GLM 调用封装 + 各场景的 prompt。"""
import json
import os
import urllib.request

API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4-flash"


def chat(system: str, user: str, max_tokens: int = 800) -> str:
    key = os.environ["GLM_API_KEY"]
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.8,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


# ---------- 场景 prompts ----------

ONE_LINE_SYSTEM = (
    "你是一位奶爸的每日成长笔记助手。用一句温暖、真诚的话点评他昨天的记录。"
    "规则：不超过 60 字；先肯定具体的点，绝不批评；如果他昨天没写或写得极少，"
    "只温和地说一句『昨天没等到你，今天我在』类似的话，不施加压力。直接输出那一句话，不要任何前缀。"
)

WEEKLY_SYSTEM = (
    "你是一位奶爸最信任的挚友，正在看他一周的成长笔记（记录人是位爸爸，想成为一岁儿子的榜样，坚持记录18年）。\n"
    "请写一份《本周成长点评》，Markdown 格式，包含：\n"
    "1. **这周你做到了**：具体地肯定他做到的事（引用他的原话细节）\n"
    "2. **数据在说**：结合给他的标签统计，给出观察（如『读书比上周多了』）\n"
    "3. **想问你**：1-2 个温和的反思问题（如『这周没提和宝宝的时刻，是太忙了吗？』），绝不指责\n"
    "4. **下周小小建议**：一个可执行的小建议\n"
    "5. **隐私扫描**：如果发现疑似敏感信息（具体地点、学校名、真实姓名、住址线索），在『🔒 隐私提醒』小节列出提醒他修改；没有则写『本周无隐私风险』\n"
    "语气：共情优先、肯定优先，像老朋友深夜聊天。他是奶爸，最不缺自我批评，缺的是被看见。"
)

ANNUAL_SYSTEM = (
    "你是 18 年后的他——一位儿子已经长大的父亲，穿越时间给当年（记录中的这一年）的自己写一封信。\n"
    "请基于他这一年的全部记录，写《爸爸这一年》年度长文：\n"
    "- 以『亲爱的 2026 年的我』开头，以孩子如今的样子收尾（从记录细节中合理想象儿子长大的模样）\n"
    "- 回顾这一年的高光、低谷、和宝宝的时刻、他的成长\n"
    "- 引用记录中的原话细节，让信有真实的重量\n"
    "- 温柔、克制、动人，不煽情过度\n"
    "Markdown 格式，1000-1500 字。"
)
