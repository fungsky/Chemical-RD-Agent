"""文档解析：PDF / Word / TXT / URL 文本提取 + 分块。"""

import logging
from io import BytesIO
from typing import Optional

import requests as _requests
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter

from chem_agent.config import settings

logger = logging.getLogger(__name__)


class DocumentParseError(Exception):
    """文档解析异常。"""


# ============ 文本提取 ============


def parse_pdf(file_bytes: bytes) -> str:
    """解析 PDF，逐页提取文本。"""
    import fitz  # pymupdf

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages = []
        for page in doc:
            text = page.get_text("text")
            if text.strip():
                pages.append(text)
        doc.close()
        if not pages:
            raise DocumentParseError("PDF 文件中未提取到文本内容")
        return "\n\n".join(pages)
    except DocumentParseError:
        raise
    except Exception as e:
        raise DocumentParseError(f"PDF 解析失败: {e}") from e


def parse_docx(file_bytes: bytes) -> str:
    """解析 Word (.docx)，提取段落和表格内容。"""
    from docx import Document

    try:
        doc = Document(BytesIO(file_bytes))
        parts: list[str] = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                parts.append(text)

        for table in doc.tables:
            rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                rows.append(" | ".join(cells))
            if rows:
                parts.append("\n".join(rows))

        if not parts:
            raise DocumentParseError("Word 文件中未提取到文本内容")
        return "\n\n".join(parts)
    except DocumentParseError:
        raise
    except Exception as e:
        raise DocumentParseError(f"Word 解析失败: {e}") from e


def parse_txt(file_bytes: bytes) -> str:
    """解析纯文本文件，自动检测编码。"""
    for encoding in ("utf-8", "gbk", "gb2312", "latin-1"):
        try:
            text = file_bytes.decode(encoding)
            if text.strip():
                return text
        except (UnicodeDecodeError, ValueError):
            continue
    raise DocumentParseError("无法识别文本编码")


def parse_excel(file_bytes: bytes) -> str:
    """解析 Excel (.xlsx/.xls)，提取所有工作表中的表格内容。"""
    import openpyxl

    try:
        wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
        parts: list[str] = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = []
            for row in ws.iter_rows(values_only=True):
                cells = [str(c) if c is not None else "" for c in row]
                if any(cells):
                    rows.append(" | ".join(cells))
            if rows:
                parts.append(f"[{sheet_name}]\n" + "\n".join(rows))
        wb.close()
        if not parts:
            raise DocumentParseError("Excel 文件中未提取到内容")
        return "\n\n".join(parts)
    except DocumentParseError:
        raise
    except Exception as e:
        raise DocumentParseError(f"Excel 解析失败: {e}") from e


def scrape_url(url: str, timeout: int = 30) -> tuple[str, str]:
    """抓取网页，返回 (正文, 标题)。"""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        resp = _requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"

        soup = BeautifulSoup(resp.text, "lxml")

        title = soup.title.string.strip() if soup.title and soup.title.string else url

        # 移除脚本、样式、导航等非正文元素
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # 清理多余空行
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = "\n".join(lines)

        if not content:
            raise DocumentParseError("网页中未提取到正文内容")
        return content, title
    except DocumentParseError:
        raise
    except _requests.RequestException as e:
        raise DocumentParseError(f"网页抓取失败: {e}") from e
    except Exception as e:
        raise DocumentParseError(f"网页解析失败: {e}") from e


# ============ 文本分块 ============


def chunk_text(
    text: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[str]:
    """将文本按语义分块。"""
    size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", "。", "；", ".", ";", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_text(text)
    return [c for c in chunks if c.strip()]
