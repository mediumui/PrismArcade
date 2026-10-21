# Prism Arcade — SEO / GEO 项目规范

> 适用范围：本仓库（`arcade-site/`）所有页面的新增与改动。
> 目的：每次新增游戏 / 新增页面，**必须同步完成下列 SEO/GEO 动作**，否则站点会被搜索引擎漏收录、被 AI 答案引擎（ChatGPT / 豆包 / 文心 / Perplexity / Claude）降权或漏引用。
> 本规范经线上 `geo_audit.py` 审计验证：7 项检查全部 PASS，原唯一 P0 阻断项 `llms.txt` 已 HTTP 200。
> 本文件位于 `tools/`，已被 `.assetsignore` 排除，**不会被公开部署**，仅作开发期规范。

---

## 一、新增一个游戏（强制清单）

按 A→E 顺序执行，每步都不可省。

### A. 写入数据源 `tools/seo_games_data.json`
新增一项（键为 slug，如 `"snake.html"`）：
```json
"<slug>.html": {
  "name": "游戏显示名",
  "title": "Play <Name> Online No Download - <类型> | Prism Arcade",
  "desc": "真实、独特的英文描述，一句话讲清玩法与免费/无下载",
  "og_title": "与 title 一致的 OG 标题",
  "category": "PuzzleGame | Game | BrainGame …（schema.org 游戏类）",
  "playmode": "SinglePlayer | TwoPlayer",
  "overview": "2-3 句概述，首句即自包含直接答案",
  "faq": [
    { "q": "Can I play <Name> online for free?", "a": "Yes. … no download, no sign-up, no payment." },
    { "q": "How do I control <Name>?", "a": "用箭头键 / 触屏按钮 …" },
    { "q": "What is the goal of <Name>?", "a": "…" }
  ],
  "related": [
    { "name": "同类游戏A", "file": "a.html", "desc": "…" },
    { "name": "同类游戏B", "file": "b.html", "desc": "…" },
    { "name": "同类游戏C", "file": "c.html", "desc": "…" }
  ]
}
```
- `title` / `desc` / `og_title` 必须**真实独特**，禁止复制其它游戏文案。
- `faq` 至少 2–3 条，问法要能被 AI 直接引用（"Can I play X online for free?" / "How do I control X?"）。

### B. 跑 SEO 注入管线
```bash
python tools/seo_inject_games.py
```
- 幂等，标记 `<!-- SEO:INJECTED v1 -->`，已注入的页会跳过。
- 自动重写 `<head>`（title / description / robots / canonical / OG / Twitter）、注入 JSON-LD（**WebPage + BreadcrumbList + Game + FAQPage**）、插入可见 FAQ 区块 + Related Games 区块（位于 `</main>` 前）。
- **绝不改动游戏逻辑 / CSS / JS**。

### C. 补 GEO 玩法段
在 `tools/geo_add_howto.py` 的 `HOWTO` 字典里新增：
```python
"<slug>.html": [
  "第 1 步：针对该游戏的具体操作",
  "第 2 步：…",
  "第 3 步：…",
  "第 4 步：…",
],
```
然后重跑：
```bash
python tools/geo_add_howto.py
```
- 幂等，标记 `<!-- GEO:HOWTO v1 -->`，自动插入在 Overview 与 FAQ 之间。
- 步骤要从 `seo_games_data.json` 取 `name` 拼标题，所以 A 步必须先做。

### D. 更新 `llms.txt`（站点根 `arcade-site/llms.txt`）
- 在对应分类小标题下新增一行（三分类见文件内 `### Reflex & Reaction` / `### Puzzle & Strategy` / `### Memory & Brain`）：
  `- [游戏名](https://www.prismarcade.top/games/<slug>.html) — 真实描述`
- 若游戏**总数变化**：同步更新顶部 Overview 段的数字（当前 22）与 FAQ 里的 "22 browser games"。
- 末尾 6 条 FAQ 保持不动。

### E. 更新 `sitemap.xml`
- 必须包含新页面 URL：`https://www.prismarcade.top/games/<slug>.html`。
- 若 sitemap 由脚本生成 → 重跑生成；若手维护 → 手动加 `<url>` 块。

### F. 美术质量（强制，禁止只做"贴块"）
新增游戏**不允许**只画裸矩形 / 裸三角形 / 单色色块当主体就交付（早期 runner 就是"一个正方形+三角形"被用户点名要求重做）。游戏画面主体（canvas 或 DOM）必须达到下列基准，参考已升级的 9 款（snake / stack-tower / maze / flappy / whack / reflex-relay / sequence / block-slide / quick-tap）：

**Canvas 游戏至少具备：**
1. **分层背景**——夜空/环境渐变（`createLinearGradient`）+ 闪烁星或网格，禁止纯黑/纯白底。
2. **主体发光**——玩家与障碍用 `shadowColor`+`shadowBlur` 做霓虹光晕，主体用渐变填充而非单色 `fillRect`。
3. **角色有"脸"或识别特征**——眼睛 / 高光 / 圆角，不是素方块。
4. **动效反馈**——跳跃/落地/撞击/得分有粒子（`particles` 数组）；死亡有红闪或屏幕震动。
5. **闲置预览**——游戏未开始时有 `idleLoop` 持续渲染背景，让画面"活着"。

