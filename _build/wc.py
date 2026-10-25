#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花桥.cn 单篇文章字数实测工具
--------------------------------------------------
用法： python wc.py huaqiao-xxx
       python wc.py huaqiao-xxx --raw   （同时打印正文纯文本）

复用 build.py 的 parse_front_matter / md_to_html / text_len，
保证与构建期统计口径完全一致（去 HTML 标签 + 去所有空白后的字符数）。

用途：任务要求正文字数 800-1500，而 build.py 只卡下限（<700 警告），
      上限无任何脚本校验，必须靠本工具人工实测。
"""
import os
import sys
import re

import build as B

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "_content")


def measure(slug):
    path = os.path.join(CONTENT, slug + ".md")
    if not os.path.exists(path):
        print("文件不存在：%s" % path)
        return None
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    meta, body_md = B.parse_front_matter(raw)
    html_body, faqs = B.md_to_html(body_md)
    wc = B.text_len(html_body)

    # 分段统计：正文（不含 FAQ 与内容说明）
    idx_faq = body_md.find("## 常见问题")
    idx_note = body_md.find("## 内容说明")
    main_md = body_md[: idx_faq if idx_faq > 0 else (idx_note if idx_note > 0 else len(body_md))]
    main_html, _ = B.md_to_html(main_md)
    main_wc = B.text_len(main_html)

    # meta 字段长度
    title = meta.get("title", "")
    seo_title = meta.get("seo_title", "")
    desc = meta.get("desc", "")

    print("=" * 60)
    print("文件：%s" % (slug + ".md"))
    print("=" * 60)
    print("全文 text_len（构建口径，含 FAQ+说明）：%d" % wc)
    print("  其中正文段（不含 FAQ/说明）      ：%d" % main_wc)
    print("  FAQ 问答组数                     ：%d" % len(faqs))
    print("-" * 60)
    print("title     ：%d 字  %s" % (len(title), "✓" if len(title) <= 30 else "✗ 超 30"))
    print("seo_title ：%d 字  %s" % (len(seo_title), "✓" if len(seo_title) <= 28 else "✗ 超 28"))
    print("desc      ：%d 字符  %s" % (len(desc), "✓ 符合 150-160" if 150 <= len(desc) <= 160 else "✗ 需 150-160"))
    print("-" * 60)
    print("字数判定（任务要求 800-1500，构建下限 700）：")
    if wc > 1500:
        print("  ✗ 超上限 %d 字，需精简 %d 字" % (wc, wc - 1500))
    elif wc < 800:
        print("  ✗ 低于 800（%d 字），需补充 %d 字；构建下限 700 %s" % (wc, 800 - wc, "也未达" if wc < 700 else "已过"))
    else:
        print("  ✓ 达标（%d 字，距上限还有 %d 字余量）" % (wc, 1500 - wc))
    print("-" * 60)
    # desc 里的 ASCII 直双引号会导致 meta 提前闭合（历史站级技术债）
    if '"' in desc:
        print("  ⚠ desc 含 ASCII 直双引号，会导致 meta description 被提前闭合！")
    if '"' in title or '"' in seo_title:
        print("  ⚠ title/seo_title 含 ASCII 直双引号！")
    return wc


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    measure(sys.argv[1].replace(".md", ""))
