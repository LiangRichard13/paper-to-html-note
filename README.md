# Paper to HTML Reading Note

> [**English README** →](assets/README_en.md)

> **⚠️ Token 消耗**：生成一份完整的阅读笔记大约消耗 **60k–120k tokens**（视论文长度、流水线模式和组织策略而定）。请合理规划预算。

将计算机/软件工程领域的学术 PDF 论文转换为**自包含、可交互的 HTML 阅读笔记**——暗色模式、侧边栏导航、丰富的组件库，并支持根据阅读意图选择 **4 种组织策略**。注释语言由用户选择（简体中文或英文）。

**单个 HTML 文件，零外部依赖。** KaTeX 在首次访问时从 CDN 加载，离线时回退为等宽字体。

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-%E2%89%A51.23-green)

---

## 功能特性

- 🌓 **暗色/亮色模式**——跨会话持久化到 `localStorage`
- 📑 **粘性侧边栏**——IntersectionObserver 高亮当前章节，可折叠分组
- 🔗 **h2 锚点链接**——悬停显示 `#` 链接，点击触发章节闪烁动画
- 📊 **阅读进度条**——accent→cyan 渐变色
- 🖼 **智能图表裁剪**——从 PDF 中提取单个图表区域（非整页），对纯文字图表提供文本块聚类回退
- 📐 **KaTeX 数学公式渲染**——行内 `$...$` 和展示 `$$...$$`，离线时回退为等宽字体
- 🔍 **Lightbox 点击放大**——键盘导航（← → Esc），上一张/下一张按钮
- 🎬 **滚动触发入场动画**——前 2–3 个章节淡入显示
- 📱 **移动端响应式**——960px 以下侧边栏折叠为 ☰ 浮层；表格可滑动并显示滚动指示器
- 📋 **代码复制按钮**——悬停 `<pre>` 块显示剪贴板复制按钮
- 🖨 **打印优化**——隐藏操作界面，展开所有章节，约束图片尺寸
- 📋 **6 种标注框类型** + 3 种网格布局 + 6 种标签颜色 + 语法高亮代码块
- 🌐 **用户自选注释语言**——中文（默认）或英文
- 🎯 **4 种组织策略**——根据阅读意图选择内容的排序方式
- 🔎 **论文类型检测**——自动分类（系统/算法/综述/实证/立场论文），推荐最优策略
- 📝 **公式预提取**——在章节重组之前将公式转录为 LaTeX，保留 PDF 页面上下文
- 🖍 **浏览器内荧光笔批注**——选中文本即可高亮，6 种荧光色可选；点击高亮区域换色、删除或弹出便签编辑批注；右侧滑动面板管理所有批注，支持 localStorage 持久化

---

## 快速开始

### 前置依赖

```bash
pip install PyMuPDF
```

推荐安装 `pdftotext` 用于文本提取（大多数系统的 `poppler-utils` 包中包含）。

### 作为 Claude Code 技能使用

```
/paper-to-html-note @paper.pdf
```

技能首先收集论文元数据（页数、图表数量），从摘要和标题检测论文类型，然后引导您选择流水线、注释语言和**阅读意图**（映射为一种组织策略）：

| | Pipeline A（串行） | Pipeline B（并行） |
|---|:---:|:---:|
| **Agent 数量** | 1 | 5–12（需要 Ultracode） |
| **适用场景** | 短论文（<12页）、公式多、快速预览、实践者叙事 | 长论文（≥12页）、图表多（>6）、综述类、认知先行 |
| **Token 消耗** | ~60k–120k | ~70k–100k（架构节省抵消开销） |
| **输出风格** | 单 Agent 一致性 | 每章节独立 Agent，分析更深 |
| **图表处理** | 直接 base64 内联嵌入 | `<!-- FIG:N -->` 占位符 + Python 后处理 |
| **质量保障** | 撰写者自检 + 29 项检查清单 | B3.5 评审 Agent + B3.5b 连贯性 Agent + B4c 结构验证 |

---

## 组织策略

阅读笔记可按四种方式组织，根据**阅读意图** × **论文类型**自动选择：

