#!/usr/bin/env python3
"""Compile approved physical pages and optionally build an InDesign proof via COM."""

from __future__ import annotations

import argparse
import hashlib
import json
import locale
import os
import re
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import NamedTuple


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PAGE_PATTERN = re.compile(r"^(\d{2})-.+\.png$", re.IGNORECASE)
COM_PROGID = "InDesign.Application.2025"


class PageAsset(NamedTuple):
    index: int
    path: Path
    width_px: int
    height_px: int
    sha256: str


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError(f"not a supported PNG: {path}")
    return struct.unpack(">II", header[16:24])


def discover_pages(page_dir: Path) -> list[PageAsset]:
    if not page_dir.is_dir():
        raise FileNotFoundError(f"page directory not found: {page_dir}")
    numbered: list[tuple[int, Path]] = []
    for path in page_dir.iterdir():
        if not path.is_file():
            continue
        match = PAGE_PATTERN.match(path.name)
        if match:
            numbered.append((int(match.group(1)), path.resolve()))
    numbered.sort(key=lambda item: item[0])
    if not numbered:
        raise ValueError(f"no numbered PNG pages found: {page_dir}")
    expected = list(range(len(numbered)))
    actual = [index for index, _ in numbered]
    if actual != expected:
        raise ValueError(f"page prefixes must be contiguous from 00; found: {actual}")

    pages: list[PageAsset] = []
    dimensions: set[tuple[int, int]] = set()
    for index, path in numbered:
        width, height = png_dimensions(path)
        dimensions.add((width, height))
        pages.append(
            PageAsset(
                index=index,
                path=path,
                width_px=width,
                height_px=height,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    if len(dimensions) != 1:
        raise ValueError(f"all physical pages must share one pixel size; found: {sorted(dimensions)}")
    return pages


def _jsx_string(value: str | Path) -> str:
    text = str(value).replace("\\", "/")
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_jsx(
    *,
    pages: list[PageAsset],
    project_id: str,
    document_title: str,
    trim_width_mm: float,
    trim_height_mm: float,
    bleed_mm: float,
    indd_path: Path,
    pdf_path: Path,
) -> str:
    page_paths = ",\n        ".join(_jsx_string(page.path) for page in pages)
    return f'''#target indesign
(function () {{
    var previousInteraction = app.scriptPreferences.userInteractionLevel;
    var doc = null;
    try {{
        app.scriptPreferences.userInteractionLevel = UserInteractionLevels.NEVER_INTERACT;
        var pageFiles = [
        {page_paths}
        ];
        var inddFile = File({_jsx_string(indd_path.resolve())});
        var pdfFile = File({_jsx_string(pdf_path.resolve())});
        if (inddFile.exists) inddFile.remove();
        if (pdfFile.exists) pdfFile.remove();

        doc = app.documents.add();
        doc.documentPreferences.facingPages = true;
        doc.documentPreferences.pageWidth = "{trim_width_mm:g}mm";
        doc.documentPreferences.pageHeight = "{trim_height_mm:g}mm";
        doc.documentPreferences.documentBleedTopOffset = "{bleed_mm:g}mm";
        doc.documentPreferences.documentBleedBottomOffset = "{bleed_mm:g}mm";
        doc.documentPreferences.documentBleedInsideOrLeftOffset = "{bleed_mm:g}mm";
        doc.documentPreferences.documentBleedOutsideOrRightOffset = "{bleed_mm:g}mm";
        doc.metadataPreferences.documentTitle = {_jsx_string(document_title)};
        doc.insertLabel("book-production-project-id", {_jsx_string(project_id)});
        doc.insertLabel("book-production-mode", "approved-page-proof");

        while (doc.pages.length < pageFiles.length) {{
            doc.pages.add(LocationOptions.AT_END);
        }}
        while (doc.pages.length > pageFiles.length) {{
            doc.pages.lastItem().remove();
        }}

        var proofLayer = doc.layers.item(0);
        proofLayer.name = "Approved Page Proofs";
        for (var i = 0; i < pageFiles.length; i++) {{
            var source = File(pageFiles[i]);
            if (!source.exists) throw new Error("Missing page asset: " + source.fsName);
            var page = doc.pages.item(i);
            var frame = page.rectangles.add({{
                geometricBounds: [0, 0, {trim_height_mm:g}, {trim_width_mm:g}],
                strokeWeight: 0
            }});
            frame.itemLayer = proofLayer;
            frame.label = "approved-page:" + source.name;
            frame.place(source);
            frame.fit(FitOptions.FILL_PROPORTIONALLY);
            frame.fit(FitOptions.CENTER_CONTENT);
        }}

        doc.save(inddFile);
        app.pdfExportPreferences.exportReaderSpreads = false;
        app.pdfExportPreferences.pageRange = PageRange.ALL_PAGES;
        app.pdfExportPreferences.useDocumentBleedWithPDF = {str(bleed_mm > 0).lower()};
        app.pdfExportPreferences.viewPDF = false;
        doc.exportFile(ExportFormat.PDF_TYPE, pdfFile, false);
        var result = '{{"status":"built","application":"' + app.name +
            '","version":"' + app.version + '","pages":' + doc.pages.length +
            ',"links":' + doc.links.length + '}}';
        doc.close(SaveOptions.NO);
        doc = null;
        return result;
    }} catch (error) {{
        if (doc !== null) {{
            try {{ doc.close(SaveOptions.NO); }} catch (closeError) {{}}
        }}
        throw error;
    }} finally {{
        app.scriptPreferences.userInteractionLevel = previousInteraction;
    }}
}})();
'''


def _vbs_string(value: str | Path) -> str:
    return str(value).replace('"', '""')


def run_jsx_via_com(jsx_path: Path, timeout_seconds: int = 180) -> dict[str, object]:
    if os.name != "nt":
        raise OSError("InDesign COM execution requires Windows")
    with tempfile.TemporaryDirectory(prefix="book-indesign-") as tmp:
        temp_root = Path(tmp)
        output_path = temp_root / "result.json"
        vbs_path = temp_root / "run-indesign.vbs"
        vbs = f'''Const idJavascript = 1246973031
On Error Resume Next
Set app = CreateObject("{COM_PROGID}")
If Err.Number <> 0 Then
  WScript.Echo "COM create failed: " & Err.Description
  WScript.Quit 2
End If
Err.Clear
result = app.DoScript("{_vbs_string(jsx_path.resolve())}", idJavascript)
If Err.Number <> 0 Then
  WScript.Echo "JSX failed: " & Err.Description
  WScript.Quit 3
End If
Call WriteUtf8("{_vbs_string(output_path)}", CStr(result))

Sub WriteUtf8(path, text)
  Dim stream
  Set stream = CreateObject("ADODB.Stream")
  stream.Type = 2
  stream.Charset = "utf-8"
  stream.Open
  stream.WriteText text
  stream.SaveToFile path, 2
  stream.Close
End Sub
'''
        vbs_path.write_text(vbs, encoding="utf-8")
        completed = subprocess.run(
            ["cscript", "//nologo", str(vbs_path)],
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        if not output_path.is_file():
            detail = (completed.stderr or completed.stdout).decode(
                locale.getpreferredencoding(False), errors="replace"
            ).strip()
            raise RuntimeError(f"InDesign COM bridge produced no result (exit {completed.returncode}): {detail}")
        result = json.loads(output_path.read_text(encoding="utf-8-sig"))
        if completed.returncode or "error" in result:
            detail = (completed.stderr or completed.stdout).decode(
                locale.getpreferredencoding(False), errors="replace"
            ).strip()
            raise RuntimeError(str(result.get("error") or detail).strip())
        return result


def build_report(
    *,
    project_id: str,
    mode: str,
    pages: list[PageAsset],
    trim_width_mm: float,
    trim_height_mm: float,
    output_dir: Path,
    execution: dict[str, object] | None,
) -> dict[str, object]:
    effective_ppi = min(
        min(page.width_px / (trim_width_mm / 25.4), page.height_px / (trim_height_mm / 25.4))
        for page in pages
    )
    blockers: list[str] = []
    if effective_ppi < 300:
        blockers.append("minimum_effective_ppi_below_300")
    if mode == "proof":
        blockers.append("proof_pages_are_flattened_images")
    return {
        "schema_version": "1.0",
        "project_id": project_id,
        "mode": mode,
        "status": "built" if execution else "compiled",
        "page_count": len(pages),
        "trim_mm": [trim_width_mm, trim_height_mm],
        "quality": {
            "minimum_effective_ppi": round(effective_ppi, 2),
            "print_ready": mode == "print" and not blockers,
            "blockers": blockers,
        },
        "source_pages": [
            {
                "index": page.index,
                "path": str(page.path),
                "width_px": page.width_px,
                "height_px": page.height_px,
                "sha256": page.sha256,
            }
            for page in pages
        ],
        "outputs": {
            "jsx": str(output_dir / "build-book.jsx"),
            "indd": str(output_dir / "book-proof.indd"),
            "pdf": str(output_dir / "book-proof.pdf"),
            "report": str(output_dir / "indesign-build-report.json"),
        },
        "execution": execution,
    }


def compile_build(
    *,
    project_root: Path,
    page_dir: Path,
    output_dir: Path,
    project_id: str,
    document_title: str,
    mode: str,
    trim_width_mm: float,
    trim_height_mm: float,
    bleed_mm: float,
    execute: bool,
) -> dict[str, object]:
    project_root = project_root.resolve()
    page_dir = page_dir if page_dir.is_absolute() else project_root / page_dir
    output_dir = output_dir if output_dir.is_absolute() else project_root / output_dir
    pages = discover_pages(page_dir.resolve())
    output_dir.mkdir(parents=True, exist_ok=True)
    indd_path = output_dir / "book-proof.indd"
    pdf_path = output_dir / "book-proof.pdf"
    jsx_path = output_dir / "build-book.jsx"
    jsx_path.write_text(
        build_jsx(
            pages=pages,
            project_id=project_id,
            document_title=document_title,
            trim_width_mm=trim_width_mm,
            trim_height_mm=trim_height_mm,
            bleed_mm=bleed_mm,
            indd_path=indd_path,
            pdf_path=pdf_path,
        ),
        encoding="utf-8-sig",
    )

    preliminary = build_report(
        project_id=project_id,
        mode=mode,
        pages=pages,
        trim_width_mm=trim_width_mm,
        trim_height_mm=trim_height_mm,
        output_dir=output_dir,
        execution=None,
    )
    if mode == "print" and preliminary["quality"]["blockers"]:
        raise ValueError("print build blocked: " + ", ".join(preliminary["quality"]["blockers"]))

    execution = run_jsx_via_com(jsx_path) if execute else None
    if execute:
        if execution.get("pages") != len(pages):
            raise RuntimeError(f"InDesign page count mismatch: {execution.get('pages')} != {len(pages)}")
        for output in (indd_path, pdf_path):
            if not output.is_file() or output.stat().st_size == 0:
                raise RuntimeError(f"InDesign output missing or empty: {output}")

    report = build_report(
        project_id=project_id,
        mode=mode,
        pages=pages,
        trim_width_mm=trim_width_mm,
        trim_height_mm=trim_height_mm,
        output_dir=output_dir,
        execution=execution,
    )
    (output_dir / "indesign-build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--page-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--mode", choices=("proof", "print"), default="proof")
    parser.add_argument("--trim-width-mm", type=float, default=145)
    parser.add_argument("--trim-height-mm", type=float, default=210)
    parser.add_argument("--bleed-mm", type=float, default=0)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        report = compile_build(
            project_root=args.project_root,
            page_dir=args.page_dir,
            output_dir=args.output_dir,
            project_id=args.project_id,
            document_title=args.title,
            mode=args.mode,
            trim_width_mm=args.trim_width_mm,
            trim_height_mm=args.trim_height_mm,
            bleed_mm=args.bleed_mm,
            execute=args.execute,
        )
    except (FileNotFoundError, ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=os.sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
