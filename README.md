# pdf-recognize-liamoy

基于 [MinerU](https://github.com/opendatalab/MinerU) 的智能 PDF 识别工具，将 PDF 文件高质量转换为 Markdown 文档。

## 功能

- ✅ **文字提取** — 保留标题、段落、列表等排版结构
- ✅ **表格识别** — 自动转换为 Markdown 表格
- ✅ **公式转换** — 识别数学公式并输出 LaTeX
- ✅ **图片提取** — 自动分离并保存 PDF 中的图片
- ✅ **三级降级** — MinerU → pdfplumber → OCR，确保始终有输出
- ✅ **批量处理** — 一键处理整个目录的所有 PDF
- ✅ **自动检测** — 智能判断 PDF 类型（原生/扫描/混合）

## 安装

```bash
git clone https://github.com/hhhky/pdf-recognize-liamoy.git
cd pdf-recognize-liamoy
pip install -r scripts/requirements.txt
```

### 安装 MinerU（推荐）

```bash
pip install mineru[full]
mineru download-models
```

## 使用

```bash
cd scripts

# 自动识别（推荐）
python recognize.py document.pdf

# 强制使用 MinerU
python recognize.py document.pdf --engine mineru

# 启用公式识别
python recognize.py document.pdf --formula

# 批量处理
python recognize.py -d ./pdfs --batch

# 指定输出目录
python recognize.py document.pdf -o ./output/
```

## 引擎对比

| 引擎 | 文字 | 表格 | 公式 | 图片 | 速度 | 内存 |
|------|------|------|------|------|------|------|
| MinerU | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | 慢 | ~4GB |
| pdfplumber | ★★★★☆ | ★★★☆☆ | ☆☆☆☆☆ | ☆☆☆☆☆ | 快 | ~100MB |
| OCR | ★★★☆☆ | ☆☆☆☆☆ | ☆☆☆☆☆ | ☆☆☆☆☆ | 很慢 | ~2GB |

## 输出

```
input.pdf
├── input.md          # Markdown 文档
└── input_images/     # 提取的图片
```

## 与 tuxiangshibie 的区别

| 特性 | pdf-recognize-liamoy | tuxiangshibie |
|------|---------------------|---------------|
| 核心引擎 | MinerU | easyocr + PaddleOCR |
| 输出格式 | Markdown（保留排版） | 纯文本 / JSON |
| 表格提取 | ✅ 原生支持 | ❌ |
| 公式识别 | ✅ LaTeX | ❌ |
| 排版保留 | ✅ | ❌ |

## 许可

MIT License