| 策略 | 适用场景 | 工作原理 |
|------|---------|---------|
| **论文结构对齐**（paper-structure-aligned） | 复习已读内容 | 章节按论文自身结构排列——便于交叉参考 |
| **认知先行**（cognition-first） | 初次阅读（系统/综述/立场论文） | 从问题 → 核心思想 → 设计 → 结果 → 启示逐步构建理解 |
| **问题驱动**（question-driven） | 初次阅读（算法/实证论文）或快速评估 | 每个章节就是论文回答的一个问题——FAQ 风格 |
| **实践者视角**（persona-driven） | 实践者评估 | 以实践者视角进行对话式叙述 |

### 策略选择逻辑

| 意图 | system | algorithm | survey | empirical | position |
|------|--------|-----------|--------|-----------|----------|
| 复习 | paper-structure | paper-structure | paper-structure | paper-structure | paper-structure |
| 初学 | cognition-first | question-driven | cognition-first | question-driven | cognition-first |
| 查找 | paper-structure | paper-structure | question-driven | paper-structure | question-driven |
| 评估 | question-driven | question-driven | cognition-first | question-driven | cognition-first |

---

## 图表提取：标题驱动的智能裁剪

学术 PDF 中的图表是**矢量图形**（drawings），而非嵌入的栅格图像。内置提取器融合了四种信号——**无需外部模型或 API**，纯几何分析，仅依赖 PyMuPDF：

```
                正文段落（通栏，>150 字符）
                  ↓ 约束上边界
  ┌──────────────────────────────────┐  ← 图表顶部
  │    矢量图 ██████████              │  ← 绘图密度收紧边界
  │    （或文本块聚类）               │  ← v4.1 回退
  │    图表内容                       │
  ├──────────────────────────────────┤  ← 图表底部 = 标题顶部 − 2pt
  │  Fig. 1. Overview of ...         │  ← 标题锚点
  └──────────────────────────────────┘
```

覆盖约 95% 的计算机科学论文；纯文字图表（分类树、表格、流程图）使用 v4.1 文本块聚类回退。

在运行完整提取器之前会进行**快速预检**——扫描所有页面的 "Fig."/"Figure" 标题，判断是否需要执行提取。

### 独立图表提取

```bash
python scripts/extract_figures.py paper.pdf --dpi 200 -o figures.json

# 同时保存为独立 PNG
python scripts/extract_figures.py paper.pdf --dpi 200 --save-images
```

---

## HTML 组件库

| 组件 | 用途 |
|------|------|
| `.callout`（6 种变体：info/warn/success/danger/purple/cyan） | 见解、警告、要点、设计动机 |
| `.grid-2 > .mini-card` | 并行概念、价值观、未来方向 |
| `.pbox` 编号列表 | 设计原则、规则、指南 |
| `.table-wrap` 内的 `table` | 架构、对比、分类、基准 |
| `figure.paper-fig` | 内嵌图表（支持 Lightbox 放大 + 懒加载） |
| `.summary-grid` | 关键指标仪表板（6–16 项） |
| `.formula-display` / `.formula-inline` | KaTeX 公式（离线回退） |
| `pre` + 语法高亮 | 伪代码和代码片段（悬停复制） |
| `.trace` 有序列表 | 编号流程 |
| `.mindmap` | 概念可视化（中心节点 + 子节点） |
| `.tag`（6 种颜色） | 内联标签 |

---

## 上下文安全设计

Pipeline B 通过文件 I/O 隔离避免上下文爆炸——base64 图片数据**绝不进入 LLM 上下文**：

| 阶段 | 子代理返回内容 | 上下文占用 |
|------|---------------|:--------:|
| B1（并行提取） | JSON 元数据（图表 ID、公式 LaTeX） | <2KB |
| B2（章节分配） | N 个章节分配（含 `strategy`、`position_context`、`previously_defined_concepts`） | <5KB |
| B3（并行撰写） | `{section_id, num, title, file_path}`（结构化 schema） | ~50B × N |
| B3.5（质量评审） | 结构化评审 JSON + 连贯性门控检查 | <1KB |
| B3.5b（连贯性验证） | 轻量级成对编辑 + div 安全验证 | 0（shell 验证） |
| B4（shell 组装） | `assemble_figures.py` + 按顺序拼接 | **0 LLM tokens** |
| B4c（最终 Agent） | 仅读取 `sections_meta.json`——绝不读取 `assembled_body.html` | <2KB |

