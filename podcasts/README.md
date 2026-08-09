# 本周电波 · 播客文稿库

把每周听的播客中文文稿，整理成一个可阅读、可持续更新的单页网站。

**打开** `index.html` 即可阅读（完全自包含，无需服务器、无外部依赖）。

---

## 最省事的用法：推文稿就行（自动流水线）

仓库配了 GitHub Action（`.github/workflows/podcasts.yml`）。**你只要把新文稿 `.md` 放进 `podcasts/transcripts/` 并推到 `main`**，CI 会自动：

1. 运行 `ingest.py`：内容重复的自动跳过；新文稿自动解析文头，在 `manifest.json` 里生成一条「草稿」条目（卡片标 **待整理**）；
2. 运行 `build.py` 重建 `index.html`，并提交回仓库；
3. 部署到 **GitHub Pages**，固定网址自动更新。

> 分类、要点、导语这类需要判断的字段，草稿里先留空（不影响先能读）。想润色时改 `manifest.json` 里那条、再推一次即可。

**首次启用**：把本分支合并进 `main`，Action 会在首次运行时自动开启 Pages。网址为
`https://<你的用户名>.github.io/<仓库名>/`。若组织限制了自动开启，去 **Settings → Pages → Source** 选 **GitHub Actions** 即可。

本地想手动跑同样的流程：`python3 podcasts/ingest.py`（收录+构建），或 `--dry-run` 只看会发生什么。

---

## 目录结构

```
podcasts/
├── index.html          # 构建产物 —— 直接打开阅读的页面（自包含）
├── manifest.json       # 唯一的元数据源：节目列表、分类、首页文案
├── transcripts/        # 每集一个 .md 文稿（完整中文整理）
│   ├── oddlots.md
│   ├── hardfork.md
│   └── …
├── template.html       # 页面外壳（CSS + 交互逻辑 + 占位符）
├── build.py            # 构建脚本：template + manifest + transcripts → index.html
└── README.md
```

**改动流程永远是：改数据 → `python3 build.py` → 提交。** 不要手改 `index.html`（它是生成的，会被覆盖）。

---

## 新增一集（三步）

### 1. 放文稿
把整理好的 Markdown 文稿存成 `transcripts/<id>.md`，`<id>` 用简短英文小写（如 `oddlots-gold`）。
文稿用标准 Markdown 即可：`#`/`##`/`###` 标题、`**加粗**`、表格、`>` 引用、列表、`---` 分隔线都支持。
（`##` 二级标题会自动成为阅读页左侧的章节目录。）

### 2. 在 `manifest.json` 的 `episodes` 数组里加一条
按日期倒序放到合适位置（最新在最前）：

```json
{
  "id": "oddlots-gold",
  "file": "oddlots-gold.md",
  "ep": "#2F9E93",
  "show": "Odd Lots · Bloomberg",
  "eyebrow": "大宗商品 / 宏观",
  "title": "黄金为什么又创新高",
  "date": "2026·08·20",
  "dur": "访谈",
  "host": "Tracy Alloway、Joe Weisenthal",
  "guest": "某某某",
  "tags": ["黄金", "央行购金", "去美元"],
  "cats": ["energy", "invest"],
  "blurb": "一句话导语，说清这集在讲什么、为什么值得读。",
  "hl": [
    "本集要点第一条：最锋利的结论",
    "第二条",
    "第三条"
  ]
}
```

### 3. 构建
```bash
python3 build.py          # 生成 index.html
# 或 python3 build.py --check  只校验不写文件
```
构建会校验字段完整性、分类是否合法、文稿是否存在、以及是否含会破坏页面的 `</script`。
首页的「档节目 / 档制作方」计数会自动根据 `episodes` 重算，无需手动改。

---

## 字段说明

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | ✓ | 唯一英文小写标识，也是文件名 |
| `file` | ✓ | `transcripts/` 下的文稿文件名（一般 = `<id>.md`） |
| `ep` | ✓ | 该集强调色（hex）。**同一档节目建议共用一个颜色**，见下表 |
| `show` | ✓ | 节目名，`·` 前的部分用于「制作方」计数 |
| `eyebrow` | ✓ | 卡片上节目名后的小标签，如 `AI / 半导体` |
| `title` | ✓ | 标题 |
| `date` | ✓ | 形如 `2026·08·07`（用于展示，排序由数组顺序决定） |
| `dur` | | 时长/形态，如 `62 min`、`访谈`、`EP 485` |
| `host` / `guest` | | 主持人 / 嘉宾 |
| `tags` | | 关键词药丸（数组） |
| `cats` | ✓ | 分类键数组，用于首页筛选（见下）。可多选 |
| `blurb` | ✓ | 一句话导语 |
| `hl` | ✓ | 「本集要点」3 条左右，卡片与阅读页顶部都会显示 |

### 分类键（`cats` 可选值）
定义在 `manifest.json` 的 `categories` / `categoryOrder`：

`ai` AI 与算力 · `invest` 投资与市场 · `geo` 地缘与安全 · `china` 中国 · `energy` 能源与大宗 · `robotics` 机器人 · `consumer` 消费与供应链

要新增一个分类：在 `categories` 里加 `"键":"中文名"`，并把键加进 `categoryOrder`。

### 各节目建议配色（保持同一节目一致）
| 节目 | 颜色 |
|---|---|
| Odd Lots | `#2F9E93` |
| Hard Fork | `#CF8A3A` |
| ChinaTalk | `#7E8B44` |
| 20VC | `#8B6FC7` / `#4F7DC9` |
| Invest Like the Best | `#C05A44` |
| All-In | `#5E7C88` |
| Latent Space | `#C15F8A` |
| Sinica | `#9E4E5E` |

---

## 首页文案

改 `manifest.json` 的 `meta`（`weekLabel` / `heroTitle` / `heroLead` / `statHours` / `brand`），再 `build.py` 即可。
