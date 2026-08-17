#target indesign
(function () {
    var target = File("D:/book-production-skills-v1/projects/lost-human-world-cover/indesign/book-proof.indd");
    if (!target.exists) {
        throw new Error("InDesign proof file not found: " + target.fsName);
    }

    var doc = null;
    for (var index = 0; index < app.documents.length; index++) {
        try {
            if (app.documents.item(index).fullName.fsName === target.fsName) {
                doc = app.documents.item(index);
                break;
            }
        } catch (error) {}
    }
    if (doc === null) {
        doc = app.open(target, true);
    }
    if (doc.layoutWindows.length > 0) {
        doc.layoutWindows.item(0).activePage = doc.pages.item(0);
        doc.layoutWindows.item(0).zoomPercentage = 70;
    }
    app.activate();
    return '{"status":"opened","name":"' + doc.name + '","pages":' + doc.pages.length + ',"links":' + doc.links.length + '}';
})();
