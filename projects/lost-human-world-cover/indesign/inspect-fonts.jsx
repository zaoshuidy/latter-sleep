#target indesign
(function () {
    var preferred = [
        "Source Han Serif SC\tRegular",
        "Noto Serif CJK SC\tRegular",
        "思源宋体\tRegular",
        "方正书宋_GBK\tRegular",
        "FZShuSong-Z01\tRegular",
        "SimSun\tRegular",
        "宋体\tRegular",
        "Microsoft YaHei\tRegular",
        "微软雅黑\tRegular"
    ];
    var found = [];
    for (var preferredIndex = 0; preferredIndex < preferred.length; preferredIndex++) {
        var font = app.fonts.itemByName(preferred[preferredIndex]);
        if (font.isValid) found.push(preferred[preferredIndex]);
    }
    var encoded = [];
    for (var foundIndex = 0; foundIndex < found.length; foundIndex++) {
        encoded.push('"' + found[foundIndex].replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\t/g, "\\t") + '"');
    }
    return '{"status":"ok","fonts":[' + encoded.join(",") + ']}';
})();
