#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花桥.cn 单文章构建脚本
仅处理新增的文章，避免重新构建全部60篇文章
"""
import os
import re
import json
import html as _html

# 路径配置
BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.dirname(BUILD_DIR)
CONTENT_DIR = os.path.join(BUILD_DIR, '_content')
DOMAIN = "https://xn--6yv589c.cn"
SITE_NAME = "花桥.cn"
TODAY = "2026-10-14"
CONTACT = "mfujun@agent.qq.com"

# 簇定义
CLUSTERS = {
    "decision": ("决策与是否值得", "/buy/", "买房决策"),
    "commute": ("跨城通勤", "/commute/", "通勤攻略"),
    "area": ("区域与配套", "/directory/", "本地黄页"),
    "price": ("价格与行情", "/buy/", "买房决策"),
    "process": ("交易流程与避坑", "/guide/", "跨城办事"),
    "hold": ("产品选择与持有", "/review/", "跑盘评测"),
}

DISCLAIMER = ("<strong>免责声明：</strong>本文为公开信息梳理与判断方法整理，非购房建议、非楼盘推荐。"
              "房价、政策、学区划分、税费标准以各主管部门与官方公示为准，并按年度调整。"
              "本站不代理楼盘、不介入交易、不收取开发商费用，不承担因信息滞后或误差导致的责任。")


def rel(target, depth):
    base = "../" * depth if depth else "./"
    return base + target.lstrip("/")


def esc(s):
    return _html.escape(s, quote=False)


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def text_len(s):
    return len(re.sub(r"\s", "", re.sub(r"<[^>]+>", "", s)))


def parse_front_matter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise ValueError("缺少 frontmatter")
    meta = {}
    for ln in m.group(1).split("\n"):
        if ":" in ln:
            k, v = ln.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def render_table(rows):
    head = [c.strip() for c in rows[0].strip("|").split("|")]
    body = rows[2:]
    h = ('<div class="table-scroll"><table class="info-table"><thead><tr>'
         + "".join("<th>%s</th>" % inline(c) for c in head)
         + "</tr></thead><tbody>")
    for r in body:
        cells = [c.strip() for c in r.strip("|").split("|")]
        h += "<tr>" + "".join("<td>%s</td>" % inline(c) for c in cells) + "</tr>"
    return h + "</tbody></table></div>"


def render_faq(block):
    qa, cur = [], None
    for ln in block:
        s = ln.strip()
        if s.startswith("Q|"):
            if cur:
                qa.append(cur)
            cur = [s[2:].strip(), []]
        elif s.startswith("A|") and cur:
            cur[1].append(s[2:].strip())
    if cur:
        qa.append(cur)
    out = ['<div class="faq">']
    for q, a in qa:
        out.append("<details><summary>%s</summary><div class=\"faq-a\"><p>%s</p></div></details>"
                   % (inline(q), inline(" ".join(a))))
    out.append("</div>")
    return "\n".join(out), [(q, " ".join(a)) for q, a in qa]


def md_to_html(md):
    lines = md.split("\n")
    out, faqs, i = [], [], 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if not line:
            i += 1
            continue
        if line == "::faq":
            block, i = [], i + 1
            while i < len(lines) and lines[i].strip() != "::":
                block.append(lines[i])
                i += 1
            i += 1
            h, qa = render_faq(block)
            out.append(h)
            faqs.extend(qa)
            continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1].strip()):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            out.append(render_table(rows))
            continue
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2)), lvl))
            i += 1
            continue
        if line.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append('<div class="notice">%s</div>' % inline(" ".join(buf)))
            continue
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(inline(re.sub(r"^[-*]\s+", "", lines[i].strip())))
                i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % x for x in items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(inline(re.sub(r"^\d+\.\s+", "", lines[i].strip())))
                i += 1
            out.append("<ol>" + "".join("<li>%s</li>" % x for x in items) + "</ol>")
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{2,4}\s|[-*]\s|\d+\.\s|\||>|::)", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))
    return "\n".join(out), faqs


def header_nav(depth):
    nav_items = [
        ("买房", "/buy/"),
        ("买房攻略", "/articles/"),
        ("跑盘评测", "/review/"),
        ("通勤", "/commute/"),
        ("跨城办事", "/guide/"),
        ("本地黄页", "/directory/"),
        ("关于", "/about/"),
    ]
    items = "".join('\n        <a href="%s">%s</a>' % (rel(u, depth), n) for n, u in nav_items)
    return """  <header class="site-header">
    <div class="container">
      <a href="%s" class="logo">花桥<span>.cn</span></a>
      <nav class="main-nav">%s
      </nav>
    </div>
  </header>""" % (rel("/", depth), items)


def footer(depth):
    return """  <footer class="site-footer">
    <div class="container">
      <p class="disclaimer">%s</p>
      <p class="copyright">© 2026 花桥.cn · 民间信息聚合 · <a href="%s">关于与联系</a></p>
    </div>
  </footer>""" % (DISCLAIMER, rel("/about/", depth))


def page(title, desc, canonical, depth, body, jsonld=None, robots=None, extra_css=None):
    ld = ""
    if jsonld:
        for obj in jsonld:
            ld += '\n  <script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False)
    rb = '\n  <meta name="robots" content="%s">' % robots if robots else ""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>%s</title>
  <meta name="description" content="%s">
  <link rel="canonical" href="%s">%s%s
  <link rel="stylesheet" href="%sassets/css/style.css">
</head>
<body>
%s

%s

%s
</body>
</html>
""" % (esc(title), esc(desc), canonical, rb, ld, rel("/", depth), header_nav(depth), body, footer(depth))


