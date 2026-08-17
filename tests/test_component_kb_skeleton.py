from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ai.book_component_kb.build import DERIVED_NAMES
from ai.book_component_kb.paths import sha256_file
from ai.book_component_kb.validate import validate_library
from ai.contracts import validate_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LIBRARY_ROOT = PROJECT_ROOT / "knowledge" / "book-component-libraries"
REGISTRY_PATH = LIBRARY_ROOT / "source-registry.json"
COVER_ROOT = LIBRARY_ROOT / "cover"
PROTOCOL_PATH = PROJECT_ROOT / "docs" / "封面知识库采集与使用说明.md"
PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
BUILD_CLI = PROJECT_ROOT / "scripts" / "book_component_kb" / "build_library.py"
VALIDATE_CLI = PROJECT_ROOT / "scripts" / "book_component_kb" / "validate_library.py"
BUILDER_OUTPUTS = (*DERIVED_NAMES, "manifest.json")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def output_bytes(root: Path) -> dict[str, bytes]:
    return {relative: (root / relative).read_bytes() for relative in BUILDER_OUTPUTS}


class ComponentKnowledgeBaseSkeletonTests(unittest.TestCase):
    def test_registry_and_human_protocol_are_present(self) -> None:
        registry = read_json(REGISTRY_PATH)

        self.assertEqual([], validate_data(registry, "book-component-source-registry"))
        self.assertEqual("1.0", registry["schema_version"])
        self.assertEqual("accumulation", registry["source_mode"])
        self.assertTrue(PROTOCOL_PATH.is_file())
        self.assertGreater(PROTOCOL_PATH.stat().st_size, 0)

    def test_accumulating_inputs_have_exact_closure_and_builder_owned_derivatives(self) -> None:
        record_paths = sorted((COVER_ROOT / "records").glob("*.json"))
        asset_paths = sorted((COVER_ROOT / "assets").glob("*"))
        self.assertEqual(
            {
                Path(read_json(path)["asset"]["relative_path"]).name
                for path in record_paths
            },
            {path.name for path in asset_paths},
        )
        self.assertEqual(
            {relative for relative in BUILDER_OUTPUTS if relative.startswith("categories/")},
            {
                path.relative_to(COVER_ROOT).as_posix()
                for path in (COVER_ROOT / "categories").iterdir()
            },
        )
        self.assertEqual(
            {
                *BUILDER_OUTPUTS,
                *(f"records/{path.name}" for path in record_paths),
                *(f"assets/{path.name}" for path in asset_paths),
            },
            {
                path.relative_to(COVER_ROOT).as_posix()
                for path in COVER_ROOT.rglob("*")
                if path.is_file()
            },
        )

    def test_real_builder_and_validator_cli_reproduce_current_accumulation_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temp_library = Path(temporary) / "book-component-libraries"
            temp_cover = temp_library / "cover"
            temp_cover.mkdir(parents=True)
            shutil.copytree(COVER_ROOT / "records", temp_cover / "records")
            shutil.copytree(COVER_ROOT / "assets", temp_cover / "assets")
            temp_registry = temp_library / "source-registry.json"
            shutil.copyfile(REGISTRY_PATH, temp_registry)
            production_manifest = read_json(COVER_ROOT / "manifest.json")
            expected_count = production_manifest["valid_record_count"]
            expected_status = "available" if expected_count >= 50 else "building"

            built = subprocess.run(
                [
                    str(PYTHON),
                    str(BUILD_CLI),
                    "--component-root",
                    str(temp_cover),
                    "--registry",
                    str(temp_registry),
                ],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, built.returncode, built.stderr)
            build_report = json.loads(built.stdout)
            self.assertEqual(expected_status, build_report["status"])
            self.assertEqual(expected_count, build_report["valid_record_count"])
            self.assertEqual(0, build_report["invalid_record_count"])

            first = output_bytes(temp_cover)
            rebuilt = subprocess.run(
                [
                    str(PYTHON),
                    str(BUILD_CLI),
                    "--component-root",
                    str(temp_cover),
                    "--registry",
                    str(temp_registry),
                ],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, rebuilt.returncode, rebuilt.stderr)
            self.assertEqual(first, output_bytes(temp_cover))
            self.assertEqual(output_bytes(COVER_ROOT), output_bytes(temp_cover))

            checked = subprocess.run(
                [
                    str(PYTHON),
                    str(VALIDATE_CLI),
                    "--component-root",
                    str(temp_cover),
                    "--registry",
                    str(temp_registry),
                    "--required-count",
                    "50",
                ],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0 if expected_status == "available" else 2, checked.returncode, checked.stderr)
            validation = json.loads(checked.stdout)
            self.assertTrue(validation["valid"])
            self.assertEqual(expected_status, validation["status"])
            self.assertEqual(expected_count, validation["record_count"])

    def test_production_accumulation_validates_read_only_at_its_current_count(self) -> None:
        before = {
            path.relative_to(LIBRARY_ROOT).as_posix(): sha256_file(path)
            for path in LIBRARY_ROOT.rglob("*")
            if path.is_file()
        }

        report = validate_library(COVER_ROOT, REGISTRY_PATH, required_count=50)

        after = {
            path.relative_to(LIBRARY_ROOT).as_posix(): sha256_file(path)
            for path in LIBRARY_ROOT.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)
        self.assertTrue(report["valid"])
        expected_count = read_json(COVER_ROOT / "manifest.json")["valid_record_count"]
        expected_status = "available" if expected_count >= 50 else "building"
        self.assertEqual(expected_status, report["status"])
        self.assertEqual(expected_count, report["record_count"])
        self.assertEqual(
            {
                "records": len(list((COVER_ROOT / "records").iterdir())),
                "assets": len(list((COVER_ROOT / "assets").iterdir())),
                "books": len(read_json(COVER_ROOT / "catalog.json")["entries"]),
                "categories": 4,
                "derived": 6,
            },
            report["counts"],
        )

    def test_task_12_reviewed_evidence_identity_and_structure_remain_bound(self) -> None:
        expected_year_sources = {
            "COV-CN-0023": "https://image.chinawriter.com.cn/n1/2025/0414/c404072-40459309.html",
            "COV-CN-0024": "https://www.sanmin.com.tw/product/index/013464043",
            "COV-CN-0025": "https://www.nationalreading.gov.cn/hstj/rwsk/202405/t20240521_849121.html",
            "COV-CN-0027": "https://www.sanmin.com.tw/product/index/007175651",
            "COV-CN-0028": "https://search.worldcat.org/title/Allusions-in-the-subway-stations%27-name-of-Beijing/oclc/1243234501",
            "COV-CN-0029": "https://www.nju.edu.cn/info/3191/206341.htm",
            "COV-CN-0030": "https://www.sanmin.com.tw/product/index/010129803",
        }
        registry = {
            item["source_registry_id"]: item
            for item in read_json(REGISTRY_PATH)["sources"]
        }
        records = {
            record_id: read_json(COVER_ROOT / "records" / f"{record_id}.json")
            for record_id in expected_year_sources
        }

        for record_id, expected_url in expected_year_sources.items():
            with self.subTest(record_id=record_id):
                record = records[record_id]
                source = record["source"]
                registry_source = registry[source["source_registry_id"]]
                self.assertEqual(expected_url, source["publication_year_source_url"])
                self.assertEqual(expected_url, registry_source["publication_year_source_url"])
                self.assertEqual(source["publication_year"], record["identity"]["publication_year"])

        self.assertEqual("陈从周", records["COV-CN-0025"]["identity"]["author"])
        self.assertEqual("江苏凤凰文艺出版社", records["COV-CN-0025"]["identity"]["publisher"])
        self.assertEqual("孙江（主编）", records["COV-CN-0029"]["identity"]["author"])

    def test_task_12_source_confirmed_packaging_and_five_book_system_preserve_front_profiles(self) -> None:
        records = {
            record_id: read_json(COVER_ROOT / "records" / f"{record_id}.json")
            for record_id in ("COV-CN-0024", "COV-CN-0026", "COV-CN-0030")
        }
        for record in records.values():
            self.assertEqual("front", record["component_profile"]["cover_scope"])
        record_text = {
            record_id: json.dumps(records[record_id], ensure_ascii=False)
            for record_id in ("COV-CN-0024", "COV-CN-0026", "COV-CN-0030")
        }
        self.assertIn("木盒", record_text["COV-CN-0024"])
        for marker in ("五册", "连接", "分开", "纸张", "色彩"):
            self.assertIn(marker, record_text["COV-CN-0026"])
        self.assertNotIn("不把并置封面推断成多册", record_text["COV-CN-0026"])
        self.assertIn("外盒", record_text["COV-CN-0030"])

    def test_task_13_exact_case_year_identity_and_asset_bindings_remain_fixed(self) -> None:
        expected = {
            "0031": ("姑苏繁华录——苏州桃花坞木版年画特展作品集", "张晴", "上海人民美术出版社", "刘晓翔、郭晴婷、张宇", 2017, "328", "https://www.sanmin.com.tw/product/index/006696287", 600, 400, "572d4abdb59ee327deaeecd3c0b6a090b6f3f0d71d5724dfeb43eb2173e664af"),
            "0032": ("敦煌", "柴剑虹、刘进宝", "朝华出版社", "雅昌设计中心·田之友", 2018, "365", "https://www.sanmin.com.tw/product/index/007011776", 600, 400, "5d0e8407941b9607a89b26e849cb7cd181cedd96ba64954c91ff1f8d2439b101"),
            "0033": ("中国园林：诗意审美与四季", "(英)彼得·内斯特鲁克", "中国民族摄影艺术出版社", "郭萌", 2019, "394", "https://www.books.com.tw/products/CN11714154", 900, 600, "797721e1e0a2a60303352d8bd169b847f17eaac76a2e059ac59b93da9f0de6b6"),
            "0034": ("猴子捞月", "张俊杰", "明天出版社", "张俊杰", 2020, "415", "https://www.ccgp-neimenggu.gov.cn/gpx-bid-file/150501/gpx-tender/2022/9/27/402881dd82f475a001837dd994c704ec.pdf?accessCode=6ee03dd5dfaa580f5676714376d8dec5", 833, 556, "e4fae1a95f7badb3249262f726e566087a48b02de3cf451298a2f035d3f95a89"),
            "0035": ("夏天的故事", "魏捷（文）、李小光（图）", "新世界出版社", "陈萌、任伟嘉", 2021, "420", "https://topics.gmw.cn/2022-04/23/content_35674383.htm", 600, 400, "c7ae60fe9470427cffaf38471d354adb3d2a46f4545a8b3f3e7c5b1ec490c786"),
            "0036": ("乡村与木刻", "刘庆元、左靖", "上海人民美术出版社", "黄扬设计工作室", 2022, "468", "https://books.google.com/books/about/%E4%B9%A1%E6%9D%91%E4%B8%8E%E6%9C%A8%E5%88%BB.html?id=dc8T0AEACAAJ", 1875, 1250, "8984f03fd4ae9ffcb54afd7fb2df6e696e03f3aa13db4a6f07e95fdf3743d053"),
            "0037": ("吸呼（全3册）", "胡一凡", "海豚出版社", "胡一凡、戚翔宇", 2023, "501", "https://www.sanmin.com.tw/product/index/012700139", 1875, 1250, "f0ab16941a48bc92b43f7d293565e1c6bb8aec87a6f81b4860bc0142b3ef5e84"),
            "0038": ("千古霓裳：汉服穿着文化", "汉服北京", "化学工业出版社", "尹琳琳", 2023, "499", "https://www.cbbr.com.cn/contents/560/92285.html", 1875, 1250, "89a11096c62f8c46313767bb28d9b1187a03738894ccfcc8d63a610858106dda"),
            "0039": ("何物", "何明", "江苏凤凰美术出版社", "清门引", 2024, "506", "https://www.sanmin.com.tw/product/index/014362378", 1500, 1000, "ce0e35e7bdc4fb6907129bf8546169c2da5374e08dc16a835e67e4e78c99b56f"),
            "0040": ("我不是好惹的", "丁成", "湖南美术出版社", "张鑫", 2025, "532", "https://book.douban.com/subject/37816782/", 1063, 800, "9e243c0728391ece8cdc8fce61a6012a3073370d33941358c46cd29cb448e9fe"),
        }
        registry = {
            item["source_registry_id"]: item
            for item in read_json(REGISTRY_PATH)["sources"]
        }

        for number, values in expected.items():
            with self.subTest(number=number):
                title, author, publisher, designer, year, case_id, year_url, width, height, digest = values
                record_id = f"COV-CN-{number}"
                source_id = f"SRC-CN-{number}"
                record_path = COVER_ROOT / "records" / f"{record_id}.json"
                self.assertTrue(record_path.is_file(), record_path)
                if not record_path.is_file():
                    continue
                self.assertIn(source_id, registry)
                if source_id not in registry:
                    continue
                record = read_json(record_path)
                source = record["source"]
                identity = record["identity"]
                asset = record["asset"]
                case_url = f"https://beautyofbooks.cn/bookdetail?id={case_id}"
                self.assertEqual(
                    (title, author, publisher, designer, year),
                    (identity["book_title"], identity["author"], identity["publisher"], identity["designer"], identity["publication_year"]),
                )
                self.assertEqual((case_url, year_url), (source["source_url"], source["publication_year_source_url"]))
                self.assertEqual("BeautyOfBooks", source["platform"])
                self.assertEqual(source_id, source["source_registry_id"])
                self.assertEqual(source, {
                    key: registry[source_id][key]
                    for key in ("source_registry_id", "source_url", "platform", "collected_at", "publication_year", "publication_year_source_url")
                })
                self.assertEqual(("image/jpeg", width, height, digest), (asset["mime_type"], asset["width"], asset["height"], asset["sha256"]))
                asset_path = LIBRARY_ROOT / asset["relative_path"]
                self.assertTrue(asset_path.is_file(), asset_path)
                if asset_path.is_file():
                    self.assertEqual(digest, sha256_file(asset_path))

    def test_task_13_extends_the_production_prefix_with_unique_separated_sources(self) -> None:
        records = [read_json(path) for path in sorted((COVER_ROOT / "records").glob("COV-CN-*.json"))]
        registry = read_json(REGISTRY_PATH)["sources"]

        self.assertEqual([f"COV-CN-{number:04d}" for number in range(1, 41)], [record["record_id"] for record in records[:40]])
        self.assertEqual([f"SRC-CN-{number:04d}" for number in range(1, 41)], [source["source_registry_id"] for source in registry[:40]])
        self.assertEqual(40, len({record["identity"]["book_case_id"] for record in records[:40]}))
        self.assertEqual(40, len({record["asset"]["sha256"] for record in records[:40]}))
        for record in records[30:40]:
            self.assertNotEqual(record["source"]["source_url"], record["source"]["publication_year_source_url"])
            self.assertEqual("accumulation", record["lifecycle"]["status"])

    def test_task_13_reviewed_dunhuang_scope_remains_a_dust_jacket(self) -> None:
        record = read_json(COVER_ROOT / "records" / "COV-CN-0032.json")

        self.assertEqual("dust-jacket", record["component_profile"]["cover_scope"])

    def test_task_13_reviewed_hanfu_year_evidence_remains_replayable(self) -> None:
        record = read_json(COVER_ROOT / "records" / "COV-CN-0038.json")
        registry = {
            item["source_registry_id"]: item
            for item in read_json(REGISTRY_PATH)["sources"]
        }
        reviewed_year_url = "https://www.cbbr.com.cn/contents/560/92285.html"

        self.assertEqual(reviewed_year_url, record["source"]["publication_year_source_url"])
        self.assertEqual(reviewed_year_url, registry["SRC-CN-0038"]["publication_year_source_url"])

    def test_task_13_reviewed_hewu_designer_credit_remains_exact(self) -> None:
        record = read_json(COVER_ROOT / "records" / "COV-CN-0039.json")

        self.assertEqual("清门引", record["identity"]["designer"])

    def test_task_14_exact_diversity_case_bindings_remain_fixed(self) -> None:
        expected = {
            "0041": ("便形鸟", "朱赢椿", "广西师范大学出版社", "朱赢椿、皇甫珊珊", 2017, "361", "https://www.megbook.com.hk/mall/detail.jsp?proID=3090155", 600, 400, "23f09b742b0387fd9743e32afcca28d6c18d5b68a2c452f99eb2eee3f6e85aa1", ("front", "illustration", "centered", "vertical", "independent", "strong")),
            "0042": ("江苏老行当百业写真", "龚为摄影、潘文龙撰文", "江苏凤凰教育出版社", "周晨", 2018, "359", "https://www.abebooks.com/9787549973248/Jiangsu-Old-Hongyi-Photo-7549973245/plp", 600, 400, "9aaf4759099d877703cbebd2ee6f4e9997ff10ec76b0c54fa7918fe5bb3d58b3", ("front", "typography", "whitespace", "top", "not-visible", "weak")),
            "0043": ("芳华修远：第19届国际植物学大会植物艺术画展画集", "第十九届国际植物学大会组织委员会、深圳市中国科学院仙湖植物园", "江苏凤凰科学技术出版社", "KJ.DesignStudio", 2017, "325", "https://www.pspress.cn/book-detail-7325.html", 600, 400, "90dca2f2ae03d486a0d93c66c6d3f7eb3a2422cce53d0043cd536db3703f580b", ("front", "abstract", "centered", "vertical", "not-visible", "weak")),
            "0044": ("梦影红楼", "孙温、孙允谟绘", "上海古籍出版社", "潘焰荣", 2019, "389", "https://book.douban.com/subject/33379360/", 900, 600, "c902ee876df2aff7db3600ccedb4be6f81be440afce139d80d0637c5867d9d78", ("front", "abstract", "centered", "vertical", "independent", "weak")),
            "0045": ("天上掉下一头鲸", "西雨客文图", "天天出版社", "林蓓", 2019, "399", "https://ci.nii.ac.jp/ncid/BD14670867", 833, 556, "f3d8bfbc0cacf97374a0590a133dfad97f329701c850146874de72c54f735cab", ("front", "illustration", "asymmetric", "bottom", "not-visible", "strong")),
            "0046": ("肖全和妲妲的世界", "肖全", "中国青年出版社", "白凤鹍", 2020, "416", "https://search.megbook.com.hk/mall/detail.jsp?proID=3516071", 833, 556, "75a596f34f1610bb9c753861a1dc4d27d04c20cf286066ddda8d1f13f47ea87a", ("front", "typography", "asymmetric", "center", "not-visible", "medium")),
            "0047": ("一群马 满天星", "李刚", "中国摄影出版社", "樊响", 2022, "476", "https://aus.zxhsd.com/kgsm/ts/2022/09/26/5639030.shtml", 1875, 1250, "55ed9368d7c692d5193777d883c9920fd89edef1e2d35df0bf794bfad342ecb3", ("front", "mixed", "asymmetric", "vertical", "not-visible", "strong")),
            "0048": ("豆腐", "朱赢椿（主编）", "湖南文艺出版社", "朱赢椿、小羊、谢磊", 2022, "454", "https://tuan.bookschina.com/tuan/20754", 1875, 1250, "46d773b65a79791fc93c31cdd59286cd118bdc06b13c167c4f0456df9e71b009", ("front", "abstract", "centered", "center", "not-visible", "weak")),
            "0049": ("衣冠民尚：中国百年民族服饰与传统工艺", "上海浦东碧云美术馆编", "上海人民美术出版社", "张志奇工作室", 2023, "490", "https://www.sohu.com/a/753516208_121418230", 1875, 1250, "fed7289856d5ac4fc7a9b80c82a4b2fe0bbfa3a8bdf8b475c575bfae141297f9", ("full-wrap", "typography", "asymmetric", "top", "continuous", "strong")),
            "0050": ("东京行", "洪卫", "岭南美术出版社", "洪卫", 2025, "536", "https://tl.zxhsd.com/kgsm/ts/big5/2025/12/10/6738819.shtml", 1200, 800, "1e5fa8207706fe8fb8a710e34fd8272541d80bdcc41064b915dd8c55e1983de3", ("front", "typography", "whitespace", "top", "not-visible", "strong")),
        }
        registry = {
            item["source_registry_id"]: item
            for item in read_json(REGISTRY_PATH)["sources"]
        }

        for number, values in expected.items():
            with self.subTest(number=number):
                title, author, publisher, designer, year, case_id, year_url, width, height, digest, profile = values
                record_id = f"COV-CN-{number}"
                source_id = f"SRC-CN-{number}"
                record_path = COVER_ROOT / "records" / f"{record_id}.json"
                self.assertTrue(record_path.is_file(), record_path)
                if not record_path.is_file():
                    continue
                self.assertIn(source_id, registry)
                if source_id not in registry:
                    continue
                record = read_json(record_path)
                identity = record["identity"]
                source = record["source"]
                asset = record["asset"]
                self.assertEqual(
                    (title, author, publisher, designer, year),
                    (identity["book_title"], identity["author"], identity["publisher"], identity["designer"], identity["publication_year"]),
                )
                self.assertEqual(
                    (f"https://beautyofbooks.cn/bookdetail?id={case_id}", year_url),
                    (source["source_url"], source["publication_year_source_url"]),
                )
                self.assertEqual("BeautyOfBooks", source["platform"])
                self.assertEqual(source_id, source["source_registry_id"])
                self.assertEqual(source, {
                    key: registry[source_id][key]
                    for key in ("source_registry_id", "source_url", "platform", "collected_at", "publication_year", "publication_year_source_url")
                })
                self.assertEqual(("image/jpeg", width, height, digest), (asset["mime_type"], asset["width"], asset["height"], asset["sha256"]))
                self.assertEqual(profile, tuple(record["component_profile"][key] for key in ("cover_scope", "visual_strategy", "composition", "title_zone", "spine_relationship", "thumbnail_recognition")))
                asset_path = LIBRARY_ROOT / asset["relative_path"]
                self.assertTrue(asset_path.is_file(), asset_path)
                if asset_path.is_file():
                    self.assertEqual(digest, sha256_file(asset_path))

    def test_task_14_reviewed_visible_evidence_remains_bound_to_the_actual_title_faces(self) -> None:
        botanical = read_json(COVER_ROOT / "records" / "COV-CN-0043.json")
        xiao_quan = read_json(COVER_ROOT / "records" / "COV-CN-0046.json")

        self.assertEqual(
            [
                "浅灰米色孤立正封中央偏上仅一枚细线圆环，四周大面积低信息空场",
                "圆环内／近中轴为极微小低对比竖排题名；书脊不可见，不据纹理推断材料或工艺",
            ],
            [item["value"] for item in botanical["visual_decomposition"]["observations"]],
        )
        self.assertEqual(
            [
                "中央大号低对比轮廓“Xiao Quan & Ginda & Vanda”构成主标题",
                "左侧“01”和小号黑字构成次级信息列；绿色手写卡片、盒体与照片仅作上下文",
            ],
            [item["value"] for item in xiao_quan["visual_decomposition"]["observations"]],
        )

    def test_task_14_completes_the_available_unique_fifty_record_library(self) -> None:
        records = [read_json(path) for path in sorted((COVER_ROOT / "records").glob("COV-CN-*.json"))]
        registry = read_json(REGISTRY_PATH)["sources"]

        self.assertEqual([f"COV-CN-{number:04d}" for number in range(1, 51)], [record["record_id"] for record in records])
        self.assertEqual(
            [f"SRC-CN-{number:04d}" for number in range(1, 51)],
            [source["source_registry_id"] for source in registry[:50]],
        )
        self.assertEqual(50, len({record["identity"]["book_case_id"] for record in records}))
        self.assertEqual(50, len({record["asset"]["sha256"] for record in records}))
        self.assertNotIn(2026, {record["identity"]["publication_year"] for record in records})
        report = validate_library(COVER_ROOT, REGISTRY_PATH, required_count=50)
        self.assertEqual((True, "available", 50, []), (report["valid"], report["status"], report["record_count"], report["errors"]))


if __name__ == "__main__":
    unittest.main()
