#!/usr/bin/env python3
"""消息推送：Server酱（直达个人微信）。环境变量 SERVERCHAN_SENDKEY。"""
import json
import os
import urllib.request


def push(title: str, content: str, url: str = ""):
    """推送到个人微信。失败只打印不抛出——提醒是增强，不是主流程。"""
    key = os.environ.get("SERVERCHAN_SENDKEY", "")
    if not key:
        print("未配置 SERVERCHAN_SENDKEY，跳过推送")
        return
    body = json.dumps({
        "title": title,
        "desp": f"{content}\n\n[👉 点这里]({url})" if url else content,
    }).encode()
    req = urllib.request.Request(
        f"https://sctapi.ftqq.com/{key}.send",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"Server酱推送: {json.loads(resp.read()).get('code')}")
    except Exception as e:
        print(f"Server酱推送失败（不影响主流程）: {e}")