**DOM 游戏至少具备：**
1. **状态色+光晕**——active / lit / target 态用 `box-shadow`（外光晕）+ `inset`（内光）做霓虹，禁止只贴一层 `rgba` 平涂。
2. **图形化图标**——用图形 / SVG / CSS 造型（圆碟、靶心、字形）替代 emoji 或 `#`/`+`/纯字母当图标。
3. **过渡**——关键状态加 `transition`（transform / box-shadow / background）。
4. **配色体系**——复用 `style.css` 的紫橙霓虹系（`#7c5cff` / `#ffb347` / `#ffd24d` / `#36d399` / `#4aa3ff`），不要随机撞色。

**验收**：交付前自问"画面有没有'发光/层次/动效'，还是只贴了个色块？"——后者打回重做。


---

## 二、新增非游戏页面（about / contact / privacy / 新栏目，强制清单）

- `<head>` 必备：真实 `title` + `meta description` + `canonical` + 全套 OG/Twitter + `robots: index,follow`。
- 至少一段 JSON-LD：
  - **首页 `index.html`**：`WebSite` + `ItemList` + `Organization` + `FAQPage`（四段齐全）。
  - **`about.html`**：`Organization` + 「at a Glance」事实枢纽（4 张事实卡）+ `Publisher` 发布者块（明确无账号 / 无付费 / 无个人数据采集）。
  - 其它页：`WebPage` + 恰当的 `FAQPage` / `BreadcrumbList`。
- 首段 = **自包含直接答案**（不依赖上下文也能看懂，AI 最易引用）。
- 若有 FAQ，可见区块与 JSON-LD 必须同源。
- 更新 `llms.txt` 的 `## Key Pages`。
- 加入 `sitemap.xml`。

---

## 三、全站硬性规则（不要违反）

1. **不注水凑字数**。AI 按「段落（约 40–80 词）」检索引用，不是按整页长度。游戏页 300–700 词是甜区；硬凑到 2000 词反而稀释每段 embedding、降低被引概率。内容长度不是排名因素（Google 官方确认无最低字数）。
2. **Organization 的 `sameAs` 只填真实存在的社媒账号**。不存在就别加——曾误加 `https://x.com/prismarcade`（无该账号）已移除，避免假实体信号。
3. **保留标记隔离**：`SEO:INJECTED` / `SEO:CLEANED` / `GEO:HOWTO` 互不影响；重跑脚本前确认幂等，避免重复注入。重做前用 `tools/seo_clean_games.py` 清理。
4. **全站英文界面**（目标用户是海外玩家）；meta / 结构化数据一律英文。
5. **生产域名固定 `https://www.prismarcade.top`（带 www）**。`canonical` / `og:url` / sitemap `<loc>` / `llms.txt` 链接全部用这个，不要用裸域或 `example` 占位。
6. **美术底线**：新增游戏的画面主体必须做"霓虹发光+分层背景+动效"，禁止只做贴块（裸矩形/裸三角/单色色块/纯字母图标）。详见「一.F 美术质量」。DOM 游戏的发光态必须用 `box-shadow` 真光晕，不许只贴一层 `rgba` 平涂。

---

## 四、上线前校验

本地：
```bash
python -m http.server 8080 --directory arcade-site
# 另开一个终端：
python <geo-optimizer技能>/scripts/geo_audit.py http://localhost:8080
```
→ 7 项必须全 PASS（`llms.txt` 尤其要 200）。

推送与部署：
```bash
git add <改动的游戏页 / llms.txt / sitemap.xml / 数据文件 / 脚本>
git commit -m "Add <game>: SEO+GEO (inject, how-to, llms.txt, sitemap)"
git push origin main      # Cloudflare 自动部署
```
- 部署后，对 `https://www.prismarcade.top` 复跑 `geo_audit.py`，确认 `llms.txt` 转 200。
- ⚠️ 沙箱坑：`sleep 300 && <网络抓取>` 链式命令会被拦截（`decisionRecord missing actual resource subject`）。审计**单独跑**即可，不要和 sleep 串一条。

---

## 五、关键文件与脚本速查

| 文件 / 脚本 | 作用 |
|---|---|
| `tools/seo_games_data.json` | 游戏数据源（驱动注入管线 + how-to 取 name） |
| `tools/seo_inject_games.py` | SEO 注入：head + JSON-LD(WebPage/Breadcrumb/Game/FAQ) + FAQ + Related，标记 `SEO:INJECTED v1` |
| `tools/seo_clean_games.py` | 清理注入（重做前用） |
| `tools/geo_add_howto.py` | GEO 玩法段注入：How to Play 块，标记 `GEO:HOWTO v1` |
| `arcade-site/llms.txt` | AI 爬虫首选文件（手动维护，新增游戏必改） |
| `arcade-site/robots.txt` `sitemap.xml` | 抓取与收录 |
| `arcade-site/.assetsignore` | 排除 `tools/` 等内部目录，避免公开部署 |

---

## 六、一个判断原则（给未来的自己）

> **问"这段内容 AI 能不能直接当答案引用？"** 而不是"够不够 2000 字？"
> 能独立成立、含事实/数字/步骤的段落，比注水长文更容易被引用。证据密度（统计、引用、引语）> 字数。

## 七、美术质量判断原则（给未来的自己）

> **问"这个画面像不像'一个产品'，还是只贴了个色块？"**
> 贴块 = 裸矩形/裸三角/单色 fillRect/纯字母当图标/只有一层 rgba 平涂 → 打回重做。
> 达标 = 有发光（shadowBlur / box-shadow）、有层次（渐变背景/视差）、有反馈（粒子/动效/闲置预览）。
> 参考基准：`games/snake.html`、`games/whack.html`（最弱两款的升级后形态），照它做就不会"太丑"。
