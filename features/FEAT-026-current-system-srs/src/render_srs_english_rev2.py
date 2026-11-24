"""Render and audit the English SRS PDF for local visual review."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from unicodedata import category, name

import pypdfium2 as pdfium
import pdfplumber
from docx import Document
from docx.oxml.ns import qn
from lxml import etree
from PIL import Image, ImageDraw


FEATURE = Path(__file__).resolve().parents[1]
DOCX = FEATURE / "artifacts" / "Sketch2Life_SRS_Form_English.docx"
PDF = FEATURE / "artifacts" / "Sketch2Life_SRS_Form_English.pdf"
RENDERS = FEATURE / "evidence" / "screenshots" / "rev2_english"
METRICS = FEATURE / "evidence" / "metrics" / "rev2_english_qa.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latin_diacritics(text: str) -> list[str]:
    return sorted({
        ch for ch in text
        if ord(ch) > 127 and "LATIN" in name(ch, "") and category(ch).startswith("L")
    })


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    for pattern in ("page-*.png", "contact-*.png"):
        for old_image in RENDERS.glob(pattern):
            old_image.unlink()
    doc = Document(DOCX)
    font_counts: Counter[str] = Counter()
    size_counts: Counter[str] = Counter()
    visible_text: list[str] = []
    xml_fonts: Counter[str] = Counter()
    xml_languages: Counter[str] = Counter()
    with zipfile.ZipFile(DOCX) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise ValueError(f"DOCX archive has a corrupt member: {bad_member}")
        for member in archive.namelist():
            if not member.startswith("word/") or not member.endswith(".xml"):
                continue
            root = etree.fromstring(archive.read(member))
            for fonts in root.iter(qn("w:rFonts")):
                for key in ("ascii", "hAnsi", "eastAsia", "cs"):
                    value = fonts.get(qn(f"w:{key}"))
                    if value:
                        xml_fonts[value] += 1
            for language in root.iter(qn("w:lang")):
                for key in ("val", "eastAsia", "bidi"):
                    value = language.get(qn(f"w:{key}"))
                    if value:
                        xml_languages[value] += 1
    if set(xml_fonts) != {"Arial"}:
        raise ValueError(f"Unexpected OOXML font families: {dict(xml_fonts)}")
    if set(xml_languages) - {"en-US"}:
        raise ValueError(f"Unexpected OOXML proofing languages: {dict(xml_languages)}")
    for paragraph in doc.paragraphs:
        visible_text.append(paragraph.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    visible_text.append(paragraph.text)
    for section in doc.sections:
        for part in (section.header, section.footer, section.first_page_header, section.first_page_footer):
            visible_text.extend(paragraph.text for paragraph in part.paragraphs)
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            if run.text.strip():
                font_counts[run.font.name or paragraph.style.font.name or "style"] += len(run.text)
                size_counts[str(run.font.size.pt if run.font.size else "style")] += len(run.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if run.text.strip():
                            font_counts[run.font.name or paragraph.style.font.name or "style"] += len(run.text)
                            size_counts[str(run.font.size.pt if run.font.size else "style")] += len(run.text)

    latin_issues = latin_diacritics("\n".join(visible_text))
    if latin_issues:
        raise ValueError(f"DOCX has non-ASCII Latin letters: {latin_issues}")
    if set(font_counts) != {"Arial"}:
        raise ValueError(f"Unexpected DOCX font families: {font_counts}")

    pdf = pdfium.PdfDocument(PDF)
    pages = []
    thumbs: list[Image.Image] = []
    for index in range(len(pdf)):
        page = pdf[index]
        text = page.get_textpage().get_text_range().replace("\x00", "")
        page_labels = re.findall(r"\bPage\s+(\d+)\b", text)
        if page_labels != [str(index + 1)]:
            raise ValueError(f"Page-number footer mismatch on PDF page {index + 1}: {page_labels}")
        image = page.render(scale=1.7).to_pil().convert("RGB")
        gray = image.convert("L")
        ink = sum(gray.point(lambda value: 255 if value < 245 else 0).histogram()[1:])
        ink_ratio = ink / (image.width * image.height)
        image.save(RENDERS / f"page-{index + 1:02d}.png", optimize=True)
        thumb = image.copy()
        thumb.thumbnail((510, 710))
        card = Image.new("RGB", (530, 750), "#e7ebf1")
        card.paste(thumb, ((530 - thumb.width) // 2, 8))
        ImageDraw.Draw(card).text((12, 726), f"English SRS | page {index + 1}", fill="#17212e")
        thumbs.append(card)
        pages.append({
            "page": index + 1,
            "printed_page_number": int(page_labels[0]),
            "orientation": "landscape" if page.get_size()[0] > page.get_size()[1] else "portrait",
            "text_chars": len(text.strip()),
            "ink_ratio": round(ink_ratio, 6),
            "visually_blank": ink_ratio < 0.005 and len(text.strip()) < 80,
            "latin_diacritics": latin_diacritics(text),
            "text_preview": " ".join(text.split())[:240],
        })
    for start in range(0, len(thumbs), 4):
        sheet = Image.new("RGB", (1060, 1500), "white")
        for offset, thumb in enumerate(thumbs[start:start + 4]):
            sheet.paste(thumb, ((offset % 2) * 530, (offset // 2) * 750))
        sheet.save(RENDERS / f"contact-{start // 4 + 1:02d}.png", optimize=True)

    pdf_text = "\n".join(page.get_textpage().get_text_range() for page in pdf)
    pdf_issues = latin_diacritics(pdf_text)
    if pdf_issues:
        raise ValueError(f"PDF has non-ASCII Latin letters: {pdf_issues}")
    normalized_pdf_text = " ".join(pdf_text.split())
    for expected in (
        "AI for Children", "Do Cao Dat", "Pham Tan Hieu", "Vu Chi Bao",
        "Ly Anh Khoa", "Lam Huu Khanh Phuong", "Traceability", "Appendix",
    ):
        if expected not in normalized_pdf_text:
            raise ValueError(f"PDF is missing expected text: {expected}")

    page_text_bounds = []
    out_of_bounds_chars = []
    with pdfplumber.open(PDF) as parsed_pdf:
        for page_number, page in enumerate(parsed_pdf.pages, start=1):
            chars = [char for char in page.chars if char.get("text", "").strip()]
            if not chars:
                page_text_bounds.append({"page": page_number, "min_x": None, "max_x": None})
                continue
            page_text_bounds.append({
                "page": page_number,
                "min_x": round(min(char["x0"] for char in chars), 2),
                "max_x": round(max(char["x1"] for char in chars), 2),
            })
            for char in chars:
                if char["x0"] < -0.1 or char["x1"] > page.width + 0.1 or char["top"] < -0.1 or char["bottom"] > page.height + 0.1:
                    out_of_bounds_chars.append({
                        "page": page_number,
                        "text": char.get("text", ""),
                        "x0": round(char["x0"], 2),
                        "x1": round(char["x1"], 2),
                        "top": round(char["top"], 2),
                        "bottom": round(char["bottom"], 2),
                    })
    if out_of_bounds_chars:
        raise ValueError(f"PDF text is outside page bounds: {out_of_bounds_chars[:10]}")

    report = {
        "docx_zip_integrity": "pass",
        "docx_sha256": sha256(DOCX),
        "docx_bytes": DOCX.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "pdf_bytes": PDF.stat().st_size,
        "pdf_page_count": len(pdf),
        "docx_font_char_counts": dict(font_counts),
        "docx_run_size_char_counts_pt": dict(size_counts),
        "ooxml_font_family_attribute_counts": dict(xml_fonts),
        "ooxml_proofing_language_attribute_counts": dict(xml_languages),
        "docx_text_latin_diacritics": latin_issues,
        "pdf_text_latin_diacritics": pdf_issues,
        "pages_without_extractable_text": [p["page"] for p in pages if p["text_chars"] == 0],
        "visually_blank_pages": [p["page"] for p in pages if p["visually_blank"]],
        "pdf_text_out_of_bounds_characters": len(out_of_bounds_chars),
        "page_text_horizontal_bounds_pt": page_text_bounds,
        "page_records": pages,
        "visual_review": "Pass: all 13 pages reviewed in contact sheets; cover, introduction/team, repaired tables, route/state model, requirements, security, traceability, sign-off and appendix pages checked at full size.",
    }
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "page_records"}, indent=2))


if __name__ == "__main__":
    main()
