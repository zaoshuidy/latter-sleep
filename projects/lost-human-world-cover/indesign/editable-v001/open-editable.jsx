#target indesign
(function () {
    var target = File("D:/book-production-skills-v1/projects/lost-human-world-cover/indesign/editable-v001/book-editable-v001.indd");
    var doc = app.documents.itemByName("book-editable-v001.indd");
    if (!doc.isValid) doc = app.open(target, true);
    doc.save();
    if (doc.layoutWindows.length > 0) {
        doc.layoutWindows.item(0).activePage = doc.pages.item(7);
        doc.layoutWindows.item(0).zoomPercentage = 105;
    }
    app.activate();
    return '{"status":"opened","name":"' + doc.name + '","pages":' + doc.pages.length + ',"editableFrames":' + doc.textFrames.length + '}';
})();
