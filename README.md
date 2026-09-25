# 花桥.cn（xn--6yv589c.cn）静态站

花桥买房决策信息服务（纯静态，无后端）。面向"在上海上班、考虑在花桥（江苏昆山）买房"的人群。
内容覆盖：买房决策、跨城通勤、板块配套、房价查法、交易流程、持有成本。

- **仓库**：https://github.com/mfujun2025/huaqiao （`main` 分支根目录发布）
- **主域名**：`xn--6yv589c.cn`（中文域名「花桥.cn」的 punycode，GitHub Pages 只认 punycode）
- **规模**：8 个正式页 + 28 篇文章页 = 37 个页面，正文约 6.2 万字
- **更新日期**：2026-09-25

## 目录结构

```
huaqiao-cn/
├── index.html                 首页（6 个栏目入口 + 精选文章内链）
├── buy/                       买房决策页（栏目 hub）
├── articles/                  买房攻略目录（按 6 簇分组，带意图地图表）
│   └── <slug>/index.html      28 篇文章（slug 全 ASCII）
├── review/                    跑盘评测（栏目 hub）
├── commute/                   通勤攻略（栏目 hub）
├── guide/                     跨城办事（栏目 hub）
├── directory/                 本地黄页（分类筛选 + 商家卡片）
├── about/                     关于与免责
├── 404.html  robots.txt  sitemap.xml  CNAME  .nojekyll
├── assets/css/style.css       单文件样式（移动优先、响应式）
└── _build/                    ★ 构建工具
    ├── build.py               文章构建：_content/*.md → articles/
    ├── _content/*.md          28 篇文章源文件（markdown + frontmatter）
    ├── check_site.py          静态自检（链接/锚点/meta/标签配对/JSON-LD/title 唯一/正文体量）
    └── patch_nav_all.py       统一全站导航 + 清理编辑器注入属性
```

`_build/` 会被 GitHub Pages 一并发布（有 `.nojekyll`），已在 `robots.txt` 中 `Disallow`。文章源文件本身是内容，暴露无害。

## 本地预览

```bash
cd huaqiao-cn
python -m http.server 8080
# 浏览器访问 http://localhost:8080/
```

## 怎么加一篇新文章（三步）

**第 1 步**：在 `_build/_content/` 新建 `<slug>.md`（slug 用英文/拼音，**不要中文文件名**）：

```markdown
---
title: 页面上显示的完整标题（用用户问句形态）
seo_title: <title> 标签用（含核心词，≤30 全角字）
slug: your-slug
cluster: decision      # decision / commute / area / price / process / hold
core: 核心关键词
longtail: 长尾词1|长尾词2|长尾词3
desc: description（≤80 全角字，含核心词）
brief: 目录页卡片显示的一句话
date: 2026-09-25
---

正文从 h2 开始写，语法支持：
- ## / ### / ####        标题
- 标准 markdown 表格      → 自动包进 .table-scroll 容器（窄屏内横滑）
- - / 1.                 无序 / 有序列表
- > 提示                   渲染成 .notice 高亮块
- **加粗**、[链接](url)、`代码`

::faq
Q|用户实际搜索的问句？
A|答案。
::
```

**第 2 步**：构建 + 自检（自检必须全绿再提交）

```bash
python _build/build.py       # 生成文章页、重写目录页、注入 hub 列表、重建 sitemap
python _build/check_site.py  # 7 项静态自检
```

**第 3 步**：提交推送

```bash
python _build/patch_nav_all.py   # 统一导航 + 清理编辑器注入属性（提交前必跑）
git add . && git commit -m "content: 新增 XX 篇"
git push
```

构建会自动完成：文章页（含 Article / BreadcrumbList / FAQPage 结构化数据、页内目录锚点、同簇互链）、`/articles/` 目录页重写、hub 页文章列表注入（`<!-- ARTICLES:AUTO -->` 区块）、`sitemap.xml` 重建。

## 内容红线（不得突破）

1. **政策、价格、资质类信息只写"去哪查、怎么判断"，不写死具体数字。** 房价、税率、首付比例、社保年限、学区划片都会随年度调整，写死即埋雷，且会误导读者。
2. **不推荐、不评价任何具体机构**（中介、银行、验房、装修）。避坑类内容只给核查方法，不给白名单也不给黑名单。
3. **不写具体楼盘评价**。跑盘页只做"公开资料梳理 + 待实地核实清单"；价格只给查询渠道（备案价公示 / 一房一价 / 周边二手成交）。
4. **每个页面保留免责声明**，全站口径一致。
5. **付费内容必须标注「广告」**（黄页置顶条目），且不改变非付费条目的信息完整度。

> 这五条的直接效果是：内容**不需要按季度返工**。因为写的是方法和路径，不是会过期的数字。

