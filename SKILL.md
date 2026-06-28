---
name: pdf-recognize-liamoy
description: Intelligent PDF recognition and Markdown conversion using MinerU. Use when the user needs to extract text, tables, formulas, and images from PDF files and convert them into well-formatted Markdown documents. Triggers include: any mention of 'PDF识别', 'PDF转Markdown', '提取PDF内容', 'PDF文字提取', 'PDF解析', 'PDF提取表格', '.pdf文件处理', 'PDF to Markdown', or when a .pdf file needs content extraction. Supports single file and batch processing with multi-engine fallback (MinerU → pdfplumber → OCR).
---

# PDF Recognize Liamoy — 智能 PDF 识别与 Markdown 转换

## 概述

基于 **MinerU** (opendatalab) 核心引擎的 PDF 智能识别工具，将 PDF 文件高质量转换为 Markdown 文档。支持文本提取、表格识别、公式转换（LaTeX）、图片提取，保留原始排版结构。

**核心脚本**: `scripts/recognize.py`

## 与 tuxiangshibie 的区别

| 特性 | pdf-recognize-liamoy | tuxiangshibie |
|------|---------------------|---------------|
| 核心引擎 | MinerU (magic-pdf) | easyocr + PaddleOCR |
| 输出格式 | **Markdown**（保留排版） | 纯文本 / JSON |
| 表格提取 | ✅ 原生支持 | ❌ |
| 公式识别 | ✅ LaTeX 转换 | ❌ |
| 图片提取 | ✅ 自动分离保存 | ❌ |
| 适用场景 | 结构化 PDF（报告/论文/合同） | 图片/扫描件 OCR |
| 排版保留 | ✅ 标题/段落/列表 | ❌ 仅文字流 |

## 适用场景

- "帮我把这个 PDF 转成 Markdown"
- "提取 PDF 里的文字和表格"
- "解析这份 PDF 报告"
- "把这个 PDF 的内容识别出来"
- "识别 PDF 里的图表和公式"
- "批量处理这些 PDF 文件"
- 任何需要从 PDF 中提取结构化文字、表格、公式的需求

## 快速使用

### 基本用法

```bash
cd "/c/Users/14168/.claude/skills/pdf-recognize-liamoy/scripts"

# 自动识别（推荐：自动选择最佳引擎）
python recognize.py document.pdf

# 指定输出目录
python recognize.py document.pdf -o ./output/

# 启用公式识别
python recognize.py document.pdf --formula

# 安静模式
python recognize.py document.pdf --quiet
```

### 批量处理

```bash
# 处理整个目录的所有 PDF
python recognize.py -d /path/to/pdfs --batch

# 批量 + 指定输出目录
python recognize.py -d /path/to/pdfs --batch -o ./output/
```

### 引擎选择

```bash
# 自动模式（默认：检测 PDF 类型后选择最佳引擎）
python recognize.py document.pdf --engine auto

# 强制使用 MinerU（最佳质量，需要安装 mineru）
python recognize.py document.pdf --engine mineru

# 使用 pdfplumber（快速文本提取，无需 GPU）
python recognize.py document.pdf --engine text

# 使用 OCR（扫描件/图片型 PDF，需要 tuxiangshibie）
python recognize.py document.pdf --engine ocr
```

## 工作流程

### Step 1: 确认文件

确认用户要处理的 PDF 文件路径。支持：
- 单个 PDF 文件
- 目录（批量处理所有 `.pdf` 文件）

### Step 2: 判断 PDF 类型

系统自动检测 PDF 类型：
- **原生 PDF**（native）：文字可选择、有文本层的 PDF
- **扫描件**（scanned）：无文本层的图片型 PDF
- **混合型**（mixed）：部分页面有文本，部分是图片

### Step 3: 选择引擎并执行

