#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""构建后处理：把外链样式表内联进每个 HTML 页面。

为什么必须内联
--------------
本站经常被"单文件预览"消费：把某一个 index.html 单独取出渲染（IDE 预览面板、
文档内嵌预览、单页分享、离线打开）。此时相对路径 `../assets/css/style.css`
越界取不到文件，**样式表整个 404**。

后果不只是"难看"：页面里内联的 <svg> 若没有 width/height 属性、尺寸完全依赖
CSS，一旦 CSS 丢失就会按默认宽度撑满容器 —— 整页被一排巨幅图标挤爆。
（2026-09-25 实测事故：预览面板 404 → 9 个电话图标各占一整行。）

内联后，线上 / 预览 / 分享 / 离线四种环境渲染完全一致；顺带消掉一次 CSS 请求。

执行顺序
--------
    python _build/build.py       # 生成文章页/目录/sitemap（输出的是 <link> 外链形式）
    python _build/inline_css.py  # 全站 <link> → 内联 <style>（必须在 build 之后）
    python _build/check_site.py  # 自检（兼容内联形式）

改动样式表后只需重跑 inline_css.py，无需重建文章。
幂等：重复执行只更新 <style> 内容，不会重复插入块。
"""
import os
import re
import glob

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS_FILE = os.path.join(SITE, "assets", "css", "style.css")

MARK_OPEN = "<!-- CSS:INLINE -->"
MARK_CLOSE = "<!-- /CSS:INLINE -->"

# 外链样式表标签（可能带任意缩进）
LINK_RE = re.compile(r'[ \t]*<link[^>]+rel="stylesheet"[^>]*>[ \t]*\n?')
# 已内联的块（幂等更新用）
BLOCK_RE = re.compile(re.escape(MARK_OPEN) + r".*?" + re.escape(MARK_CLOSE) + r"[ \t]*\n?", re.S)

INDENT = "  "


def build_block(css):
    """生成内联块。CSS 内容保持原样（不二次缩进，避免无谓体积）。"""
    return (INDENT + MARK_OPEN + "\n"
            + INDENT + "<style>\n"
            + css.rstrip() + "\n"
            + INDENT + "</style>\n"
            + INDENT + MARK_CLOSE + "\n")


def process(path, css):
    with open(path, encoding="utf-8") as f:
        src = f.read()

    block = build_block(css)
    if MARK_OPEN in src:
        new = BLOCK_RE.sub(lambda m: block, src, count=1)
    else:
        m = LINK_RE.search(src)
        if not m:
            return None          # 该页没有样式引用，跳过
        new = src[:m.start()] + block + src[m.end():]

    if new == src:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return True


def main():
    if not os.path.exists(CSS_FILE):
        raise SystemExit("找不到样式表：%s" % CSS_FILE)
    with open(CSS_FILE, encoding="utf-8") as f:
        css = f.read()

    targets = sorted(glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True))
    changed = skipped = 0
    for p in targets:
        # 跳过构建脚本目录与版本库
        if (os.sep + "_build" + os.sep) in p or (os.sep + ".git" + os.sep) in p:
            continue
        r = process(p, css)
        if r is True:
            changed += 1
        elif r is None:
            skipped += 1
    print("样式表 %.1f KB → 扫描 %d 个页面：更新 %d 个，跳过 %d 个（无样式引用）"
          % (len(css) / 1024.0, len(targets), changed, skipped))


if __name__ == "__main__":
    main()
