#!/usr/bin/env python3
"""
pdf-recognize-liamoy — 基于 MinerU 的智能 PDF 识别工具
将 PDF 文件高质量转换为 Markdown 文档。
核心引擎: MinerU (opendatalab)
降级方案: pdfplumber → tuxiangshibie OCR
版本: v1.0.0
仓库: https://github.com/hhhky/pdf-recognize-liamoy
"""

import os, sys, re, argparse, subprocess, shutil
from pathlib import Path
from typing import Optional, List, Tuple

# Windows: 强制 UTF-8 输出，避免 GBK 编码错误
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

VERSION = "1.0.0"
TUXIANGSHIBIE_OCR = Path("C:/Users/14168/Desktop/task1/ocr.py")


class PDFRecognizer:
    """PDF 智能识别引擎 — MinerU → pdfplumber → OCR 三级降级"""

    def __init__(self, pdf_path, output_dir=None, engine="auto",
                 extract_images=True, extract_tables=True,
                 formula=False, quiet=False):
        self.pdf_path = Path(pdf_path).resolve()
        self.output_dir = Path(output_dir).resolve() if output_dir else self.pdf_path.parent
        self.engine = engine
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        self.formula = formula
        self.quiet = quiet
        self._engine_used = "unknown"
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF不存在: {self.pdf_path}")
        if self.pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"不是PDF文件: {self.pdf_path}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _log(self, msg, level="info"):
        if self.quiet and level == "info":
            return
        p = {"info":"📄","success":"✅","error":"❌","warn":"⚠️ "}.get(level,"  ")
        print(f"{p} [liamoy] {msg}")

    def _check_mineru(self):
        try:
            r = subprocess.run(["mineru","--version"], capture_output=True, text=True, timeout=10)
            return r.returncode == 0
        except:
            return False

    def _check_ocr(self):
        return TUXIANGSHIBIE_OCR.exists()

    def _detect_type(self):
        """返回: native / mixed / scanned / unknown"""
        try:
            from pypdf import PdfReader
            r = PdfReader(str(self.pdf_path))
            n = min(5, len(r.pages))
            chars = sum(len((p.extract_text() or "").strip()) for p in r.pages[:n])
            avg = chars / n if n > 0 else 0
            return "native" if avg > 100 else ("mixed" if avg > 10 else "scanned")
        except:
            return "unknown"

    # ── MinerU 引擎 ───────────────────────────────────

    def _run_mineru(self):
        if not self._check_mineru():
            raise RuntimeError("MinerU未安装: pip install mineru[full]")
        name = self.pdf_path.stem
        tmp = self.output_dir / f".liamoy_{name}"
        cmd = ["mineru","-p",str(self.pdf_path),"-o",str(tmp),"-m","auto" if self.formula else "txt"]
        self._log(f"mineru -p {self.pdf_path.name}")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, encoding="utf-8")
            if r.returncode != 0:
                shutil.rmtree(tmp, ignore_errors=True)
                raise RuntimeError(f"MinerU错误: {(r.stderr or '')[:500]}")
            md = self._find_md(tmp, name)
            if md is None:
                shutil.rmtree(tmp, ignore_errors=True)
                raise RuntimeError("MinerU未生成输出")
            if self.extract_images:
                self._copy_imgs(tmp, name)
            shutil.rmtree(tmp, ignore_errors=True)
            return md
        except subprocess.TimeoutExpired:
            shutil.rmtree(tmp, ignore_errors=True)
            raise RuntimeError("MinerU超时(>10分钟)")

    def _find_md(self, tmp, name):
        for mode in ("auto","txt",""):
            c = tmp / name / mode / f"{name}.md"
            if c.exists():
                return c.read_text(encoding="utf-8")
        mds = [f for f in tmp.rglob("*.md") if "content_list" not in f.name]
        return max(mds, key=lambda f: f.stat().st_size).read_text(encoding="utf-8") if mds else None

    def _copy_imgs(self, tmp, name):
        target = self.output_dir / f"{name}_images"
        for root, dirs, _ in os.walk(tmp):
            if "images" in dirs:
                src = Path(root) / "images"
                if src.exists() and any(src.iterdir()):
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(src, target)
                    self._log(f"图片: {target.name}/")
                    return

    # ── pdfplumber 引擎 ───────────────────────────────

    def _run_pdfplumber(self):
        import pdfplumber
        lines = [f"# {self.pdf_path.stem}\n",
                 f"> *pdf-recognize-liamoy (pdfplumber)*\n",
                 f"> `{self.pdf_path.name}`\n\n---\n"]
        with pdfplumber.open(str(self.pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                lines.append(f"\n## 第{i}页\n")
                t = page.extract_text()
                if t:
                    lines.append(re.sub(r"(?<!\n)\n(?!\n|\#)", " ", t))
                    lines.append("")
                if self.extract_tables:
                    for j, tbl in enumerate(page.extract_tables() or []):
                        if tbl and any(any(c for c in r) for r in tbl):
                            lines.append(f"\n### 表格{i}.{j+1}\n")
                            lines.append(self._tbl_md(tbl))
                            lines.append("")
        return "\n".join(lines)

    def _tbl_md(self, tbl):
        clean = [[str(c or "").strip() for c in r] for r in tbl if any(r)]
        if not clean:
            return ""
        h = clean[0]
        out = ["| " + " | ".join(h) + " |",
               "| " + " | ".join(["---"]*len(h)) + " |"]
        for r in clean[1:]:
            out.append("| " + " | ".join((r + [""]*len(h))[:len(h)]) + " |")
        return "\n".join(out)

    # ── OCR (tuxiangshibie) 引擎 ─────────────────────

    def _run_ocr(self):
        if not self._check_ocr():
            raise RuntimeError(f"OCR不可用: {TUXIANGSHIBIE_OCR}")
        self._log(f"OCR: {self.pdf_path.name}")
        try:
            r = subprocess.run(
                ["python", str(TUXIANGSHIBIE_OCR), "--pdf", str(self.pdf_path), "--quiet"],
                capture_output=True, text=True, timeout=600,
                cwd=str(TUXIANGSHIBIE_OCR.parent), encoding="utf-8")
            if r.returncode != 0:
                raise RuntimeError(f"OCR错误: {(r.stderr or '')[:300]}")
            txt = r.stdout.strip()
            if not txt:
                raise RuntimeError("OCR空结果")
            return "\n".join([
                f"# {self.pdf_path.stem}\n",
                f"> *pdf-recognize-liamoy (OCR — tuxiangshibie v3.0)*\n",
                f"> `{self.pdf_path.name}`\n\n---\n\n", txt])
        except subprocess.TimeoutExpired:
            raise RuntimeError("OCR超时(>10分钟)")

    # ── 主识别流程 ────────────────────────────────────

    def recognize(self):
        """主入口。返回输出 Path。"""
        name = self.pdf_path.stem
        out = self.output_dir / f"{name}.md"
        strategies = {"auto": self._auto_s, "mineru": self._mineru_s,
                      "text": self._text_s, "ocr": self._ocr_s}
        if self.engine not in strategies:
            raise ValueError(f"未知引擎: {self.engine} (可选: auto/mineru/text/ocr)")
        content = strategies[self.engine]()
        if content is None:
            raise RuntimeError("所有引擎均失败，无法提取内容")
        content = self._clean(content, name)
        out.write_text(content, encoding="utf-8")
        self._log(f"输出: {out}", "success")
        self._log(f"引擎: {self._engine_used}", "info")
        return out

    def _auto_s(self):
        t = self._detect_type()
        self._log(f"类型: {t}")
        if self._check_mineru():
            try:
                self._engine_used = "mineru"
                return self._run_mineru()
            except RuntimeError as e:
                self._log(f"MinerU失败: {e}", "warn")
        if t in ("scanned","unknown") and self._check_ocr():
            try:
                self._engine_used = "ocr"
                return self._run_ocr()
            except RuntimeError as e:
                self._log(f"OCR失败: {e}", "warn")
        self._engine_used = "pdfplumber"
        return self._run_pdfplumber()

    def _mineru_s(self):
        self._engine_used = "mineru"
        return self._run_mineru()

    def _text_s(self):
        self._engine_used = "pdfplumber"
        return self._run_pdfplumber()

    def _ocr_s(self):
        self._engine_used = "ocr"
        return self._run_ocr()

    def _clean(self, c, name):
        c = re.sub(r'\n{4,}', '\n\n\n', c)
        c = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', c)
        c = re.sub(r'!\[([^\]]*)\]\(images/([^)]+)\)', rf'![\1]({name}_images/\2)', c)
        return c.strip() + "\n"


# ─── 批量处理 ──────────────────────────────────────────

def process_batch(directory, output_dir, engine, extract_images,
                  extract_tables, formula, quiet):
    files = sorted(Path(directory).rglob("*.pdf"))
    if not files:
        print(f"在 {directory} 中未找到 PDF 文件")
        return 0, 0
    print(f"\n{'='*60}")
    print(f"  pdf-recognize-liamoy v{VERSION} — 批量处理")
    print(f"  目录: {directory}  |  引擎: {engine}  |  {len(files)} 个 PDF")
    print(f"{'='*60}\n")
    ok = 0
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f.name} ... ", end="", flush=True)
        try:
            r = PDFRecognizer(str(f), output_dir, engine, extract_images,
                              extract_tables, formula, True)
            r.recognize()
            print(f"✅ ({r._engine_used})")
            ok += 1
        except Exception as e:
            print(f"❌ {str(e)[:100]}")
    return ok, len(files)


# ─── CLI 入口 ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="pdf-recognize-liamoy — 基于 MinerU 的智能 PDF 识别与 Markdown 转换",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
引擎说明:
  auto   - 自动检测 → MinerU → pdfplumber → OCR 逐级降级（推荐）
  mineru - 强制 MinerU（最佳质量，需: pip install mineru[full]）
  text   - pdfplumber 轻量提取（快速，无需 GPU）
  ocr    - tuxiangshibie OCR（扫描件专用）

示例:
  python recognize.py report.pdf                 # 自动识别
  python recognize.py report.pdf --engine mineru # 强制 MinerU
  python recognize.py report.pdf --formula       # 启用公式识别
  python recognize.py -d ./pdfs --batch          # 批量处理
  python recognize.py report.pdf -o ./output/    # 指定输出目录

GitHub: https://github.com/hhhky/pdf-recognize-liamoy
        """)
    parser.add_argument("pdf", nargs="?", help="PDF 文件路径")
    parser.add_argument("-d","--directory", help="批量处理目录")
    parser.add_argument("-o","--output", help="输出目录 (默认: PDF同目录)")
    parser.add_argument("--engine", choices=["auto","mineru","text","ocr"], default="auto")
    parser.add_argument("--formula", action="store_true", help="启用公式识别(LaTeX)")
    parser.add_argument("--no-images", action="store_true", help="不提取图片")
    parser.add_argument("--no-tables", action="store_true", help="不提取表格")
    parser.add_argument("-q","--quiet", action="store_true", help="安静模式")
    parser.add_argument("--batch", action="store_true", help="批量处理模式")
    parser.add_argument("-V","--version", action="version", version=f"pdf-recognize-liamoy v{VERSION}")
    args = parser.parse_args()

    if args.batch or args.directory:
        ok, tot = process_batch(args.directory or ".", args.output, args.engine,
                                not args.no_images, not args.no_tables,
                                args.formula, args.quiet)
        if tot:
            print(f"\n{'='*60}")
            print(f"  完成: {ok}/{tot} 成功" + (f"  |  失败: {tot-ok}" if ok < tot else ""))
            print(f"{'='*60}\n")
        sys.exit(0 if ok == tot else 1)

    if not args.pdf:
        parser.print_help()
        sys.exit(1)

    try:
        r = PDFRecognizer(args.pdf, args.output, args.engine,
                          not args.no_images, not args.no_tables,
                          args.formula, args.quiet)
        if not args.quiet:
            print(f"\n{'─'*50}\n  pdf-recognize-liamoy v{VERSION}")
            print(f"  📄 {r.pdf_path.name}\n  🏷️  引擎: {args.engine}\n{'─'*50}\n")
        result = r.recognize()
        if not args.quiet:
            print(f"\n{'─'*50}\n  ✅ 识别完成\n  📄 {result}")
            print(f"  🏷️  实际引擎: {r._engine_used}\n{'─'*50}\n")
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ 识别失败: {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
        sys.exit(130)


if __name__ == "__main__":
    main()
