#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全站导航统一 + 清理编辑器注入属性
用法： python _build/patch_nav_all.py
说明：
  1) 把所有页面的 <nav class="main-nav">…</nav> 重写为统一的 7 项导航，并按当前页设置 active；
  2) 清理 data-page-node-id="…" 这类无意义注入属性（编辑器会持续注入，提交前跑一次）。
"""
import os
import re
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)

NAV = [
    ("买房", "/buy/"),
    ("买房攻略", "/articles/"),
    ("跑盘评测", "/review/"),
    ("通勤", "/commute/"),
    ("跨城办事", "/guide/"),
    ("本地黄页", "/directory/"),
    ("关于", "/about/"),
]

# 一级目录 → 导航项名称（用于 active 判定）
DIR2NAV = {"buy": "买房", "articles": "买房攻略", "review": "跑盘评测",
           "commute": "通勤", "guide": "跨城办事", "directory": "本地黄页", "about": "关于"}


def page_files():
    out = sorted(glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True))
    return [p for p in out if "/_build/" not in p.replace("\\", "/")]


def nav_block(path):
    rel = os.path.relpath(path, SITE).replace("\\", "/")
    segs = rel.split("/")[:-1]          # 去掉文件名
    depth = len(segs)
    prefix = "../" * depth if depth else "./"

    active = ""
    if segs:
        active = DIR2NAV.get(segs[0], "")

    links = ""
    for name, url in NAV:
        cls = ' class="active"' if name == active else ""
        links += '\n        <a href="%s%s"%s>%s</a>' % (prefix, url.lstrip("/"), cls, name)
    return ('<nav class="main-nav">%s\n      </nav>' % links)


def main():
    changed = 0
    for path in page_files():
        with open(path, encoding="utf-8") as f:
            src = f.read()
        orig = src
        # 1) 清理注入属性
        src = re.sub(r'\s+data-page-node-id="[^"]*"', "", src)
        # 2) 统一导航
        src, n = re.subn(r'<nav class="main-nav"[^>]*>.*?</nav>', nav_block(path), src, flags=re.S)
        if n == 0:
            print("  [跳过] 无导航: %s" % os.path.relpath(path, SITE))
        if src != orig:
            with open(path, "w", encoding="utf-8") as f:
                f.write(src)
            changed += 1
    print("处理页面 %d 个，更新 %d 个" % (len(page_files()), changed))


if __name__ == "__main__":
    main()
