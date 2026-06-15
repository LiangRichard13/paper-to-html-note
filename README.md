# Paper to HTML Reading Note

> [English README →](assets/README_en.md)

> **Token 消耗**：生成一份阅读笔记约 **60k–120k tokens**，视论文长度、流水线模式和组织策略而定。

将计算机/软件工程领域的学术 PDF 论文转换为单个自包含的 HTML 阅读笔记。支持暗色模式、侧边栏导航、内置批注系统，以及 4 种组织策略。

**单文件 HTML，不依赖外部资源。** KaTeX 首次访问时从 CDN 加载，离线回退为等宽字体。

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-%E2%89%A51.23-green)

---

## 功能

- 🌓 暗色/亮色模式（`localStorage` 持久化）
- 📑 侧边栏导航（IntersectionObserver 高亮当前位置，可折叠分组）
- 🖍 浏览器内荧光笔批注：选中高亮（6 色）、便签编辑、右侧滑动面板管理、手动保存到 HTML
- 📐 KaTeX 数学公式渲染（行内 + 展示），离线回退为等宽字体
- 🎯 4 种组织策略：论文结构对齐 / 认知先行 / 问题驱动 / 实践者视角，根据论文类型自动推荐
- 🔎 论文类型检测（系统/算法/综述/实证/立场），自动分类推荐最优策略
- 🖼 标题驱动的智能图表裁剪（矢量图形区域提取 + 文本块聚类回退）
- 📝 公式预提取——在章节重组前将公式转录为 LaTeX，保留 PDF 页面上下文
- 🔍 Lightbox 点击放大（← → Esc 键盘导航）
- 📱 移动端响应式（960px 以下侧边栏折叠为浮层）
- 📊 阅读进度条 + 滚动触发入场动画
- 📚 笔记索引页生成器——递归扫描文件夹，生成带搜索/过滤/文件树的目录页

---

## 快速开始

### 前置依赖

```bash
pip install PyMuPDF
```

推荐安装 `pdftotext`（大多数系统的 `poppler-utils` 包含）。

### 作为 Claude Code 技能使用

```
/paper-to-html-note @paper.pdf
```

技能收集论文元数据后，让你选择流水线、注释语言和组织策略：

| | Pipeline A（串行） | Pipeline B（并行） |
|---|:---:|:---:|
| **Agent 数量** | 1 | 5–12（需要 Ultracode） |
| **适用场景** | 短论文（<12页）、公式多、快速预览 | 长论文（≥12页）、图表多（>6）、综述类 |
| **Token 消耗** | ~60k–120k | ~70k–100k |
| **图表处理** | 直接 base64 内联 | `<!-- FIG:N -->` 占位符 + Python 后处理 |

---

## 组织策略

四种策略，在 Phase 0b 由用户直接选择（Agent 根据论文类型给出建议）：

| 策略 | 适合 | 逻辑 |
|------|------|------|
| 论文结构对齐 | 复习/查找 | 按论文原章节顺序，方便交叉参考 |
| 认知先行 | 初学 system/survey/position | 问题 → 核心思想 → 设计 → 结果，从零构建认知 |
| 问题驱动 | 初学 algorithm/empirical | 每节是一个问题 + 答案，FAQ 风格 |
| 实践者视角 | 评估 | 第一人称叙事："我为什么读""我哪里谨慎""何时用" |

---

## 图表提取：标题驱动的智能裁剪

学术 PDF 图表是矢量图形，不是嵌入的栅格图像。提取器融合四种信号——纯几何分析，不依赖外部模型或 API：

```
                正文段落（通栏，>150 字符）
                  ↓ 约束上边界
  ┌──────────────────────────────────┐  ← 图表顶部
  │    矢量图 ██████████              │  ← 绘图密度收紧边界
  │    （或文本块聚类回退）            │
  │    图表内容                       │
  ├──────────────────────────────────┤  ← 底部 = 标题顶部 − 2pt
  │  Fig. 1. Overview of ...         │  ← 标题锚点
  └──────────────────────────────────┘
```

覆盖约 95% 的 CS 论文。纯文字图表（分类树、流程图）使用文本块聚类回退。提取前会做快速预检——扫描 "Fig."/"Figure" 标题判断是否需要执行。

