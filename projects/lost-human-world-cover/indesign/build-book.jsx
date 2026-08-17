#target indesign
(function () {
    var previousInteraction = app.scriptPreferences.userInteractionLevel;
    var doc = null;
    try {
        app.scriptPreferences.userInteractionLevel = UserInteractionLevels.NEVER_INTERACT;
        var pageFiles = [
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/00-front-cover.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/01-inside-front-cover.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/02-title-page.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/03-toc-left.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/04-toc-right.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/05-chapter-opener-left.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/06-chapter-opener-right.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/07-body-6.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/08-body-7.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/09-body-8.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/10-body-9.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/11-body-10.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/12-body-11.png",
        "D:/book-production-skills-v1/projects/lost-human-world-cover/ebook/pages-v003/13-back-cover.png"
        ];
        var inddFile = File("D:/book-production-skills-v1/projects/lost-human-world-cover/indesign/book-proof.indd");
        var pdfFile = File("D:/book-production-skills-v1/projects/lost-human-world-cover/indesign/book-proof.pdf");
        if (inddFile.exists) inddFile.remove();
        if (pdfFile.exists) pdfFile.remove();

        doc = app.documents.add();
        doc.documentPreferences.facingPages = true;
        doc.documentPreferences.pageWidth = "145mm";
        doc.documentPreferences.pageHeight = "210mm";
        doc.documentPreferences.documentBleedTopOffset = "0mm";
        doc.documentPreferences.documentBleedBottomOffset = "0mm";
        doc.documentPreferences.documentBleedInsideOrLeftOffset = "0mm";
        doc.documentPreferences.documentBleedOutsideOrRightOffset = "0mm";
        doc.metadataPreferences.documentTitle = "失落人间";
        doc.insertLabel("book-production-project-id", "BOOK-LOST-HUMAN-WORLD");
        doc.insertLabel("book-production-mode", "approved-page-proof");

        while (doc.pages.length < pageFiles.length) {
            doc.pages.add(LocationOptions.AT_END);
        }
        while (doc.pages.length > pageFiles.length) {
            doc.pages.lastItem().remove();
        }

        var proofLayer = doc.layers.item(0);
        proofLayer.name = "Approved Page Proofs";
        for (var i = 0; i < pageFiles.length; i++) {
            var source = File(pageFiles[i]);
            if (!source.exists) throw new Error("Missing page asset: " + source.fsName);
            var page = doc.pages.item(i);
            var frame = page.rectangles.add({
                geometricBounds: [0, 0, 210, 145],
                strokeWeight: 0
            });
            frame.itemLayer = proofLayer;
            frame.label = "approved-page:" + source.name;
            frame.place(source);
            frame.fit(FitOptions.FILL_PROPORTIONALLY);
            frame.fit(FitOptions.CENTER_CONTENT);
        }

        doc.save(inddFile);
        app.pdfExportPreferences.exportReaderSpreads = false;
        app.pdfExportPreferences.pageRange = PageRange.ALL_PAGES;
        app.pdfExportPreferences.useDocumentBleedWithPDF = false;
        app.pdfExportPreferences.viewPDF = false;
        doc.exportFile(ExportFormat.PDF_TYPE, pdfFile, false);
        var result = '{"status":"built","application":"' + app.name +
            '","version":"' + app.version + '","pages":' + doc.pages.length +
            ',"links":' + doc.links.length + '}';
        doc.close(SaveOptions.NO);
        doc = null;
        return result;
    } catch (error) {
        if (doc !== null) {
            try { doc.close(SaveOptions.NO); } catch (closeError) {}
        }
        throw error;
    } finally {
        app.scriptPreferences.userInteractionLevel = previousInteraction;
    }
})();