## 维护约定

| 频率 | 动作 |
|---|---|
| 每两周 | 加 2–3 篇新文章（`_content/` 新建 md → 构建 → 自检 → 推送） |
| 每季度 | 检查文中的**查询路径描述**是否仍成立（办事栏目改名、系统迁移等） |
| 每年初 | 复核政策流程类页面，**只更新"流程步骤"，不新增具体数字** |
| 每次更新 | 更新 frontmatter 的 `date`，重建 sitemap |

**不要把具体金额、税率、社保年限、机构名单填回文章里。** 这份红线是给下一位接手的人写的（包括未来的自己）。

## 部署状态

- GitHub Pages 已启用，`build_type: legacy`，source = `main` / `/`
- 自定义域名已设为 `xn--6yv589c.cn`（punycode），根目录有 `CNAME` 文件
- 推送 `main` 即自动发布，无需构建步骤（文章页是预生成的静态文件）

### 后续更新流程

```bash
cd huaqiao-cn
python _build/build.py && python _build/check_site.py && python _build/patch_nav_all.py
git add . && git commit -m "update: 说明本次改动" && git push
```

> 本机 git 若卡在凭据交互或推送被拦截，先 `git config credential.helper ""`，再用内嵌 token 的 remote URL + `GIT_TERMINAL_PROMPT=0` 推送；仍失败则走 GitHub 数据 API 通道。

## 绑定花桥.cn 自定义域名

### GitHub 端

仓库根目录已有 `CNAME` 文件，内容为 punycode `xn--6yv589c.cn`（GitHub 不接受中文域名）。

`Settings` → `Pages` → `Custom domain` 填 `xn--6yv589c.cn` → Save → 勾选 `Enforce HTTPS`（自动签 Let's Encrypt，通常几分钟到几十分钟）。

### DNS 端（在花桥.cn 的 DNS 服务商面板操作）

**方案 A（推荐）**：Cloudflare 里把 `@` 改为**灰云（DNS only）**，4 条 A 记录指向 GitHub Pages：

```
类型   主机记录  记录值
A      @        185.199.108.153
A      @        185.199.109.153
A      @        185.199.110.153
A      @        185.199.111.153
AAAA   @        2606:50c0:8000::153
AAAA   @        2606:50c0:8001::153
AAAA   @        2606:50c0:8002::153
AAAA   @        2606:50c0:8003::153
CNAME  www      mfujun2025.github.io.
```

**方案 B**：保持橙云代理，则须在 CF 确认 `SSL/TLS = Full`、`Always Use HTTPS = On`。此时 GitHub 签不下专属证书属正常现象。

### 验证

```bash
dig xn--6yv589c.cn +short     # 应返回 185.199.108~111.153 中的一个
curl -sI https://xn--6yv589c.cn/   # 应返回 200
```

## 国内访问与 ICP 备案说明

- GitHub Pages 服务器在境外，**`.cn` 域名指向 GitHub Pages 无法完成 ICP 备案**
- 未备案域名在国内访问受运营商策略影响，速度不稳定
- 应对路径（按阶段）：
  1. **MVP 阶段**：直接 GitHub Pages，0 成本验证内容与流量
  2. **流量起量后**：接入 Cloudflare 免费 CDN 改善访问速度
  3. **需要备案时**：迁移到国内服务器（阿里云/腾讯云轻量），正式完成 ICP 备案

## 技术约束与验证记录

- 纯静态（HTML + CSS + 原生 JS，仅黄页筛选用到少量 JS），无后端、无数据库、无用户系统
- 移动优先、响应式；无第三方依赖（不加载外部字体/脚本，保证国内访问速度）
- SEO：`<title>` ≤30 全角字、description ≤80 全角字、核心词密度 0.3%–0.6%、canonical 全绝对地址
- 结构化数据：文章页含 Article + BreadcrumbList + FAQPage；目录页含 CollectionPage
- FAQ 用原生 `<details>` 折叠（首屏零阻塞、爬虫可读全文）
- **验证记录（2026-09-25）**：37 页自检全绿；桌面 1440px 与移动 390px（iframe 外壳法）渲染正常，无横向溢出

### 已知环境注意点

- 本机 `git push` 可能被 SIGTERM 拦截 → 走 GitHub 数据 API 通道
- 某些编辑器会持续往 HTML 注入 `data-page-node-id` 属性 → **提交前跑 `python _build/patch_nav_all.py`**
- 本机无头渲染验证用 Edge：`--headless=old --window-size=1440,1800 --virtual-time-budget=8000`
  **窄屏验证不要用 `--window-size=390`**（宽度会被钳制到约 500px 造成伪影），改用固定宽度 iframe 的外壳页