---

## 示例输出

来自 **"Towards Personalized LLM-Powered Agents"** 的实际阅读笔记——一篇关于个性化 Agent 的综述论文：

> **[📄 在线查看阅读笔记 →](https://htmlpreview.github.io/?https://github.com/LiangRichard13/paper-to-html-note/blob/master/assets/examples/toward_personalized_llm_powered_agents_reading_notes.html)**
> *（由 [htmlpreview.github.io](https://htmlpreview.github.io/) 驱动——直接在浏览器中渲染 HTML）*

<img src="assets/examples/screenshot.png" alt="阅读笔记截图——暗色模式，侧边栏导航，标注卡和内嵌图表" width="720">

**此示例展示**：
- 29 页综述论文，8 张图，中文注释语言
- 6 个内容章节：基础 → 记忆 → 画像 → 检索 → 进化 → 评估
- 架构图和对比图内嵌展示，支持 Lightbox 放大
- 见解标注框（设计动机、跨章节链接、实践要点、关键观察）
- 执行摘要仪表板展示关键指标
- 分类表、对比表和未来方向卡片
- **浏览器内荧光笔批注系统**：选中高亮、点击换色/删除、便签编辑、右侧滑动面板

> 文件完全自包含——无需网络（KaTeX 首次访问时加载，此后离线可用）。

---

## 项目结构

```
paper-to-html-note/
  SKILL.md                   # 技能定义——包含 4 种组织策略的完整工作流规范
  README.md                  # 本文件（中文）
  assets/
    README_en.md             # 英文版 README
    template.html            # 中文模板——所有 UI 标签为简体中文
    template_en.html         # 英文模板——所有 UI 标签为英文（结构上完全一致）
    examples/
      toward_personalized_llm_powered_agents_reading_notes.html
                             # 实际示例：29 页综述论文阅读笔记
  references/
    component-catalog.md     # 所有 HTML 组件及使用指南
    design-system.md         # CSS 变量、主题、JS 模块、增强功能
  scripts/
    extract_figures.py       # 标题驱动图表提取（v4.1）
    assemble_figures.py      # 图表占位符 → base64 组装 + 结构验证
```

---

## 支持的论文类型

针对**计算机科学/软件工程学术论文**优化（arXiv、ACM、IEEE、NeurIPS、ICML 等）。

- 双栏和单栏排版
- 通栏和跨栏图表
- 矢量图形（drawings）和栅格图像
- 纯文字图表（分类树、表格、代码清单）——v4.1 文本块聚类
- 含数学公式的论文（KaTeX 通过 CDN 加载）
- 多图页面
- 无图论文（快速预检优雅跳过）

---

## 局限性与边界情况

| 场景 | 行为 |
|------|------|
| 纯栅格图（扫描版 PDF） | 回退为基于标题的估计 |
| 非英文标题（如 "図 1"） | 无法检测；需要扩展正则表达式 |
| 三栏排版 | 正文段落检测可能不准确 |
| 子图标题（Fig. 1a） | 通过正则表达式支持 |
| 标题在图片上方（旧式排版） | 裁剪将不正确 |
| 跨页图表 | 可能在页面底部被切断 |
| 纯文字图表（无绘图） | v4.1 文本块聚类回退；若边界模糊可能需要手动裁剪 |

---

## 依赖项

- **Python 3.9+**
- **PyMuPDF**（`fitz`）——PDF 解析、文本提取、图表渲染
- **KaTeX**——通过 CDN 加载（离线时回退为等宽字体）
- **pdftotext**（可选）——更快的文本提取

---

## 许可证

MIT License。

## 致谢

- [KaTeX](https://katex.org/)——快速网页数学公式渲染
- [PyMuPDF](https://pymupdf.readthedocs.io/)——PDF 解析和渲染