```
PDF 文件
  ├─ 自动检测 (--engine auto)
  │   ├─ 原生 PDF → MinerU（最优质量）
  │   │   ├─ MinerU 不可用 → pdfplumber 降级
  │   │   └─ pdfplumber 失败 → OCR 终极降级
  │   ├─ 扫描件 → MinerU（自带 OCR 能力）
  │   │   ├─ MinerU 不可用 → tuxiangshibie OCR
  │   │   └─ OCR 不可用 → pdfplumber（可能为空）
  │   └─ 混合型 → MinerU
  │
  ├─ 强制 MinerU → 直接使用 MinerU CLI
  ├─ 纯文本模式 → pdfplumber 提取
  └─ OCR 模式 → tuxiangshibie OCR
```

### Step 4: 输出结果

输出文件与 PDF 同目录（或指定目录）：
- `{文件名}.md` — 完整的 Markdown 文档
- `{文件名}_images/` — 提取的图片目录（可选）

### Step 5: 后续操作

根据识别出的内容，帮助用户完成后续任务：
- 识别出的是报告/论文 → 可进一步分析、总结、翻译
- 识别出的是表格数据 → 可转换为 Excel/CSV
- 识别出的是合同/公文 → 可提取关键信息
- 识别出的是技术文档 → 可整理为知识库

## 引擎对比

| 引擎 | 文字提取 | 表格 | 公式 | 图片 | 速度 | 内存 | 排版保留 |
|------|---------|------|------|------|------|------|---------|
| MinerU | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | 慢 | ~4GB | ✅ |
| pdfplumber | ★★★★☆ | ★★★☆☆ | ☆☆☆☆☆ | ☆☆☆☆☆ | 快 | ~100MB | ❌ |
| OCR | ★★★☆☆ | ☆☆☆☆☆ | ☆☆☆☆☆ | ☆☆☆☆☆ | 很慢 | ~2GB | ❌ |

## 依赖安装

### 核心依赖（必须）

```bash
pip install pdfplumber pypdf
```

### MinerU 引擎（推荐，最佳质量）

```bash
pip install mineru[full]

# 下载模型文件（首次使用前必须执行）
python -c "from mineru.cli import download_models; download_models.download_models()"
```

> **注意**: MinerU 需要 Python 3.10+，建议使用 GPU（NVIDIA 8GB+ 显存）以加速处理。

### OCR 降级方案（可选）

```bash
# 已安装 tuxiangshibie v3.0 则无需额外安装
# 位于 C:\Users\14168\Desktop\task1\ocr.py
```

## 输出示例

输入: `report.pdf` → 输出: `report.md`

```markdown
# report

> *由 pdf-recognize-liamoy 提取 (MinerU 模式)*

---

## 第一章 引言

这是一段从 PDF 中提取的正文内容。MinerU 自动识别了
标题层级、段落结构和排版信息。

### 1.1 数据表格

| 年份 | 收入 | 支出 | 盈余 |
|------|------|------|------|
| 2024 | 1200 | 800  | 400  |
| 2025 | 1500 | 950  | 550  |

### 1.2 公式

$$
E = mc^2
$$

![图表说明](report_images/image_001.jpg)
```

## CLI 完整参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `pdf` | PDF 文件路径 | — |
| `-d`, `--directory` | 批量处理的目录 | — |
| `-o`, `--output` | 输出目录 | PDF 同目录 |
| `--engine` | 引擎: auto/mineru/ocr/text | auto |
| `--formula` | 启用公式识别 (LaTeX) | false |
| `--no-images` | 不提取图片 | false |
| `--no-tables` | 不提取表格 | false |
| `--quiet` | 安静模式 | false |
| `--batch` | 批量处理模式 | false |

## 注意事项

1. **首次使用 MinerU 需下载模型**：约 2-4GB，存放于用户目录 `.mineru/models/`
2. **GPU 加速**：MinerU 在 GPU 环境下速度快 5-10 倍，CPU 模式下大文件可能较慢
3. **公式识别开销**：`--formula` 会增加约 30% 处理时间和约 1GB 显存
4. **PDF 密码保护**：加密 PDF 需要先解密才能处理
5. **降级策略**：MinerU 不可用时自动降级，确保始终有输出
6. **临时文件清理**：MinerU 生成的临时文件会自动清理
7. **中文支持**：完整支持中英文混合文档、中文表格和公式