def render_article(slug):
    """渲染单篇文章"""
    # 读取文章
    article_path = os.path.join(CONTENT_DIR, f"{slug}.md")
    if not os.path.exists(article_path):
        print(f"ERROR: Article not found: {article_path}")
        return False

    with open(article_path, encoding="utf-8") as f:
        meta, body = parse_front_matter(f.read())

    html_body, faqs = md_to_html(body)
    wc = text_len(html_body)

    print(f"Article: {meta.get('title')}")
    print(f"Word count: {wc}")
    print(f"Cluster: {meta.get('cluster')}")

    # 验证
    if meta.get('cluster') not in CLUSTERS:
        print(f"ERROR: Unknown cluster: {meta.get('cluster')}")
        return False

    if wc < 700:
        print(f"WARNING: Article too short ({wc} words)")

    # 生成页面
    depth = 2
    canon = "%s/articles/%s/" % (DOMAIN, slug)
    cname = CLUSTERS[meta['cluster']]

    # 目录
    heads = re.findall(r"<h2>(.*?)</h2>", html_body)
    toc = ""
    if len(heads) >= 4:
        items = ""
        for idx, h in enumerate(heads):
            hid = "s%d" % (idx + 1)
            items += '<li><a href="#%s">%s</a></li>' % (hid, h)
        toc = '<nav class="toc"><strong>本文目录</strong><ol>%s</ol></nav>' % items
        cnt = [0]

        def add_id(m):
            cnt[0] += 1
            return '<h2 id="s%d">%s</h2>' % (cnt[0], m.group(1))

        html_body = re.sub(r"<h2>(.*?)</h2>", add_id, html_body)

    # 相关文章（同簇）
    related = ""
    # 这里简化处理，不加载全部文章

    body_html = """  <main class="sub-page">
    <div class="container article">
      <p class="breadcrumb"><a href="%s">首页</a> / <a href="%s">买房攻略</a> / %s</p>
      <h1>%s</h1>
      <p class="subtitle">%s</p>
      <p class="meta-line">栏目：<a href="%s">%s</a> · 更新于 %s</p>
      %s
      %s
      <div class="notice">%s</div>
      <section class="related">
        <h2>相关阅读</h2>
        <ul>
          <li><a href="%s">%s</a>（本栏目总览）</li>
        </ul>
      </section>
    </div>
  </main>""" % (
        rel("/", depth), rel("/articles/", depth), esc(meta["title"]),
        esc(meta["title"]), esc(meta.get("desc", "")),
        rel(cname[1], depth), esc(cname[2]), esc(meta.get("date", TODAY)),
        toc, html_body,
        '本文由花桥.cn 整理，联系方式 %s。内容会随官方口径变化修订。' % esc(CONTACT),
        rel(cname[1], depth), esc(cname[2]),
    )

    # JSON-LD
    jsonld = [{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta["title"],
        "description": meta.get("desc", ""),
        "datePublished": meta.get("date", TODAY),
        "dateModified": meta.get("date", TODAY),
        "inLanguage": "zh-CN",
        "mainEntityOfPage": canon,
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": {"@type": "Organization", "name": SITE_NAME},
    }, {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "首页", "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": "买房攻略", "item": DOMAIN + "/articles/"},
            {"@type": "ListItem", "position": 3, "name": meta["title"], "item": canon},
        ],
    }]
    if faqs:
        jsonld.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": ans}}
                           for q, ans in faqs],
        })

    title = meta.get("seo_title") or meta["title"]
    html = page(title, meta.get("desc", ""), canon, depth, body_html, jsonld)

    # 写入文件
    out_dir = os.path.join(SITE_DIR, "articles", slug)
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "index.html")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Written to: {out_file}")
    print(f"File size: {os.path.getsize(out_file)} bytes")
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python build_single.py <slug>")
        sys.exit(1)

    slug = sys.argv[1]
    if render_article(slug):
        print("\n✓ Build successful!")
    else:
        print("\n✗ Build failed!")
        sys.exit(1)