### 独立使用

```bash
python scripts/extract_figures.py paper.pdf --dpi 200 -o figures.json
python scripts/extract_figures.py paper.pdf --dpi 200 --save-images
```

---

## HTML 组件

| 组件 | 用途 |
|------|------|
| `.callout`（6 种变体） | 见解、警告、要点、设计动机 |
| `.grid-2 > .mini-card` | 并行概念、对比 |
| `.pbox` 编号列表 | 设计原则、规则 |
| `table` inside `.table-wrap` | 架构对比、分类、基准 |
| `figure.paper-fig` | 内嵌图表（Lightbox 放大 + 懒加载） |
| `.summary-grid` | 关键指标仪表板 |
| `.formula-display` / `.formula-inline` | KaTeX 公式 |
| `pre` + 语法高亮 | 伪代码和代码 |
| `.mindmap` | 概念可视化 |
| `.trace` 有序列表 | 编号流程 |

---

## 笔记索引

生成的笔记可以通过索引页进行浏览和检索。在笔记目录下运行：

```bash
python scripts/build_manifest.py /path/to/notes/dir
```

这会生成一个自包含的 `index.html`，支持搜索、按论文类型过滤、文件树导航、批注预览。详情见 `SKILL.md` 中的 Note Indexing 节，或通过 `/paper-to-html-note` skill 的"构建索引"功能自动创建。

---

## 上下文安全（Pipeline B）

Pipeline B 通过文件 I/O 隔离，base64 图片数据不进入 LLM 上下文：

| 阶段 | 返回内容 | 上下文占用 |
|------|---------|:--------:|
| B1 并行提取 | JSON 元数据（图表 ID、公式 LaTeX） | <2KB |
| B2 章节分配 | 章节分配 + 上下文信息 | <5KB |
| B3 并行撰写 | `{section_id, num, title, file_path}` | ~50B × N |
| B3.5a 质量评审 | 结构化评审 JSON | <1KB |
| B3.5b 连贯性验证 | 成对编辑 + div 安全验证 | 0（shell） |
| B4 组装 | `assemble_figures.py` + 按序拼接 | **0 tokens** |
| B4c 最终检查 | 读取 `sections_meta.json` + `paper_meta.json` | <2KB |

---

## 示例

来自 "Towards Personalized LLM-Powered Agents"（29 页综述，8 张图，中文注释）的阅读笔记：

> [📄 在线查看 →](https://htmlpreview.github.io/?https://github.com/LiangRichard13/paper-to-html-note/blob/master/assets/examples/toward_personalized_llm_powered_agents_reading_notes.html)

<img src="assets/examples/screenshot.png" alt="阅读笔记截图" width="720">

包含 6 个内容章节（基础 → 记忆 → 画像 → 检索 → 进化 → 评估）、内嵌架构图、见解标注框、分类对比表、摘要仪表板，以及完整的浏览器内批注系统。

---

## 项目结构

```
paper-to-html-note/
  SKILL.md
  README.md
  LICENSE
  pyproject.toml
  assets/
    README_en.md
    template.html              # 中文模板
    template_en.html           # 英文模板（结构一致）
    index-template.html        # 笔记索引页模板
    examples/
      screenshot.png
      toward_personalized_llm_powered_agents_reading_notes.html
  references/
    component-catalog.md
    design-system.md
  scripts/
    extract_figures.py
    assemble_figures.py
    build_manifest.py          # 索引生成器
```

---

## 适用论文

针对 CS/SE 学术论文优化（arXiv、ACM、IEEE、NeurIPS、ICML 等）：双栏/单栏、通栏/跨栏图表、矢量图形、数学公式、纯文字图表。

## 局限性

| 场景 | 表现 |
|------|------|
| 扫描版 PDF（纯栅格） | 回退为标题位置估算 |
| 非英文标题（"図 1"） | 不识别，需扩展正则 |
| 三栏排版 | 正文段落检测可能不准 |
| 标题在图表上方（旧式排版） | 裁剪错误 |
| 跨页图表 | 可能被页面切断 |

## 依赖

- Python 3.9+
- PyMuPDF（`fitz`）
- KaTeX（CDN 加载，离线回退等宽字体）
- pdftotext（可选，加速文本提取）

## 许可证

MIT
