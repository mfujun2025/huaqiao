#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花桥.cn 静态站自检脚本（纯标准库）
用法： python _build/check_site.py
检查：内部链接 / 页内锚点 / 必需 meta / 标签配对 / JSON-LD / title 唯一 / 正文体量
"""
import os
import re
import json
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)

errors = []
warnings = []


def pages():
    out = sorted(glob.glob(os.path.join(SITE, "**", "index.html"), recursive=True))
    out += glob.glob(os.path.join(SITE, "404.html"))
    return [p for p in out if "_build" not in p.replace("\\", "/")]


def rel(p):
    return os.path.relpath(p, SITE).replace("\\", "/")


def body_text(html):
    m = re.search(r"<main.*?</main>", html, re.S)
    src = m.group(0) if m else html
    return re.sub(r"\s", "", re.sub(r"<[^>]+>", "", src))


all_pages = pages()
titles = {}

for path in all_pages:
    with open(path, encoding="utf-8") as f:
        html = f.read()
    rp = rel(path)

    # 1) 必需 meta
    for tag, pat in [("title", r"<title>(.+?)</title>"),
                     ("description", r'<meta name="description" content="(.+?)"'),
                     ("canonical", r'<link rel="canonical" href="(.+?)"')]:
        m = re.search(pat, html, re.S)
        if not m or not m.group(1).strip():
            errors.append("[meta] %s 缺少 %s" % (rp, tag))
    m = re.search(r'<link rel="stylesheet" href="(.+?)"', html)
    if not m:
        errors.append("[meta] %s 未引用样式表" % rp)
    else:
        css = os.path.normpath(os.path.join(os.path.dirname(path), m.group(1)))
        if not os.path.exists(css):
            errors.append("[meta] %s 样式表路径不存在: %s" % (rp, m.group(1)))

    # 2) title 唯一
    mt = re.search(r"<title>(.+?)</title>", html, re.S)
    if mt:
        t = mt.group(1).strip()
        if t in titles:
            errors.append("[title] 重复：%s（%s 与 %s）" % (t, rp, titles[t]))
        titles[t] = rp

    # 3) 内部链接
    #    先剥离内联 <script>/<style>，否则 JS 模板字符串里的 href（如 'href="' + x + '"'）
    #    会被正则抓出来当成断链，造成假报。
    html_markup = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)
    html_markup = re.sub(r"<style\b.*?</style>", "", html_markup, flags=re.S | re.I)
    for attr, target in re.findall(r'(href|src)="([^"]+)"', html_markup):
        if re.match(r"^(https?:|mailto:|tel:|data:|javascript:)", target) or target.startswith("#"):
            continue
        clean = target.split("#")[0].split("?")[0]
        if not clean:
            continue
        p = os.path.normpath(os.path.join(os.path.dirname(path), clean))
        if os.path.isdir(p):
            p = os.path.join(p, "index.html")
        if not os.path.exists(p) and not os.path.exists(p + "/index.html"):
            errors.append("[link] %s → 断链 %s" % (rp, target))

    # 4) 页内锚点
    ids = set(re.findall(r'id="([^"]+)"', html_markup))
    for anchor in re.findall(r'href="#([^"]+)"', html_markup):
        if anchor and anchor not in ids:
            errors.append("[anchor] %s → 锚点 #%s 不存在" % (rp, anchor))

    # 5) 标签配对
    for tag in ["html", "head", "body", "main", "header", "footer", "section", "nav", "table"]:
        o = len(re.findall(r"<%s[\s>]" % tag, html))
        c = len(re.findall(r"</%s>" % tag, html))
        if o != c:
            errors.append("[tag] %s 标签不配对：<%s> %d / </%s> %d" % (rp, tag, o, tag, c))

    # 6) JSON-LD
    for i, block in enumerate(re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)):
        try:
            obj = json.loads(block)
            if "@context" not in obj or "@type" not in obj:
                warnings.append("[jsonld] %s 第 %d 段缺少 @context/@type" % (rp, i + 1))
        except Exception as e:
            errors.append("[jsonld] %s 第 %d 段解析失败: %s" % (rp, i + 1, e))

    # 7) 正文体量（文章页）
    if "/articles/" in rp and rp != "articles/index.html":
        n = len(body_text(html))
        if n < 1500:
            errors.append("[content] %s 正文仅 %d 字（要求 ≥1500）" % (rp, n))

    # 8) 404 页不应被索引
    if rp == "404.html":
        if 'name="robots"' not in html or "noindex" not in html:
            errors.append("[seo] 404.html 缺少 noindex")

    # 9) canonical 必须是绝对地址
    mc = re.search(r'<link rel="canonical" href="(.+?)"', html)
    if mc and not mc.group(1).startswith("http"):
        errors.append("[seo] %s canonical 不是绝对地址" % rp)

print("检查页面 %d 个" % len(all_pages))
for w in warnings:
    print("  WARN  " + w)
if errors:
    print("\n发现 %d 个问题：" % len(errors))
    for e in errors:
        print("  ERROR " + e)
    raise SystemExit(1)
print("全部通过：链接、锚点、meta、标签配对、JSON-LD、title 唯一、正文体量、canonical")
