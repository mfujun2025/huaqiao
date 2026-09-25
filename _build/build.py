#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
花桥.cn 文章批量构建脚本
--------------------------------------------------
用法： python build.py
输入： _build/_content/*.md      （frontmatter + markdown 正文）
输出： articles/<slug>/index.html
       articles/index.html      （全部文章聚合页，按簇分组）
       sitemap.xml  robots.txt  404.html
       hub 页自动文章列表注入（_content 里 cluster 对应）
不依赖任何第三方库。
"""
import os
import re
import json
import glob
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)                        # huaqiao-cn/
CONTENT = os.path.join(HERE, "_content")
DOMAIN = "https://xn--6yv589c.cn"
SITE_NAME = "花桥.cn"
TODAY = "2026-09-25"
CONTACT = "mfujun@agent.qq.com"

# 栏目导航（顺序即展示顺序）
NAV = [
    ("买房", "/buy/"),
    ("买房攻略", "/articles/"),
    ("跑盘评测", "/review/"),
    ("通勤", "/commute/"),
    ("跨城办事", "/guide/"),
    ("本地黄页", "/directory/"),
    ("关于", "/about/"),
]

# 簇 → (显示名, 该簇的栏目 hub, hub 名)
CLUSTERS = {
    "decision": ("决策与是否值得", "/buy/", "买房决策"),
    "commute": ("跨城通勤", "/commute/", "通勤攻略"),
    "area": ("区域与配套", "/directory/", "本地黄页"),
    "price": ("价格与行情", "/buy/", "买房决策"),
    "process": ("交易流程与避坑", "/guide/", "跨城办事"),
    "hold": ("产品选择与持有", "/review/", "跑盘评测"),
}
CLUSTER_ORDER = ["decision", "commute", "area", "price", "process", "hold"]

DISCLAIMER = ("<strong>免责声明：</strong>本文为公开信息梳理与判断方法整理，非购房建议、非楼盘推荐。"
              "房价、政策、学区划分、税费标准以各主管部门与官方公示为准，并按年度调整。"
              "本站不代理楼盘、不介入交易、不收取开发商费用，不承担因信息滞后或误差导致的责任。")


# ---------------------------------------------------------------- 工具
def rel(target, depth):
    """从当前页深度生成到 target（以 / 开头的站内绝对路径）的相对链接"""
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
    """去标签后的正文字数（近似，按中文字符计）"""
    return len(re.sub(r"\s", "", re.sub(r"<[^>]+>", "", s)))


# ---------------------------------------------------------------- frontmatter
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


# ---------------------------------------------------------------- markdown
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
    """::faq 块 → (html, [(q, a), ...])"""
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
        # FAQ 块
        if line == "::faq":
            block, i = [], i + 1
            while i < len(lines) and lines[i].strip() != "::":
                block.append(lines[i]); i += 1
            i += 1
            h, qa = render_faq(block)
            out.append(h); faqs.extend(qa)
            continue
        # 表格
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1].strip()):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip()); i += 1
            out.append(render_table(rows))
            continue
        # 标题
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2)), lvl)); i += 1
            continue
        # 引用 → notice
        if line.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            out.append('<div class="notice">%s</div>' % inline(" ".join(buf)))
            continue
        # 无序列表
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(inline(re.sub(r"^[-*]\s+", "", lines[i].strip()))); i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % x for x in items) + "</ul>")
            continue
        # 有序列表
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(inline(re.sub(r"^\d+\.\s+", "", lines[i].strip()))); i += 1
            out.append("<ol>" + "".join("<li>%s</li>" % x for x in items) + "</ol>")
            continue
        # 段落
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{2,4}\s|[-*]\s|\d+\.\s|\||>|::)", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))
    return "\n".join(out), faqs


# ---------------------------------------------------------------- 页面模板
def header_nav(depth):
    items = "".join('\n        <a href="%s">%s</a>' % (rel(u, depth), n) for n, u in NAV)
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


# ---------------------------------------------------------------- 加载文章
def load_articles():
    arts = []
    for path in sorted(glob.glob(os.path.join(CONTENT, "*.md"))):
        with open(path, encoding="utf-8") as f:
            meta, body = parse_front_matter(f.read())
        html_body, faqs = md_to_html(body)
        wc = text_len(html_body)
        meta["_body"] = html_body
        meta["_faq"] = faqs
        meta["_wc"] = wc
        meta["_file"] = os.path.basename(path)
        arts.append(meta)
    # 校验
    slugs = [a["slug"] for a in arts]
    dup = {s for s in slugs if slugs.count(s) > 1}
    if dup:
        raise SystemExit("重复 slug: %s" % dup)
    titles = [a["title"] for a in arts]
    dup2 = {t for t in titles if titles.count(t) > 1}
    if dup2:
        raise SystemExit("重复 title: %s" % dup2)
    for a in arts:
        if a["cluster"] not in CLUSTERS:
            raise SystemExit("未知 cluster: %s (%s)" % (a["cluster"], a["slug"]))
        if a["_wc"] < 700:
            print("  [警告] 正文偏短 %s 字: %s" % (a["_wc"], a["slug"]))
    return arts


# ---------------------------------------------------------------- 文章页
def render_article(a, arts):
    slug = a["slug"]
    depth = 2
    canon = "%s/articles/%s/" % (DOMAIN, slug)
    same = [x for x in arts if x["cluster"] == a["cluster"] and x["slug"] != slug]

    # 页内目录锚点：从 h2 生成
    heads = re.findall(r"<h2>(.*?)</h2>", a["_body"])
    toc = ""
    if len(heads) >= 4:
        items = ""
        for idx, h in enumerate(heads):
            hid = "s%d" % (idx + 1)
            items += '<li><a href="#%s">%s</a></li>' % (hid, h)
        toc = '<nav class="toc"><strong>本文目录</strong><ol>%s</ol></nav>' % items
        # 给 h2 补 id
        cnt = [0]

        def add_id(m):
            cnt[0] += 1
            return '<h2 id="s%d">%s</h2>' % (cnt[0], m.group(1))
        a["_body"] = re.sub(r"<h2>(.*?)</h2>", add_id, a["_body"])

    cname = CLUSTERS[a["cluster"]]
    related = "".join('\n        <li><a href="%s">%s</a></li>' % (rel("/articles/%s/" % x["slug"], depth), x["title"])
                      for x in same[:6])

    body = """  <main class="sub-page">
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
          <li><a href="%s">%s</a>（本栏目总览）</li>%s
        </ul>
      </section>
    </div>
  </main>""" % (
        rel("/", depth), rel("/articles/", depth), esc(a["title"]),
        esc(a["title"]), esc(a.get("desc", "")),
        rel(cname[1], depth), esc(cname[2]), esc(a.get("date", TODAY)),
        toc, a["_body"],
        "本文由花桥.cn 整理，联系方式 %s。内容会随官方口径变化修订。" % esc(CONTACT),
        rel(cname[1], depth), esc(cname[2]),
        related,
    )

    jsonld = [{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": a["title"],
        "description": a.get("desc", ""),
        "datePublished": a.get("date", TODAY),
        "dateModified": a.get("date", TODAY),
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
            {"@type": "ListItem", "position": 3, "name": a["title"], "item": canon},
        ],
    }]
    if a["_faq"]:
        jsonld.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": ans}}
                           for q, ans in a["_faq"]],
        })

    # <title> 优先用 SEO 标题（更短、含核心词）；H1 用完整标题
    title = a.get("seo_title") or a["title"]
    return page(title, a.get("desc", ""), canon, depth, body, jsonld)


# ---------------------------------------------------------------- 索引页
def render_index(arts):
    depth = 1
    canon = DOMAIN + "/articles/"
    total = len(arts)

    # 关键词地图表
    rows = ""
    for k in CLUSTER_ORDER:
        name, hub, hubname = CLUSTERS[k]
        group = [a for a in arts if a["cluster"] == k]
        core = "、".join(a.get("core", "") for a in group[:3])
        rows += "<tr><td><strong>%s</strong><br><span class=\"cnt-lite\">%d 篇</span></td><td>%s…</td></tr>" % (name, len(group), esc(core))

    groups_html = ""
    for k in CLUSTER_ORDER:
        name, hub, hubname = CLUSTERS[k]
        group = [a for a in arts if a["cluster"] == k]
        if not group:
            continue
        cards = ""
        for a in group:
            cards += ('<a class="card" href="%s"><h3>%s</h3><p>%s</p>'
                      '<p class="kw">关键词：%s</p></a>'
                      % (rel("/articles/%s/" % a["slug"], depth), esc(a["title"]),
                         esc(a.get("brief", a.get("desc", ""))), esc(a.get("core", ""))))
        groups_html += ('<section class="cluster"><h2 id="%s">%s<span class="cnt">%d 篇</span>'
                        '<a class="hub-link" href="%s">进入「%s」栏目</a></h2>'
                        '<div class="grid">%s</div></section>'
                        % (k, esc(name), len(group), rel(hub, depth), esc(hubname), cards))

    body = """  <main class="sub-page">
    <div class="container">
      <h1>花桥买房攻略：%d 篇长文，按决策路径编排</h1>
      <p class="subtitle">从"该不该买"到"怎么收房"，按你正在纠结的那一步找对应文章。每篇只讲怎么查、怎么判断，不给楼盘推荐、不写死价格。</p>
      <div class="notice"><strong>怎么用这个目录：</strong>不确定从哪看起，就按下面六个选题簇对号入座；已经锁定问题，直接用表格里的核心词在站内查找。</div>
      <h2>意图地图：你搜什么，对应看哪一篇</h2>
      <div class="table-scroll">
      <table class="info-table">
        <thead><tr><th>选题簇</th><th>规模</th><th>典型核心词</th></tr></thead>
        <tbody>%s</tbody>
      </table>
      </div>
      %s
    </div>
  </main>""" % (total, rows, groups_html)

    jsonld = [{
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "花桥买房攻略",
        "description": "花桥买房主题长文合集，覆盖决策、通勤、区域配套、价格行情、交易流程、产品选择六个方向。",
        "url": canon,
        "inLanguage": "zh-CN",
        "hasPart": [{"@type": "Article", "headline": a["title"],
                     "url": "%s/articles/%s/" % (DOMAIN, a["slug"])} for a in arts],
    }]
    return page("花桥买房攻略（%d 篇）| 花桥买房长文合集 | 花桥.cn" % total,
                "花桥买房主题长文合集：决策、通勤时间、板块配套、房价查法、交易流程、公寓与持有成本，共 %d 篇，只讲查询路径与判断标准。" % total,
                canon, depth, body, jsonld)


# ---------------------------------------------------------------- hub 注入
def update_hubs(arts):
    """把各簇文章注入对应 hub 页；多个簇共用一个 hub 时合并展示（避免互相覆盖）"""
    hubs = {}
    for k in CLUSTER_ORDER:
        name, hub, hubname = CLUSTERS[k]
        group = [a for a in arts if a["cluster"] == k]
        if group:
            hubs.setdefault(hub, []).append((name, group))

    for hub, groups in hubs.items():
        depth = 1
        total = sum(len(g) for _, g in groups)
        inner = ""
        for name, group in groups:
            items = "".join('\n            <li><a href="%s">%s</a></li>'
                            % (rel("/articles/%s/" % a["slug"], depth), a["title"]) for a in group)
            inner += '\n        <h3>%s</h3>\n        <ul>%s\n        </ul>' % (esc(name), items)
        block = ('      <!-- ARTICLES:AUTO -->\n'
                 '      <section class="related">\n'
                 '        <h2>本栏目全部文章（%d 篇）</h2>%s\n'
                 '        <p><a href="%s">查看全部买房攻略 →</a></p>\n'
                 '      </section>\n'
                 '      <!-- /ARTICLES:AUTO -->' % (total, inner, rel("/articles/", depth)))
        hub_path = os.path.join(SITE, hub.strip("/"), "index.html")
        if not os.path.exists(hub_path):
            print("  [跳过] hub 不存在: %s" % hub_path)
            continue
        with open(hub_path, encoding="utf-8") as f:
            src = f.read()
        if "<!-- ARTICLES:AUTO -->" in src:
            src = re.sub(r"      <!-- ARTICLES:AUTO -->.*?<!-- /ARTICLES:AUTO -->", block, src, flags=re.S)
        else:
            marker = "    </div>\n  </main>"
            if marker not in src:
                print("  [警告] %s 未找到注入点" % hub_path)
                continue
            src = src.replace(marker, block + "\n" + marker, 1)
        with open(hub_path, "w", encoding="utf-8") as f:
            f.write(src)
        print("  hub 注入: %s（%d 篇，%d 个簇）" % (hub, total, len(groups)))


# ---------------------------------------------------------------- sitemap / robots / 404
STATIC_PAGES = [
    ("/", "1.0", "weekly"),
    ("/buy/", "0.9", "weekly"),
    ("/articles/", "0.9", "weekly"),
    ("/review/", "0.8", "weekly"),
    ("/commute/", "0.8", "weekly"),
    ("/guide/", "0.7", "monthly"),
    ("/directory/", "0.6", "monthly"),
    ("/about/", "0.3", "yearly"),
]


def write_sitemap(arts):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, pri, freq in STATIC_PAGES:
        out.append("  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority>"
                   "<changefreq>%s</changefreq></url>" % (DOMAIN, path, TODAY, pri, freq))
    for a in arts:
        out.append("  <url><loc>%s/articles/%s/</loc><lastmod>%s</lastmod><priority>0.7</priority>"
                   "<changefreq>monthly</changefreq></url>" % (DOMAIN, a["slug"], a.get("date", TODAY)))
    out.append("</urlset>")
    with open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def write_robots():
    txt = ("User-agent: *\n"
           "Allow: /\n"
           "Disallow: /_build/\n"
           "Disallow: /_content/\n"
           "\n"
           "Sitemap: %s/sitemap.xml\n" % DOMAIN)
    with open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(txt)


def write_404():
    depth = 0
    body = """  <main class="sub-page">
    <div class="container">
      <h1>页面不存在</h1>
      <p class="subtitle">这个地址没有对应的内容，可能是链接过期或输入有误。</p>
      <h2>从这里继续</h2>
      <ul>
        <li><a href="%s">花桥买房攻略（全部长文目录）</a></li>
        <li><a href="%s">买房决策：6 个先想清楚的问题</a></li>
        <li><a href="%s">跑盘评测：核实清单与公开资料梳理</a></li>
        <li><a href="%s">通勤攻略：11 号线怎么坐</a></li>
      </ul>
    </div>
  </main>""" % (rel("/articles/", depth), rel("/buy/", depth), rel("/review/", depth), rel("/commute/", depth))
    htmls = page("页面不存在 | 花桥.cn", "该页面不存在，请从花桥买房攻略目录继续浏览。",
                 DOMAIN + "/404.html", depth, body, robots="noindex,follow")
    with open(os.path.join(SITE, "404.html"), "w", encoding="utf-8") as f:
        f.write(htmls)


# ---------------------------------------------------------------- main
def main():
    arts = load_articles()
    print("载入文章 %d 篇" % len(arts))
    total_words = 0
    for a in arts:
        out_dir = os.path.join(SITE, "articles", a["slug"])
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(render_article(a, arts))
        total_words += a["_wc"]
    os.makedirs(os.path.join(SITE, "articles"), exist_ok=True)
    with open(os.path.join(SITE, "articles", "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(arts))
    update_hubs(arts)
    write_sitemap(arts)
    write_robots()
    write_404()
    print("生成完毕：%d 篇文章，正文合计约 %d 字，平均 %d 字/篇"
          % (len(arts), total_words, total_words // max(len(arts), 1)))


if __name__ == "__main__":
    main()
