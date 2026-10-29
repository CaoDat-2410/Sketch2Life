from __future__ import annotations

import json
import math
import hashlib
import os
from pathlib import Path
from zipfile import ZipFile

from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image, ImageOps, ImageDraw, ImageFont
from docx import Document
import pdfplumber

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "features/FEAT-058-review2-document-package"
DOC_REVISION = int(os.environ.get("FEAT058_DOC_REVISION", "6"))
OUT = FEATURE / f"artifacts/submission_r2_rev{DOC_REVISION}"
EVIDENCE = FEATURE / f"evidence/render/final/rev{DOC_REVISION}"
METRICS = FEATURE / "evidence/metrics"
BM02_TEMPLATE = Path.home() / 'Downloads' / 'SWP490_R2_BM04_Review2-Document' / 'SWP490_R2_BM02_Self_Review_Report_1.docx'
SOURCE_FILES = {
    "registration_v1_2": Path.home() / 'Downloads' / 'Phieu_FA26SE225_v1.2 (1).docx',
    "review2_guide": Path.home() / 'Downloads' / 'SWP490_R2_Huong-dan-chuan-bi-Review-2_1.pdf',
    "bm01_template": Path.home() / 'Downloads' / 'SWP490_R2_BM04_Review2-Document' / 'SWP490_R2_BM01_Design_Brief_1.docx',
    "bm02_template": BM02_TEMPLATE,
    "bm03_template": Path.home() / 'Downloads' / 'SWP490_R2_BM04_Review2-Document' / 'SWP490_R2_BM03_Record_of_Changes_1.docx',
    "canonical_srs_v3_1": ROOT / "features" / "FEAT-039-collaborative-learning-scope" / "artifacts" / "Collaborative_Learning_SRS_v3.1.md",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    files = sorted(OUT.glob("SWP490_FA26SE225_R2_*.pdf"))
    result = {"revision": DOC_REVISION, "files": [], "bm01": {}, "bm02": {}, "render_scale": 1.65, "contact_sheet_pages": 4}
    horizontal_violations = []
    page_bounds = []
    for pdf_path in files:
        reader = PdfReader(str(pdf_path))
        pdf = pdfium.PdfDocument(str(pdf_path))
        with pdfplumber.open(str(pdf_path)) as layout_pdf:
            for page_no, layout_page in enumerate(layout_pdf.pages, 1):
                boxes = []
                for char in layout_page.chars:
                    if char.get("text", "").strip():
                        boxes.append((char["x0"], char["x1"], "text"))
                for kind in ("images", "rects", "curves"):
                    for obj in getattr(layout_page, kind):
                        boxes.append((obj.get("x0", 0), obj.get("x1", layout_page.width), kind))
                if not boxes:
                    continue
                left = min(box[0] for box in boxes)
                right = max(box[1] for box in boxes)
                left_clearance = left
                right_clearance = layout_page.width - right
                page_bounds.append({
                    "file": pdf_path.name,
                    "page": page_no,
                    "left_clearance_pt": round(left_clearance, 2),
                    "right_clearance_pt": round(right_clearance, 2),
                })
                if left_clearance < 18 or right_clearance < 18:
                    horizontal_violations.append({
                        "file": pdf_path.name,
                        "page": page_no,
                        "left_clearance_pt": round(left_clearance, 2),
                        "right_clearance_pt": round(right_clearance, 2),
                    })
        name = pdf_path.stem
        target = EVIDENCE / name
        target.mkdir(parents=True, exist_ok=True)
        texts = []
        images = []
        for i, page in enumerate(pdf):
            page_text = reader.pages[i].extract_text() or ""
            texts.append(page_text)
            bitmap = page.render(scale=1.65)
            image = bitmap.to_pil().convert("RGB")
            page_file = target / f"page-{i+1:02d}.png"
            image.save(page_file, quality=95)
            images.append((page_file, image))
        sheets = []
        for start in range(0, len(images), 4):
            batch = images[start:start+4]
            tile_w = max(image.width for _, image in batch)
            tile_h = max(image.height for _, image in batch)
            canvas = Image.new("RGB", (tile_w*2+60, tile_h*2+110), "#CBD3DC")
            draw = ImageDraw.Draw(canvas)
            try:
                try:
                    font = ImageFont.truetype("arial.ttf", 26)
                except OSError:
                    font = ImageFont.load_default()
            except OSError:
                font = ImageFont.load_default()
            draw.text((20, 12), f"{name} | pages {start+1}-{start+len(batch)}", fill="#14243D", font=font)
            for j, (_, im) in enumerate(batch):
                col, row = j % 2, j // 2
                x, y = 20 + col*(tile_w+20), 60 + row*(tile_h+25)
                canvas.paste(im, (x, y))
            sheet_path = target / f"contact-{start//4+1:02d}.png"
            canvas.save(sheet_path, quality=92)
            sheets.append(str(sheet_path))
        entry = {
            "name": name,
            "path": str(pdf_path),
            "pages": len(reader.pages),
            "chars_per_page": [len(t) for t in texts],
            "first_page_text": texts[0][:900] if texts else "",
            "last_page_text": texts[-1][:1200] if texts else "",
            "contact_sheets": sheets,
            "page_images": [str(path) for path, _ in images],
        }
        result["files"].append(entry)
        if name.endswith("DesignBrief"):
            appendix_pages = [i+1 for i, t in enumerate(texts) if "Appendix A" in t or "Defense 1.1 Targets" in t]
            brief_docx = Document(str(OUT / (name + ".docx")))
            brief_section = brief_docx.sections[0]
            font_sizes = []
            for paragraph in brief_docx.paragraphs:
                for run in paragraph.runs:
                    if run.text.strip() and run.font.size and not paragraph.text.startswith("SWP490  |"):
                        font_sizes.append(run.font.size.pt)
            for table in brief_docx.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                if run.text.strip() and run.font.size:
                                    font_sizes.append(run.font.size.pt)
            result["bm01"] = {
                "pages": len(texts),
                "appendix_first_page": appendix_pages[0] if appendix_pages else None,
                "main_body_pages": (appendix_pages[0]-1) if appendix_pages else None,
                "page_geometry_in": [round(reader.pages[0].mediabox.width/72, 2), round(reader.pages[0].mediabox.height/72, 2)],
                "margins_cm": [round(x/360000, 2) for x in [brief_section.top_margin, brief_section.bottom_margin, brief_section.left_margin, brief_section.right_margin]],
                "min_explicit_body_font_pt": min(font_sizes, default=None),
                "all_section_headers_present": all(any(marker in t for t in texts) for marker in ["0. Header", "1. Scope", "2. System at a Glance", "3. Key Design Decisions", "4. Top Risks", "5. Known Gaps", "6. Mandatory Features", "7. Non-Functional Requirements", "8. Ownership Map"]),
                "test_target_61": any("61" in t for t in texts),
                "test_target_31": any("31" in t for t in texts),
                "known_gap_ids": [f"G{i}" for i in range(1, 7)],
            }
        if name.endswith("SelfReview"):
            joined = "\n".join(texts)
            result["bm02"] = {
                "pages": len(texts),
                "finding_ids_present": all(f"SR-{i:02d}" in joined for i in range(1, 11)),
                "severity_counts_present": all(f"{n} {sev}" in joined for n, sev in [(7,"High"),(2,"Medium"),(1,"Low")]),
                "tag_absence_disclosed": "No review-2 tag exists" in joined,
                "prompt_first_line_present": "You are reviewing the SRS and SDD" in joined,
                "team_response_present": "Proposed response" in joined,
            }
    out_json = EVIDENCE / f"revision{DOC_REVISION}_render_inventory.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    outputs = {}
    docx_structure = {}
    for pdf_path in files:
        docx_path = OUT / (pdf_path.stem + ".docx")
        with ZipFile(docx_path) as package:
            zip_error = package.testzip()
        parsed_docx = Document(str(docx_path))
        docx_structure[pdf_path.stem] = {
            "zip_integrity": zip_error is None,
            "parsed_by_python_docx": True,
            "paragraph_count": len(parsed_docx.paragraphs),
            "table_count": len(parsed_docx.tables),
        }
        outputs[pdf_path.stem] = {
            "docx": {"path": str(docx_path), "bytes": docx_path.stat().st_size, "sha256": sha256(docx_path)},
            "pdf": {"path": str(pdf_path), "bytes": pdf_path.stat().st_size, "sha256": sha256(pdf_path)},
        }
    sources = {
        key: {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for key, path in SOURCE_FILES.items() if path.exists()
    }
    brief_docx = Document(str(OUT / "SWP490_FA26SE225_R2_DesignBrief.docx"))
    margins_cm = [round(x/360000, 2) for x in [brief_docx.sections[0].top_margin, brief_docx.sections[0].bottom_margin, brief_docx.sections[0].left_margin, brief_docx.sections[0].right_margin]]
    official_prompt = Document(str(BM02_TEMPLATE)).tables[1].cell(0, 0).text
    final_prompt = Document(str(OUT / "SWP490_FA26SE225_R2_SelfReview.docx")).tables[1].cell(0, 0).text
    report_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(OUT / "SWP490_FA26SE225_R2_Report1-5_Tracking.pdf")).pages)
    import re
    uc_ids = set(re.findall(r"UC-\d{3}", report_text))
    fr_ids = set(re.findall(r"FR\d{3}", report_text))
    result["outputs"] = outputs
    result["sources"] = sources
    result["docx_structure"] = docx_structure
    result["horizontal_layout"] = {
        "minimum_required_edge_clearance_pt": 18,
        "worst_left_clearance_pt": round(min((x["left_clearance_pt"] for x in page_bounds), default=0), 2),
        "worst_right_clearance_pt": round(min((x["right_clearance_pt"] for x in page_bounds), default=0), 2),
        "violations": horizontal_violations,
    }
    result["checks"] = {
        "exactly_four_dossiers_with_docx_and_pdf": len(outputs) == 4 and all(Path(x["docx"]["path"]).exists() and Path(x["pdf"]["path"]).exists() for x in outputs.values()),
        "all_docx_packages_valid_and_parseable": len(docx_structure) == 4 and all(x["zip_integrity"] and x["parsed_by_python_docx"] and x["table_count"] > 0 for x in docx_structure.values()),
        "report_has_38_use_cases": len(uc_ids) == 38 and "UC-001" in uc_ids and "UC-038" in uc_ids,
        "report_has_66_functional_requirements": len(fr_ids) == 66 and "FR001" in fr_ids and "FR066" in fr_ids,
        "bm01_main_body_at_most_four_pages": bool(result["bm01"].get("main_body_pages") is not None and result["bm01"]["main_body_pages"] <= 4),
        "bm01_a4_and_2cm_margins": result["bm01"].get("page_geometry_in") == [8.27, 11.69] and margins_cm == [2.0, 2.0, 2.0, 2.0],
        "bm01_content_font_at_least_11pt": result["bm01"].get("min_explicit_body_font_pt") == 11.0,
        "bm02_prompt_matches_official_template": official_prompt == final_prompt,
        "bm02_tagged_run_limitation_disclosed": result["bm02"].get("tag_absence_disclosed") is True,
        "all_rendered_pages_have_page_images": all(len(x["page_images"]) == x["pages"] for x in result["files"]),
        "no_horizontal_page_overflow": not horizontal_violations,
        "application_tests_run_for_document_task": False,
        "review_2_tag_created": False,
        "commit_or_push_performed": False,
    }
    result["baseline"] = {
        "branch": "dev",
        "commit": "0a7ce768c153f2104cff930569c3eda6e484532c",
        "working_tree": "dirty; FEAT-059 cleanup and local user changes are uncommitted",
        "review_2_tag": "TBD; does not satisfy the guide's tagged-baseline BM02 run gate",
        "modal": "selected; deployment configuration TBD",
    }
    result["visual_review"] = {
        "status": "all final PDF pages rendered to page PNGs and visually inspected in contact sheets",
        "render_inventory": str(out_json),
        "render_directory": str(EVIDENCE),
    }
    final_json = METRICS / f"final_package_qa_20261023_rev{DOC_REVISION}.json"
    METRICS.mkdir(parents=True, exist_ok=True)
    final_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pdfs": [{"name":x["name"],"pages":x["pages"],"contact_sheets":len(x["contact_sheets"])} for x in result["files"]], "bm01":result["bm01"], "bm02":result["bm02"], "inventory":str(out_json)},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
