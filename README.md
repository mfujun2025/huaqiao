# 花桥.cn（xn--6yv589c.cn）静态站

面向上海-花桥跨城通勤族、本地居民、潜在购房者的民间信息聚合站。
内容覆盖：跨城通勤（11号线）、跨城办事（居住证/医保/入学）、本地消费（黄页）、双城生活经验。

## 站点结构

```
huaqiao-cn/
├── index.html              # 首页
├── commute/index.html      # 跨城通勤
├── guide/index.html        # 跨城办事/落户指南
├── directory/index.html    # 本地商家黄页
├── about/index.html        # 关于 + 免责声明
├── assets/css/style.css    # 样式（移动优先、响应式）
├── CNAME                   # GitHub Pages 自定义域名（写 punycode: xn--6yv589c.cn）
├── .nojekyll               # 关闭 Jekyll，按纯静态发布
└── _config.yml             # GitHub Pages 配置
```

## 本地预览

```bash
cd huaqiao-cn
python -m http.server 8080
# 浏览器访问 http://localhost:8080/
```

## 部署状态（已完成）

- 仓库：https://github.com/mfujun2025/huaqiao （`main` 分支根目录发布）
- GitHub Pages 已启用，`build_type: legacy`，source = `main` / `/`
- 自定义域名已设为 `xn--6yv589c.cn`（punycode），仓库根目录有 `CNAME` 文件
- 本站点直接 push 到 `main` 即自动发布，无需构建步骤

### 后续更新流程

```bash
cd huaqiao-cn
git add .
git commit -m "update: 说明本次改动"
git push
```

> 本机 git 若卡在凭据交互，先 `git config credential.helper ""`，再用内嵌 token 的 remote URL + `GIT_TERMINAL_PROMPT=0` 推送。

## 绑定花桥.cn 自定义域名

### GitHub 端

仓库根目录已有 `CNAME` 文件，内容为 punycode 形式 `xn--6yv589c.cn`（GitHub 不接受中文域名，必须 punycode）。

仓库 `Settings` → `Pages` → `Custom domain` 填 `xn--6yv589c.cn` → Save → 勾选 `Enforce HTTPS`（GitHub 自动签 Let's Encrypt，需要几分钟到 24 小时）。

### DNS 端（在花桥.cn 的注册商控制面板添加）

**裸域**（让 `花桥.cn` 直接可访问）—— 4 条 A 记录 + 4 条 AAAA 记录：

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
```

**www 子域**（可选，让 `www.花桥.cn` 也可访问，GitHub 自动 301 到裸域）：

```
类型   主机记录  记录值
CNAME  www      <你的用户名>.github.io.
```

### 验证

```bash
dig xn--6yv589c.cn +short
# 应返回 185.199.108~111.153 中的一个
```

DNS 生效后访问 `http://花桥.cn` / `https://花桥.cn` 即可。

## 国内访问与 ICP 备案说明

- GitHub Pages 服务器在境外，**`.cn` 域名指向 GitHub Pages 无法做 ICP 备案**
- 未备案域名在国内访问会受运营商策略影响，速度不稳定
- 应对路径（按阶段）：
  1. **MVP 阶段**：直接 GitHub Pages，0 成本验证内容与流量
  2. **流量起来后**：接入 Cloudflare 免费 CDN 改善访问速度
  3. **盈利模式跑通后**：迁移到国内已备案服务器（阿里云/腾讯云轻量），正式 ICP 备案 `.cn` 域名

## 内容合规口径（必须守住）

- 不冒充官方（站点姿态是"民间信息聚合"，不是花桥镇政府或开发区官网）
- 不发布房源/房源价格（中国大陆房产信息发布有资质要求）
- 政策、收费、机构资质类内容**只写"去哪查、怎么判断"，不写具体金额/机构名**
- 商家黄页标注"信息聚合，非推荐"，保留商家自查指引
- 全站加免责声明（页脚已有）

## 技术约束

- 纯静态（HTML + CSS），无后端、无数据库、无用户系统
- 移动优先、响应式（适配手机/平板/桌面）
- SEO：title ≤30 全角字、description ≤80 全角字、主词"花桥"密度控制在 0.3%–0.6%
- 全站 https、canonical 已设
