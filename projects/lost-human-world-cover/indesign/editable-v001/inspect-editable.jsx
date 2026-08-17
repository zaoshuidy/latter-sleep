#target indesign
(function () {
    var doc = app.documents.itemByName("book-editable-v001.indd");
    if (!doc.isValid) throw new Error("Editable document is not open");
    var bodyStyle = doc.paragraphStyles.itemByName("P-BD-01");
    var parents = [];
    for (var index = 0; index < doc.masterSpreads.length; index++) parents.push(doc.masterSpreads.item(index).name);
    var bodyFrames = 0;
    var editableFrames = 0;
    for (var frameIndex = 0; frameIndex < doc.textFrames.length; frameIndex++) {
        var frame = doc.textFrames.item(frameIndex);
        if (frame.extractLabel("book-production-editable") === "true") editableFrames++;
        if (frame.parentPage !== null && frame.parentPage.extractLabel("page-role").indexOf("body") === 0) bodyFrames++;
    }
    var encodedParents = [];
    for (var parentIndex = 0; parentIndex < parents.length; parentIndex++) encodedParents.push('"' + parents[parentIndex].replace(/"/g, '\\"') + '"');
    return '{"status":"ok","name":"' + doc.name + '","pages":' + doc.pages.length +
        ',"pageWidthMm":' + doc.documentPreferences.pageWidth +
        ',"pageHeightMm":' + doc.documentPreferences.pageHeight +
        ',"editableFrames":' + editableFrames + ',"bodyFrames":' + bodyFrames +
        ',"bodySizePt":' + bodyStyle.pointSize + ',"bodyLeadingPt":' + bodyStyle.leading +
        ',"bodyIndentPt":' + bodyStyle.firstLineIndent + ',"parents":[' + encodedParents.join(",") + ']}';
})();
