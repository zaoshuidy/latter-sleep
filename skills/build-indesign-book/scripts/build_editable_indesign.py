#!/usr/bin/env python3
"""Build a native editable InDesign proof from structured book project sources."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from PIL import Image


BODY_PAGE_COUNTS = (5, 5, 8, 8, 13, 10)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def parse_manuscript(path: Path) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if not blocks or not blocks[0].startswith("# "):
        raise ValueError("manuscript must start with one '# ' chapter heading")
    chapter_title = blocks[0][2:].strip()
    paragraphs = blocks[1:]
    if not paragraphs:
        raise ValueError("manuscript has no body paragraphs")
    return chapter_title, paragraphs


def crop_cover_pages(
    source: Path,
    front_output: Path,
    back_output: Path,
    *,
    spread_width_mm: float,
    spread_height_mm: float,
    trim_width_mm: float,
    trim_height_mm: float,
    bleed_mm: float,
    spine_width_mm: float,
) -> None:
    with Image.open(source) as image:
        image = image.convert("RGB")
        px_per_mm_x = image.width / spread_width_mm
        px_per_mm_y = image.height / spread_height_mm
        top = round(bleed_mm * px_per_mm_y)
        bottom = round((bleed_mm + trim_height_mm) * px_per_mm_y)
        back_left = round(bleed_mm * px_per_mm_x)
        back_right = round((bleed_mm + trim_width_mm) * px_per_mm_x)
        front_left = round(
            (bleed_mm + trim_width_mm + spine_width_mm) * px_per_mm_x
        )
        front_right = round(
            (bleed_mm + trim_width_mm + spine_width_mm + trim_width_mm)
            * px_per_mm_x
        )
        front_output.parent.mkdir(parents=True, exist_ok=True)
        back_output.parent.mkdir(parents=True, exist_ok=True)
        image.crop((front_left, top, front_right, bottom)).save(
            front_output, dpi=(300, 300), optimize=True
        )
        image.crop((back_left, top, back_right, bottom)).save(
            back_output, dpi=(300, 300), optimize=True
        )


def _jsx_string(value: str | Path) -> str:
    return json.dumps(str(value).replace("\\", "/"), ensure_ascii=False)


def _jsx_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_editable_jsx(
    *,
    project_id: str,
    book_title: str,
    subtitle: str,
    author: str,
    studio_mark: str,
    chapter_title: str,
    paragraphs: list[str],
    toc_entries: list[dict[str, Any]],
    front_cover: Path,
    back_cover: Path,
    indd_path: Path,
    idml_path: Path,
    pdf_path: Path,
) -> str:
    chapter_number, chapter_name = (
        chapter_title.split(" ", 1) if " " in chapter_title else (chapter_title, "")
    )
    if sum(BODY_PAGE_COUNTS) != len(paragraphs):
        raise ValueError(
            f"body page plan covers {sum(BODY_PAGE_COUNTS)} paragraphs, manuscript has {len(paragraphs)}"
        )

    return f'''#target indesign
(function () {{
    var previousInteraction = app.scriptPreferences.userInteractionLevel;
    var doc = null;
    function font(name, fallback) {{
        var selected = app.fonts.itemByName(name);
        if (selected.isValid) return selected;
        selected = app.fonts.itemByName(fallback);
        if (!selected.isValid) throw new Error("No valid font: " + name + " / " + fallback);
        return selected;
    }}
    function color(name, values) {{
        var swatch = doc.colors.itemByName(name);
        if (!swatch.isValid) swatch = doc.colors.add({{name:name, model:ColorModel.PROCESS, space:ColorSpace.CMYK, colorValue:values}});
        return swatch;
    }}
    function paragraphStyle(name, props) {{
        var style = doc.paragraphStyles.itemByName(name);
        if (!style.isValid) style = doc.paragraphStyles.add({{name:name}});
        for (var key in props) {{ try {{ style[key] = props[key]; }} catch (error) {{}} }}
        return style;
    }}
    function spreadBounds(page, bounds) {{
        var pageBounds = page.bounds;
        return [
            pageBounds[0] + bounds[0],
            pageBounds[1] + bounds[1],
            pageBounds[0] + bounds[2],
            pageBounds[1] + bounds[3]
        ];
    }}
    function spreadPoints(page, points) {{
        var pageBounds = page.bounds;
        var converted = [];
        for (var pointIndex = 0; pointIndex < points.length; pointIndex++) {{
            converted.push([pageBounds[1] + points[pointIndex][0], pageBounds[0] + points[pointIndex][1]]);
        }}
        return converted;
    }}
    function textFrame(page, bounds, contents, style, layer) {{
        var frame = page.textFrames.add();
        frame.geometricBounds = spreadBounds(page, bounds);
        frame.itemLayer = layer;
        frame.contents = contents;
        if (frame.paragraphs.length > 0 && style !== null) frame.paragraphs.everyItem().appliedParagraphStyle = style;
        frame.textFramePreferences.firstBaselineOffset = FirstBaseline.LEADING_OFFSET;
        frame.insertLabel("book-production-editable", "true");
        return frame;
    }}
    function verticalFrame(page, bounds, contents, style, layer) {{
        var frame = textFrame(page, bounds, contents, style, layer);
        frame.parentStory.storyPreferences.storyOrientation = StoryHorizontalOrVertical.VERTICAL;
        return frame;
    }}
    function paperBackground(page, paper, layer) {{
        var rect = page.rectangles.add({{geometricBounds:spreadBounds(page,[0,0,210,145]), strokeWeight:0, fillColor:paper}});
        rect.itemLayer = layer;
        rect.sendToBack();
        return rect;
    }}
    function parent(prefix, baseName) {{
        var spread = doc.masterSpreads.add();
        spread.namePrefix = prefix;
        spread.baseName = baseName;
        spread.insertLabel("page-family", prefix + "-" + baseName);
        return spread;
    }}
    function placeFullPage(page, path, layer) {{
        var source = File(path);
        if (!source.exists) throw new Error("Missing image: " + source.fsName);
        var rect = page.rectangles.add({{geometricBounds:spreadBounds(page,[0,0,210,145]), strokeWeight:0}});
        rect.itemLayer = layer;
        rect.place(source);
        rect.fit(FitOptions.FILL_PROPORTIONALLY);
        rect.fit(FitOptions.CENTER_CONTENT);
        return rect;
    }}
    function outerBounds(page, top, bottom) {{
        var isLeft = page.side === PageSideOptions.LEFT_HAND;
        return isLeft ? [top,18,210-bottom,123] : [top,22,210-bottom,127];
    }}
    function addFolio(page, value, style, layer) {{
        var isLeft = page.side === PageSideOptions.LEFT_HAND;
        var frame = textFrame(page, isLeft ? [194,18,199,38] : [194,107,199,127], String(value), style, layer);
        frame.paragraphs.item(0).justification = isLeft ? Justification.LEFT_ALIGN : Justification.RIGHT_ALIGN;
    }}
    function addRunningHead(page, value, style, layer) {{
        var isLeft = page.side === PageSideOptions.LEFT_HAND;
        var frame = textFrame(page, isLeft ? [12,18,17,65] : [12,80,17,127], value, style, layer);
        frame.paragraphs.item(0).justification = isLeft ? Justification.LEFT_ALIGN : Justification.RIGHT_ALIGN;
    }}
    function closeOpenOutput(path) {{
        for (var index = app.documents.length - 1; index >= 0; index--) {{
            try {{ if (app.documents.item(index).fullName.fsName === File(path).fsName) app.documents.item(index).close(SaveOptions.NO); }} catch (error) {{}}
        }}
    }}
    try {{
        app.scriptPreferences.userInteractionLevel = UserInteractionLevels.NEVER_INTERACT;
        var inddFile = File({_jsx_string(indd_path.resolve())});
        var idmlFile = File({_jsx_string(idml_path.resolve())});
        var pdfFile = File({_jsx_string(pdf_path.resolve())});
        closeOpenOutput(inddFile.fsName);
        if (inddFile.exists) inddFile.remove();
        if (idmlFile.exists) idmlFile.remove();
        if (pdfFile.exists) pdfFile.remove();

        doc = app.documents.add();
        doc.documentPreferences.facingPages = true;
        doc.documentPreferences.pageWidth = "145mm";
        doc.documentPreferences.pageHeight = "210mm";
        doc.documentPreferences.documentBleedTopOffset = "3mm";
        doc.documentPreferences.documentBleedBottomOffset = "3mm";
        doc.documentPreferences.documentBleedInsideOrLeftOffset = "3mm";
        doc.documentPreferences.documentBleedOutsideOrRightOffset = "3mm";
        doc.viewPreferences.horizontalMeasurementUnits = MeasurementUnits.MILLIMETERS;
        doc.viewPreferences.verticalMeasurementUnits = MeasurementUnits.MILLIMETERS;
        doc.gridPreferences.baselineDivision = 17.5;
        doc.gridPreferences.baselineStart = 26;
        doc.metadataPreferences.documentTitle = {_jsx_string(book_title)};
        doc.insertLabel("book-production-project-id", {_jsx_string(project_id)});
        doc.insertLabel("trim-profile", "large-32mo-145x210mm");
        doc.insertLabel("layout-mode", "native-editable-v001");

        while (doc.pages.length < 14) doc.pages.add(LocationOptions.AT_END);
        while (doc.pages.length > 14) doc.pages.lastItem().remove();

        var backgroundLayer = doc.layers.item(0);
        backgroundLayer.name = "Background and approved art";
        var textLayer = doc.layers.add({{name:"Editable text"}});
        var navigationLayer = doc.layers.add({{name:"Running heads and folios"}});

        var paper = color("Paper Warm", [4,5,9,0]);
        var ink = color("Ink", [67,60,61,72]);
        var accent = color("Accent Red", [31,94,74,30]);
        var quiet = color("Quiet Taupe", [29,28,32,8]);
        var bodyFont = font("Source Han Serif SC\tRegular", "Noto Serif CJK SC\tRegular");
        var sansFont = font("Microsoft YaHei\tRegular", "微软雅黑\tRegular");

        var pTitle = paragraphStyle("P-TITLE", {{appliedFont:bodyFont, pointSize:25, leading:31, fillColor:ink, justification:Justification.CENTER_ALIGN, tracking:220}});
        var pSubtitle = paragraphStyle("P-SUBTITLE", {{appliedFont:bodyFont, pointSize:8.5, leading:14, fillColor:quiet, justification:Justification.CENTER_ALIGN, tracking:80}});
        var pAuthor = paragraphStyle("P-AUTHOR", {{appliedFont:bodyFont, pointSize:9, leading:14, fillColor:ink, justification:Justification.CENTER_ALIGN, tracking:100}});
        var pStudio = paragraphStyle("P-STUDIO", {{appliedFont:sansFont, pointSize:7, leading:10, fillColor:quiet, justification:Justification.CENTER_ALIGN, tracking:80}});
        var pTocHeading = paragraphStyle("P-TOC-HEADING", {{appliedFont:bodyFont, pointSize:18, leading:24, fillColor:ink, tracking:160}});
        var pTocEntry = paragraphStyle("P-TOC-ENTRY", {{appliedFont:bodyFont, pointSize:9, leading:14, fillColor:ink, tracking:20}});
        var pTocLevel = paragraphStyle("P-TOC-LEVEL", {{appliedFont:sansFont, pointSize:6.8, leading:10, fillColor:accent, tracking:100}});
        var pChapterNo = paragraphStyle("P-CH-NO", {{appliedFont:bodyFont, pointSize:8, leading:12, fillColor:accent, tracking:280}});
        var pChapterTitle = paragraphStyle("P-CH-TTL", {{appliedFont:bodyFont, pointSize:21, leading:27, fillColor:ink, tracking:160, keepAllLinesTogether:true}});
        var pBody = paragraphStyle("P-BD-01", {{appliedFont:bodyFont, pointSize:10.5, leading:17.5, fillColor:ink, justification:Justification.LEFT_JUSTIFIED, firstLineIndent:21, spaceBefore:0, spaceAfter:0, keepFirstLines:2, keepLastLines:2}});
        var pBodyFirst = paragraphStyle("P-BD-FIRST", {{appliedFont:bodyFont, pointSize:10.5, leading:17.5, fillColor:ink, justification:Justification.LEFT_JUSTIFIED, firstLineIndent:0, spaceBefore:0, spaceAfter:0, keepFirstLines:2, keepLastLines:2}});
        var pHeader = paragraphStyle("P-RUNNING-HEAD", {{appliedFont:bodyFont, pointSize:7.5, leading:10, fillColor:quiet, tracking:90}});
        var pFolio = paragraphStyle("P-FOLIO", {{appliedFont:sansFont, pointSize:7.5, leading:10, fillColor:quiet, tracking:40}});

        var parentA = doc.masterSpreads.item(0); parentA.namePrefix = "A"; parentA.baseName = "Body"; parentA.insertLabel("page-family", "A-Body");
        var parentB = parent("B", "Blank"); // B-Blank
        var parentC = parent("C", "FrontMatter"); // C-FrontMatter
        var parentD = parent("D", "TOC"); // D-TOC
        var parentE = parent("E", "Chapter"); // E-Chapter
        var parentF = parent("F", "BodyFirst"); // F-BodyFirst

        for (var pageIndex = 0; pageIndex < doc.pages.length; pageIndex++) {{
            if (pageIndex !== 0 && pageIndex !== 13) paperBackground(doc.pages.item(pageIndex), paper, backgroundLayer);
        }}

        var front = doc.pages.item(0); front.appliedMaster = parentB; front.insertLabel("page-role", "front-cover");
        placeFullPage(front, {_jsx_string(front_cover.resolve())}, backgroundLayer);

        var insideFront = doc.pages.item(1); insideFront.appliedMaster = parentB; insideFront.insertLabel("page-role", "blank-verso");

        var titlePage = doc.pages.item(2); titlePage.appliedMaster = parentC; titlePage.insertLabel("page-role", "title-page");
        var titleLine = titlePage.graphicLines.add({{strokeColor:accent, strokeWeight:0.45}}); titleLine.itemLayer = textLayer; titleLine.paths.item(0).entirePath = spreadPoints(titlePage,[[39,18],[39,75]]);
        var titleLine2 = titlePage.graphicLines.add({{strokeColor:accent, strokeWeight:0.45}}); titleLine2.itemLayer = textLayer; titleLine2.paths.item(0).entirePath = spreadPoints(titlePage,[[39,132],[39,192]]);
        verticalFrame(titlePage, [42,56,134,79], {_jsx_string(book_title)}, pTitle, textLayer);
        verticalFrame(titlePage, [55,84,128,94], {_jsx_string(subtitle)}, pSubtitle, textLayer);
        verticalFrame(titlePage, [72,102,126,112], {_jsx_string(author)}, pAuthor, textLayer);
        textFrame(titlePage, [182,50,190,95], {_jsx_string(studio_mark)}, pStudio, textLayer);

        var tocEntries = {_jsx_value(toc_entries)};
        for (var tocPageOffset = 0; tocPageOffset < 2; tocPageOffset++) {{
            var tocPage = doc.pages.item(3 + tocPageOffset); tocPage.appliedMaster = parentD; tocPage.insertLabel("page-role", tocPageOffset === 0 ? "toc-verso" : "toc-recto");
            var axis = tocPage.graphicLines.add({{strokeColor:accent, strokeWeight:0.5}}); axis.itemLayer = textLayer; axis.paths.item(0).entirePath = spreadPoints(tocPage,[[28,24],[28,186]]);
            if (tocPageOffset === 0) textFrame(tocPage, [28,38,46,116], "目录", pTocHeading, textLayer);
            var start = tocPageOffset === 0 ? 0 : 5;
            var end = tocPageOffset === 0 ? 5 : tocEntries.length;
            for (var tocIndex = start; tocIndex < end; tocIndex++) {{
                var local = tocIndex - start;
                var y = 60 + local * 22;
                textFrame(tocPage, [y,38,y+7,57], tocEntries[tocIndex].level, pTocLevel, textLayer);
                textFrame(tocPage, [y+6,38,y+16,112], tocEntries[tocIndex].title, pTocEntry, textLayer);
                var pageNo = textFrame(tocPage, [y+6,114,y+16,127], String(tocEntries[tocIndex].page), pTocEntry, textLayer);
                pageNo.paragraphs.item(0).justification = Justification.RIGHT_ALIGN;
            }}
        }}

        var chapterLeft = doc.pages.item(5); chapterLeft.appliedMaster = parentE; chapterLeft.insertLabel("page-role", "chapter-opener-left");
        var boundary = chapterLeft.graphicLines.add({{strokeColor:accent, strokeWeight:0.55}}); boundary.itemLayer = textLayer; boundary.paths.item(0).entirePath = spreadPoints(chapterLeft,[[8,38],[28,65],[17,112],[35,171],[24,195]]);
        var chapterRight = doc.pages.item(6); chapterRight.appliedMaster = parentE; chapterRight.insertLabel("page-role", "chapter-opener-right");
        verticalFrame(chapterRight, [32,92,72,102], {_jsx_string(chapter_number)}, pChapterNo, textLayer);
        verticalFrame(chapterRight, [58,105,150,133], {_jsx_string(chapter_name)}, pChapterTitle, textLayer);

        var bodyParagraphs = {_jsx_value(paragraphs)};
        var bodyFrames = [];
        for (var bodyIndex = 0; bodyIndex < 6; bodyIndex++) {{
            var bodyPage = doc.pages.item(7 + bodyIndex);
            bodyPage.appliedMaster = bodyIndex === 0 ? parentF : parentA;
            bodyPage.insertLabel("page-role", bodyIndex === 0 ? "body-first" : "body-standard");
            bodyFrames.push(textFrame(bodyPage, outerBounds(bodyPage, bodyIndex === 0 ? 54 : 26, 24), "", pBody, textLayer));
            addFolio(bodyPage, 6 + bodyIndex, pFolio, navigationLayer);
            if (bodyIndex > 0) addRunningHead(bodyPage, bodyPage.side === PageSideOptions.LEFT_HAND ? {_jsx_string(book_title)} : {_jsx_string(chapter_name)}, pHeader, navigationLayer);
        }}
        for (var threadIndex = 0; threadIndex < bodyFrames.length - 1; threadIndex++) bodyFrames[threadIndex].nextTextFrame = bodyFrames[threadIndex + 1];
        var story = bodyFrames[0].parentStory;
        story.contents = bodyParagraphs.join("\\r");
        story.paragraphs.everyItem().appliedParagraphStyle = pBody;
        story.paragraphs.item(0).appliedParagraphStyle = pBodyFirst;

        var back = doc.pages.item(13); back.appliedMaster = parentB; back.insertLabel("page-role", "back-cover");
        placeFullPage(back, {_jsx_string(back_cover.resolve())}, backgroundLayer);

        var overset = 0;
        for (var textIndex = 0; textIndex < doc.textFrames.length; textIndex++) if (doc.textFrames.item(textIndex).overflows) overset++;
        var missingLinks = 0;
        var lowResolution = 0;
        for (var linkIndex = 0; linkIndex < doc.links.length; linkIndex++) {{
            if (doc.links.item(linkIndex).status === LinkStatus.LINK_MISSING) missingLinks++;
            try {{
                var ppi = doc.links.item(linkIndex).parent.parent.effectivePpi;
                if (ppi.length > 1 && (ppi[0] < 295 || ppi[1] < 295)) lowResolution++;
            }} catch (ppiError) {{}}
        }}
        if (overset > 0) throw new Error("Overset text frames: " + overset);
        if (missingLinks > 0) throw new Error("Missing links: " + missingLinks);

        doc.save(inddFile);
        doc.exportFile(ExportFormat.INDESIGN_MARKUP, idmlFile, false);
        app.pdfExportPreferences.exportReaderSpreads = false;
        app.pdfExportPreferences.pageRange = PageRange.ALL_PAGES;
        app.pdfExportPreferences.useDocumentBleedWithPDF = false;
        app.pdfExportPreferences.viewPDF = false;
        doc.exportFile(ExportFormat.PDF_TYPE, pdfFile, false);
        if (doc.layoutWindows.length > 0) {{ doc.layoutWindows.item(0).activePage = doc.pages.item(7); doc.layoutWindows.item(0).zoomPercentage = 105; }}
        app.activate();
        return '{{"status":"built","application":"' + app.name + '","version":"' + app.version + '","pages":' + doc.pages.length + ',"links":' + doc.links.length + ',"textFrames":' + doc.textFrames.length + ',"paragraphStyles":' + doc.paragraphStyles.length + ',"parentSpreads":' + doc.masterSpreads.length + ',"overset":' + overset + ',"missingLinks":' + missingLinks + ',"lowResolutionLinks":' + lowResolution + '}}';
    }} catch (error) {{
        if (doc !== null && !doc.saved) {{ try {{ doc.close(SaveOptions.NO); }} catch (closeError) {{}} }}
        throw error;
    }} finally {{
        app.scriptPreferences.userInteractionLevel = previousInteraction;
    }}
}})();
'''


def _load_bridge():
    path = Path(__file__).with_name("build_indesign_book.py")
    spec = importlib.util.spec_from_file_location("build_indesign_bridge", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load InDesign COM bridge")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compile_editable(project_root: Path, output_dir: Path, *, execute: bool) -> dict[str, Any]:
    project_root = project_root.resolve()
    output_dir = output_dir if output_dir.is_absolute() else project_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    chapter_title, paragraphs = parse_manuscript(project_root / "manuscript" / "chapter-01.md")
    toc = load_json(project_root / "toc" / "toc-direction-b-v001-layout.json")
    title = load_json(project_root / "title-page" / "title-page-v001-layout.json")
    text_values = {item["role"]: item["value"] for item in title["text_layers"]}

    asset_dir = output_dir / "assets"
    front_cover = asset_dir / "front-cover-300ppi.png"
    back_cover = asset_dir / "back-cover-300ppi.png"
    cover_source = project_root / "generated" / "full-cover-v001-preview.png"
    crop_cover_pages(
        cover_source,
        front_cover,
        back_cover,
        spread_width_mm=309,
        spread_height_mm=216,
        trim_width_mm=145,
        trim_height_mm=210,
        bleed_mm=3,
        spine_width_mm=13,
    )
    indd_path = output_dir / "book-editable-v001.indd"
    idml_path = output_dir / "book-editable-v001.idml"
    pdf_path = output_dir / "book-editable-v001.pdf"
    jsx_path = output_dir / "build-editable-book.jsx"
    jsx_path.write_text(
        build_editable_jsx(
            project_id="BOOK-LOST-HUMAN-WORLD",
            book_title=text_values["title"],
            subtitle=text_values["subtitle"],
            author=text_values["author"],
            studio_mark=text_values["studio_mark"],
            chapter_title=chapter_title,
            paragraphs=paragraphs,
            toc_entries=toc["entries"],
            front_cover=front_cover,
            back_cover=back_cover,
            indd_path=indd_path,
            idml_path=idml_path,
            pdf_path=pdf_path,
        ),
        encoding="utf-8-sig",
    )
    execution = _load_bridge().run_jsx_via_com(jsx_path, 240) if execute else None
    outputs = {"indd": indd_path, "idml": idml_path, "pdf": pdf_path}
    if execute:
        for name, path in outputs.items():
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError(f"missing {name} output: {path}")
    report = {
        "schema_version": "1.0",
        "project_id": "BOOK-LOST-HUMAN-WORLD",
        "status": "built" if execution else "compiled",
        "mode": "native-editable-proof",
        "trim_profile": "large-32mo-145x210mm",
        "trim_mm": [145, 210],
        "body_typography": {
            "font": "Source Han Serif SC Regular",
            "size_pt": 10.5,
            "leading_pt": 17.5,
            "first_line_indent_em": 2,
            "margins_mm": {"top": 26, "inside": 22, "outside": 18, "bottom": 24},
        },
        "editable_components": ["title-page", "toc", "chapter-opener", "body", "running-heads", "folios"],
        "raster_components": ["front-cover", "back-cover"],
        "paragraph_count": len(paragraphs),
        "cover_source_sha256": hashlib.sha256(cover_source.read_bytes()).hexdigest(),
        "outputs": {name: str(path) for name, path in outputs.items()},
        "execution": execution,
    }
    (output_dir / "editable-build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("indesign/editable-v001"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        report = compile_editable(args.project_root, args.output_dir, execute=args.execute)
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
