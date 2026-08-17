#target indesign
(function () {
    var previousInteraction = app.scriptPreferences.userInteractionLevel;
    var doc = null;
    function font(name, fallback) {
        var selected = app.fonts.itemByName(name);
        if (selected.isValid) return selected;
        selected = app.fonts.itemByName(fallback);
        if (!selected.isValid) throw new Error("No valid font: " + name + " / " + fallback);
        return selected;
    }
    function color(name, values) {
        var swatch = doc.colors.itemByName(name);
        if (!swatch.isValid) swatch = doc.colors.add({name:name, model:ColorModel.PROCESS, space:ColorSpace.CMYK, colorValue:values});
        return swatch;
    }
    function paragraphStyle(name, props) {
        var style = doc.paragraphStyles.itemByName(name);
        if (!style.isValid) style = doc.paragraphStyles.add({name:name});
        for (var key in props) { try { style[key] = props[key]; } catch (error) {} }
        return style;
    }
    function spreadBounds(page, bounds) {
        var pageBounds = page.bounds;
        return [
            pageBounds[0] + bounds[0],
            pageBounds[1] + bounds[1],
            pageBounds[0] + bounds[2],
            pageBounds[1] + bounds[3]
        ];
    }
    function spreadPoints(page, points) {
        var pageBounds = page.bounds;
        var converted = [];
        for (var pointIndex = 0; pointIndex < points.length; pointIndex++) {
            converted.push([pageBounds[1] + points[pointIndex][0], pageBounds[0] + points[pointIndex][1]]);
        }
        return converted;
    }
    function textFrame(page, bounds, contents, style, layer) {
        var frame = page.textFrames.add();
        frame.geometricBounds = spreadBounds(page, bounds);
        frame.itemLayer = layer;
        frame.contents = contents;
        if (frame.paragraphs.length > 0 && style !== null) frame.paragraphs.everyItem().appliedParagraphStyle = style;
        frame.textFramePreferences.firstBaselineOffset = FirstBaseline.LEADING_OFFSET;
        frame.insertLabel("book-production-editable", "true");
        return frame;
    }
    function verticalFrame(page, bounds, contents, style, layer) {
        var frame = textFrame(page, bounds, contents, style, layer);
        frame.parentStory.storyPreferences.storyOrientation = StoryHorizontalOrVertical.VERTICAL;
        return frame;
    }
    function paperBackground(page, paper, layer) {
        var rect = page.rectangles.add({geometricBounds:spreadBounds(page,[0,0,210,145]), strokeWeight:0, fillColor:paper});
        rect.itemLayer = layer;
        rect.sendToBack();
        return rect;
    }
    function parent(prefix, baseName) {
        var spread = doc.masterSpreads.add();
        spread.namePrefix = prefix;
        spread.baseName = baseName;
        spread.insertLabel("page-family", prefix + "-" + baseName);
        return spread;
    }
    function placeFullPage(page, path, layer) {
        var source = File(path);
        if (!source.exists) throw new Error("Missing image: " + source.fsName);
        var rect = page.rectangles.add({geometricBounds:spreadBounds(page,[0,0,210,145]), strokeWeight:0});
        rect.itemLayer = layer;
        rect.place(source);
        rect.fit(FitOptions.FILL_PROPORTIONALLY);
        rect.fit(FitOptions.CENTER_CONTENT);
        return rect;
    }
    function outerBounds(page, top, bottom) {
        var isLeft = page.side === PageSideOptions.LEFT_HAND;
        return isLeft ? [top,18,210-bottom,123] : [top,22,210-bottom,127];
    }
    function addFolio(page, value, style, layer) {
        var isLeft = page.side === PageSideOptions.LEFT_HAND;
        var frame = textFrame(page, isLeft ? [194,18,199,38] : [194,107,199,127], String(value), style, layer);
        frame.paragraphs.item(0).justification = isLeft ? Justification.LEFT_ALIGN : Justification.RIGHT_ALIGN;
    }
    function addRunningHead(page, value, style, layer) {
        var isLeft = page.side === PageSideOptions.LEFT_HAND;
        var frame = textFrame(page, isLeft ? [12,18,17,65] : [12,80,17,127], value, style, layer);
        frame.paragraphs.item(0).justification = isLeft ? Justification.LEFT_ALIGN : Justification.RIGHT_ALIGN;
    }
    function closeOpenOutput(path) {
        for (var index = app.documents.length - 1; index >= 0; index--) {
            try { if (app.documents.item(index).fullName.fsName === File(path).fsName) app.documents.item(index).close(SaveOptions.NO); } catch (error) {}
        }
    }
    try {
        app.scriptPreferences.userInteractionLevel = UserInteractionLevels.NEVER_INTERACT;
        var inddFile = File("D:/book-production-skills-v1/projects/lost-human-world-cover/indesign/editable-v001/book-editable-v001.indd");
        var idmlFile = File("D:/book-production-skills-v1/projects/lost-human-world-cover/indesign/editable-v001/book-editable-v001.idml");
        var pdfFile = File("D:/book-production-skills-v1/projects/lost-human-world-cover/indesign/editable-v001/book-editable-v001.pdf");
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
        doc.metadataPreferences.documentTitle = "失落人间";
        doc.insertLabel("book-production-project-id", "BOOK-LOST-HUMAN-WORLD");
        doc.insertLabel("trim-profile", "large-32mo-145x210mm");
        doc.insertLabel("layout-mode", "native-editable-v001");

        while (doc.pages.length < 14) doc.pages.add(LocationOptions.AT_END);
        while (doc.pages.length > 14) doc.pages.lastItem().remove();

        var backgroundLayer = doc.layers.item(0);
        backgroundLayer.name = "Background and approved art";
        var textLayer = doc.layers.add({name:"Editable text"});
        var navigationLayer = doc.layers.add({name:"Running heads and folios"});

        var paper = color("Paper Warm", [4,5,9,0]);
        var ink = color("Ink", [67,60,61,72]);
        var accent = color("Accent Red", [31,94,74,30]);
        var quiet = color("Quiet Taupe", [29,28,32,8]);
        var bodyFont = font("Source Han Serif SC	Regular", "Noto Serif CJK SC	Regular");
        var sansFont = font("Microsoft YaHei	Regular", "微软雅黑	Regular");

        var pTitle = paragraphStyle("P-TITLE", {appliedFont:bodyFont, pointSize:25, leading:31, fillColor:ink, justification:Justification.CENTER_ALIGN, tracking:220});
        var pSubtitle = paragraphStyle("P-SUBTITLE", {appliedFont:bodyFont, pointSize:8.5, leading:14, fillColor:quiet, justification:Justification.CENTER_ALIGN, tracking:80});
        var pAuthor = paragraphStyle("P-AUTHOR", {appliedFont:bodyFont, pointSize:9, leading:14, fillColor:ink, justification:Justification.CENTER_ALIGN, tracking:100});
        var pStudio = paragraphStyle("P-STUDIO", {appliedFont:sansFont, pointSize:7, leading:10, fillColor:quiet, justification:Justification.CENTER_ALIGN, tracking:80});
        var pTocHeading = paragraphStyle("P-TOC-HEADING", {appliedFont:bodyFont, pointSize:18, leading:24, fillColor:ink, tracking:160});
        var pTocEntry = paragraphStyle("P-TOC-ENTRY", {appliedFont:bodyFont, pointSize:9, leading:14, fillColor:ink, tracking:20});
        var pTocLevel = paragraphStyle("P-TOC-LEVEL", {appliedFont:sansFont, pointSize:6.8, leading:10, fillColor:accent, tracking:100});
        var pChapterNo = paragraphStyle("P-CH-NO", {appliedFont:bodyFont, pointSize:8, leading:12, fillColor:accent, tracking:280});
        var pChapterTitle = paragraphStyle("P-CH-TTL", {appliedFont:bodyFont, pointSize:21, leading:27, fillColor:ink, tracking:160, keepAllLinesTogether:true});
        var pBody = paragraphStyle("P-BD-01", {appliedFont:bodyFont, pointSize:10.5, leading:17.5, fillColor:ink, justification:Justification.LEFT_JUSTIFIED, firstLineIndent:21, spaceBefore:0, spaceAfter:0, keepFirstLines:2, keepLastLines:2});
        var pBodyFirst = paragraphStyle("P-BD-FIRST", {appliedFont:bodyFont, pointSize:10.5, leading:17.5, fillColor:ink, justification:Justification.LEFT_JUSTIFIED, firstLineIndent:0, spaceBefore:0, spaceAfter:0, keepFirstLines:2, keepLastLines:2});
        var pHeader = paragraphStyle("P-RUNNING-HEAD", {appliedFont:bodyFont, pointSize:7.5, leading:10, fillColor:quiet, tracking:90});
        var pFolio = paragraphStyle("P-FOLIO", {appliedFont:sansFont, pointSize:7.5, leading:10, fillColor:quiet, tracking:40});

        var parentA = doc.masterSpreads.item(0); parentA.namePrefix = "A"; parentA.baseName = "Body"; parentA.insertLabel("page-family", "A-Body");
        var parentB = parent("B", "Blank"); // B-Blank
        var parentC = parent("C", "FrontMatter"); // C-FrontMatter
        var parentD = parent("D", "TOC"); // D-TOC
        var parentE = parent("E", "Chapter"); // E-Chapter
        var parentF = parent("F", "BodyFirst"); // F-BodyFirst

        for (var pageIndex = 0; pageIndex < doc.pages.length; pageIndex++) {
            if (pageIndex !== 0 && pageIndex !== 13) paperBackground(doc.pages.item(pageIndex), paper, backgroundLayer);
        }

        var front = doc.pages.item(0); front.appliedMaster = parentB; front.insertLabel("page-role", "front-cover");
        placeFullPage(front, "D:/book-production-skills-v1/projects/lost-human-world-cover/indesign/editable-v001/assets/front-cover-300ppi.png", backgroundLayer);

        var insideFront = doc.pages.item(1); insideFront.appliedMaster = parentB; insideFront.insertLabel("page-role", "blank-verso");

        var titlePage = doc.pages.item(2); titlePage.appliedMaster = parentC; titlePage.insertLabel("page-role", "title-page");
        var titleLine = titlePage.graphicLines.add({strokeColor:accent, strokeWeight:0.45}); titleLine.itemLayer = textLayer; titleLine.paths.item(0).entirePath = spreadPoints(titlePage,[[39,18],[39,75]]);
        var titleLine2 = titlePage.graphicLines.add({strokeColor:accent, strokeWeight:0.45}); titleLine2.itemLayer = textLayer; titleLine2.paths.item(0).entirePath = spreadPoints(titlePage,[[39,132],[39,192]]);
        verticalFrame(titlePage, [42,56,134,79], "失落人间", pTitle, textLayer);
        verticalFrame(titlePage, [55,84,128,94], "在所有归途之外", pSubtitle, textLayer);
        verticalFrame(titlePage, [72,102,126,112], "早睡的猫", pAuthor, textLayer);
        textFrame(titlePage, [182,50,190,95], "纸船工作室", pStudio, textLayer);

        var tocEntries = [{"entry_id": "TOC-TEST-000", "level": "序章", "title": "灯灭以前", "page": 1}, {"entry_id": "TOC-TEST-001", "level": "第一章", "title": "车窗里的故乡", "page": 6}, {"entry_id": "TOC-TEST-002", "level": "第二章", "title": "白昼的缝隙", "page": 24}, {"entry_id": "TOC-TEST-003", "level": "第三章", "title": "没有回声的房间", "page": 42}, {"entry_id": "TOC-TEST-004", "level": "第四章", "title": "雨停在城外", "page": 62}, {"entry_id": "TOC-TEST-005", "level": "第五章", "title": "旧门向里开", "page": 84}, {"entry_id": "TOC-TEST-006", "level": "第六章", "title": "乡音之外", "page": 106}, {"entry_id": "TOC-TEST-007", "level": "第七章", "title": "临时住址", "page": 130}, {"entry_id": "TOC-TEST-008", "level": "第八章", "title": "人间无岸", "page": 154}];
        for (var tocPageOffset = 0; tocPageOffset < 2; tocPageOffset++) {
            var tocPage = doc.pages.item(3 + tocPageOffset); tocPage.appliedMaster = parentD; tocPage.insertLabel("page-role", tocPageOffset === 0 ? "toc-verso" : "toc-recto");
            var axis = tocPage.graphicLines.add({strokeColor:accent, strokeWeight:0.5}); axis.itemLayer = textLayer; axis.paths.item(0).entirePath = spreadPoints(tocPage,[[28,24],[28,186]]);
            if (tocPageOffset === 0) textFrame(tocPage, [28,38,46,116], "目录", pTocHeading, textLayer);
            var start = tocPageOffset === 0 ? 0 : 5;
            var end = tocPageOffset === 0 ? 5 : tocEntries.length;
            for (var tocIndex = start; tocIndex < end; tocIndex++) {
                var local = tocIndex - start;
                var y = 60 + local * 22;
                textFrame(tocPage, [y,38,y+7,57], tocEntries[tocIndex].level, pTocLevel, textLayer);
                textFrame(tocPage, [y+6,38,y+16,112], tocEntries[tocIndex].title, pTocEntry, textLayer);
                var pageNo = textFrame(tocPage, [y+6,114,y+16,127], String(tocEntries[tocIndex].page), pTocEntry, textLayer);
                pageNo.paragraphs.item(0).justification = Justification.RIGHT_ALIGN;
            }
        }

        var chapterLeft = doc.pages.item(5); chapterLeft.appliedMaster = parentE; chapterLeft.insertLabel("page-role", "chapter-opener-left");
        var boundary = chapterLeft.graphicLines.add({strokeColor:accent, strokeWeight:0.55}); boundary.itemLayer = textLayer; boundary.paths.item(0).entirePath = spreadPoints(chapterLeft,[[8,38],[28,65],[17,112],[35,171],[24,195]]);
        var chapterRight = doc.pages.item(6); chapterRight.appliedMaster = parentE; chapterRight.insertLabel("page-role", "chapter-opener-right");
        verticalFrame(chapterRight, [32,92,72,102], "第一章", pChapterNo, textLayer);
        verticalFrame(chapterRight, [58,105,150,133], "车窗里的故乡", pChapterTitle, textLayer);

        var bodyParagraphs = ["车开出城的时候，雨还没有落下来。", "高架两旁的灯一盏接一盏退到车后，玻璃上映着车厢里的脸。那些脸被窗外的光切开，亮一阵，暗一阵，像在很远的水里浮着。他坐在靠窗的位置，把额头抵在玻璃上。冷气从窗缝里渗进来，贴着眉骨，过一会儿便留下了一小块模糊的白雾。", "手机还停在那条消息上。", "你爸走了。回来吧。", "句号很小，缩在屏幕右下角。他看了很多遍，始终没有往上翻。发信人是一个没有存进通讯录的号码，但他认得末尾四位。小时候家里装过一部座机，后来拆了，二叔把那四位留在了自己的手机号码里，说这样好记。很多年过去，他记不得二叔现在住哪条街，倒还记得那部座机摆在堂屋木柜上，下面压着一本缺了封皮的电话簿。", "车厢里有人拆开塑料袋，茶叶蛋的气味散出来。司机把广播调得很低，一个女人在说南方将有大范围降温。邻座没有人，座椅靠背仍保持着笔直的角度。上车时他问过乘务员，旁边是否有人。乘务员看了一眼票，说有，在下一站上。他便把背包抱到腿上。车经过下一站时没有停，后来也没人来。", "空座位随着车身轻轻晃动，像有人刚刚起身。", "他锁了手机，又很快按亮。屏幕上方显示十一点十七分。消息是傍晚六点四十三分发来的，那时他还在公司。办公室的灯全部亮着，窗外已经黑了。打印机卡住一张纸，同事隔着几排桌子叫他帮忙。他把那张纸抽出来，边缘留下一道黑色的墨痕。等他回到座位，手机屏幕已经灭了。", "他没有立刻请假。先回复了一封邮件，保存桌面上的表格，又把明天要交的文件发给同事。主管问他需要几天，他说不知道。主管把“不知道”重复了一遍，像确认一个项目期限。他于是说三天，也可能五天。主管点点头，提醒他在系统里补流程。", "离开办公楼时，保安照常让他刷卡。绿色的灯亮了一下，玻璃门向两边打开。他走出去，门又在身后合上。那一刻他想起父亲以前锁院门的声音。两扇铁门并不严丝合缝，每到冬天，风从中间挤进来，门闩便一夜一夜地响。父亲会披着棉袄出去，在门缝里塞一截旧胶皮。", "他已经想不起那截胶皮是什么颜色。", "高速公路在黑暗里延伸。路旁偶尔出现一片厂房，屋顶的红灯同时闪烁。更远处是尚未封顶的楼，窗口没有光，只在轮廓上挂着几排绿色的安全网。车从它们中间穿过去，没有减速。", "前排的孩子醒了一次，问母亲到了没有。母亲说快了，又说睡吧。孩子把脸埋回外套里。过了几分钟，他再次问到了没有，声音已经含混。母亲仍说快了。", "他小时候也问过同样的话。那时去县医院看母亲，父亲骑一辆旧摩托，他坐在后座，手抓着父亲腰间的衣服。路还没有修好，车轮碾过碎石，每一下都从座位传到牙齿。他隔一段路便问到了没有。父亲总说前面就是。前面有时是一座桥，有时是一排杨树，有时什么也没有。", "母亲住院的那几年，他学会了不再问。后来她回家，药瓶在窗台上排成一列，早晚各有不同的数量。她把吃空的瓶子洗净，用来装针线、纽扣和晒干的花椒。她去世后，父亲没有扔掉那些瓶子。前年他回去，窗台已经积了灰，瓶口却仍用白布封着。", "那次他只住了一晚。", "父亲问城里的房租贵不贵，他说还好；问工作累不累，他说还好；问什么时候再回来，他说有空。回答都是现成的，像商店里找回的零钱，大小合适，却不属于任何一件具体的东西。第二天清早，父亲在灶房煮面，锅盖被蒸汽顶得发响。他说赶时间，没有吃完。父亲送他到巷口，手里还拿着擦锅沿的布。", "后来父亲给他打过几次电话。", "有一次他正在开会，按掉了。一次是在地铁里，信号断断续续，他说晚点再打。还有一次是凌晨，手机只响了两声便停下。他第二天看到通话记录，想也许是父亲按错了。那个号码之后再没有打来。", "他点开通讯录，找到“家”。号码仍在，归属地显示本省。他盯着绿色的拨号标志，手指悬在上面。窗外正好驶过一辆货车，强光从玻璃上扫过，他在屏幕里看见自己的眼睛。等光过去，拨号标志还在那里。", "他没有按下去。", "凌晨一点，车停进服务区。大多数人没有下车。司机开了车门，冷空气涌进来，带着湿土和汽油的味道。他去洗手间洗了脸，又在便利店买了一瓶水。收银台旁摆着切开的橙子，外面蒙着保鲜膜，颜色过分鲜亮。他想起父亲近几年牙不好，吃苹果时总要切成薄片。这个念头没有带来什么，只让他在付款后多拿了一根吸管。", "回到车上，邻座依旧空着。座位上不知什么时候落了一张小票。他捡起来看，是另一座城市的超市，日期在三个月前。上面只有一袋米、一盒止痛片和一把青菜。他把小票折了一次，放进前方椅背的网袋，又觉得不妥，取出来攥在手里。", "车重新上路，雨终于落了下来。", "雨点先是零星几颗，很快连成细密的斜线。车窗里的倒影被冲散，五官浮在道路和护栏之间。他抬手擦了一下玻璃，手指只触到内侧，外面的水痕仍沿着他的脸往下流。", "司机关掉广播，车厢安静下来。有人打鼾，有人的手机在黑暗中亮着，短视频的声音刚冒出来便被按掉。头顶行李架随着路面颤动，拉链和塑料扣偶尔碰出轻响。他突然记起出门太急，没有带黑色衣服。箱子里只有两件衬衫、一条旧长裤和公司的深蓝色外套。那件外套胸口绣着很小的标志，远看像一扇关着的门。", "他想，到了以后可以买一件。", "至于到哪里买，他没有想下去。", "父亲住的老屋去年被划进了改造范围。墙上喷过一个红色的编号，巷子里有几户已经搬空。父亲在电话里说过一次，说补偿的事还没定，让他别管。他确实没有管。后来二叔提起，父亲已经搬到镇上的临时房，行李不多，锅碗仍留在老屋。他不知道父亲最后是从哪一间屋里被送走的，也不知道灵堂设在哪里。", "他重新打开那条消息，在输入框里打：到哪里？", "三个字停了一会儿。他又删掉，改成：我在车上。", "发送成功后，屏幕上出现一个小小的圆圈。没有回复。", "车驶过一段隧道。玻璃骤然变成镜子，他清楚地看见自己抱着背包，旁边空着一个位置。隧道顶灯从身后追来，一盏一盏越过他的肩。他忽然觉得那空位并非留给某个人，而是从很早以前就在那里，只是过去总被行李、衣服或一个临时上车的陌生人遮住。", "隧道结束，镜子又变回窗。", "雨小了。远处出现低矮的山影，黑得比夜色更实。公路旁的指示牌开始出现熟悉的字：河口、东岭、白石。那些名字在他的童年里不是方向，而是一个个具体的地方。河口有夏天涨水的旧桥，东岭有一座废弃砖窑，白石逢五赶集，卖竹筐的人坐在路边。他多年没有去过，却仍知道它们之间隔几站车程。", "手机震了一下。", "二叔回复：先到镇医院这边。", "过了半分钟，又发来一句：老屋钥匙找不到了。", "他看着第二句话，直到屏幕暗下去。车窗外，一排新装的路灯从田野中穿过，灯下什么也没有，只有被雨压低的草。每一盏灯都照亮一小圈地面，各自明亮，各自隔着相同的黑暗。", "天快亮时，乘务员从前面走过来，小声提醒还有四十分钟到站。有人开始整理行李，塑料袋重新发出窸窣声。前排的孩子醒了，趴在窗口看外面。他问母亲这是哪里。母亲说已经到家了。", "车正在经过县界。蓝色路牌上印着县名，下面是一句新换的宣传语。他只认出县名。再往前，废弃的收费站还在，顶棚已经褪成灰白；路边那家修车铺换了招牌，院里仍停着一辆没有轮胎的货车；更远处的水塔被清晨的雾遮住一半，像一件没有收拾完的旧家具。", "这些东西没有等他，也没有责怪他。它们只是依次出现，然后退到车后。", "乘务员问他在哪一站下。", "他报出镇医院，又在对方准备往前走时叫住她，问能不能改到老车站。乘务员说都可以，两站只差十分钟，让他想好再说。", "他点点头。", "前方岔路口的指示牌越来越近。左边通往镇医院，右边通往老车站，再往前是老屋所在的村子。三个地名他都认得，甚至知道每条路在雨后哪里会积水，哪一段曾种过两排梧桐。", "手机握在手里，没有再响。", "车在岔路前减速。司机拨动转向灯，规律的嗒嗒声传遍安静的车厢。乘务员站在过道尽头，等着他的回答。", "他望着窗外，没有立刻开口。"];
        var bodyFrames = [];
        for (var bodyIndex = 0; bodyIndex < 6; bodyIndex++) {
            var bodyPage = doc.pages.item(7 + bodyIndex);
            bodyPage.appliedMaster = bodyIndex === 0 ? parentF : parentA;
            bodyPage.insertLabel("page-role", bodyIndex === 0 ? "body-first" : "body-standard");
            bodyFrames.push(textFrame(bodyPage, outerBounds(bodyPage, bodyIndex === 0 ? 54 : 26, 24), "", pBody, textLayer));
            addFolio(bodyPage, 6 + bodyIndex, pFolio, navigationLayer);
            if (bodyIndex > 0) addRunningHead(bodyPage, bodyPage.side === PageSideOptions.LEFT_HAND ? "失落人间" : "车窗里的故乡", pHeader, navigationLayer);
        }
        for (var threadIndex = 0; threadIndex < bodyFrames.length - 1; threadIndex++) bodyFrames[threadIndex].nextTextFrame = bodyFrames[threadIndex + 1];
        var story = bodyFrames[0].parentStory;
        story.contents = bodyParagraphs.join("\r");
        story.paragraphs.everyItem().appliedParagraphStyle = pBody;
        story.paragraphs.item(0).appliedParagraphStyle = pBodyFirst;

        var back = doc.pages.item(13); back.appliedMaster = parentB; back.insertLabel("page-role", "back-cover");
        placeFullPage(back, "D:/book-production-skills-v1/projects/lost-human-world-cover/indesign/editable-v001/assets/back-cover-300ppi.png", backgroundLayer);

        var overset = 0;
        for (var textIndex = 0; textIndex < doc.textFrames.length; textIndex++) if (doc.textFrames.item(textIndex).overflows) overset++;
        var missingLinks = 0;
        var lowResolution = 0;
        for (var linkIndex = 0; linkIndex < doc.links.length; linkIndex++) {
            if (doc.links.item(linkIndex).status === LinkStatus.LINK_MISSING) missingLinks++;
            try {
                var ppi = doc.links.item(linkIndex).parent.parent.effectivePpi;
                if (ppi.length > 1 && (ppi[0] < 295 || ppi[1] < 295)) lowResolution++;
            } catch (ppiError) {}
        }
        if (overset > 0) throw new Error("Overset text frames: " + overset);
        if (missingLinks > 0) throw new Error("Missing links: " + missingLinks);

        doc.save(inddFile);
        doc.exportFile(ExportFormat.INDESIGN_MARKUP, idmlFile, false);
        app.pdfExportPreferences.exportReaderSpreads = false;
        app.pdfExportPreferences.pageRange = PageRange.ALL_PAGES;
        app.pdfExportPreferences.useDocumentBleedWithPDF = false;
        app.pdfExportPreferences.viewPDF = false;
        doc.exportFile(ExportFormat.PDF_TYPE, pdfFile, false);
        if (doc.layoutWindows.length > 0) { doc.layoutWindows.item(0).activePage = doc.pages.item(7); doc.layoutWindows.item(0).zoomPercentage = 105; }
        app.activate();
        return '{"status":"built","application":"' + app.name + '","version":"' + app.version + '","pages":' + doc.pages.length + ',"links":' + doc.links.length + ',"textFrames":' + doc.textFrames.length + ',"paragraphStyles":' + doc.paragraphStyles.length + ',"parentSpreads":' + doc.masterSpreads.length + ',"overset":' + overset + ',"missingLinks":' + missingLinks + ',"lowResolutionLinks":' + lowResolution + '}';
    } catch (error) {
        if (doc !== null && !doc.saved) { try { doc.close(SaveOptions.NO); } catch (closeError) {} }
        throw error;
    } finally {
        app.scriptPreferences.userInteractionLevel = previousInteraction;
    }
})();
