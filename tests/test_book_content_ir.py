import hashlib
import re
import unittest

from ai.contracts import validate_data
from ai.indesign_templates.content_ir import parse_html, parse_markdown, source_digest


REJECTED_HTML_TAGS = ["script", "style", "iframe", "object", "embed"]
ALLOWED_TYPES = [
    "book-title",
    "chapter-title",
    "section-title",
    "body",
    "quote",
    "note",
    "date",
    "signature",
    "image",
    "caption",
]


class SourceDigestTests(unittest.TestCase):
    def test_digest_is_sha256_of_utf8_source(self):
        source = "第一章 春归\n<body>"
        self.assertEqual(
            hashlib.sha256(source.encode("utf-8")).hexdigest(), source_digest(source)
        )

    def test_digest_is_deterministic_and_64_lowercase_hex(self):
        source = "同一个源文本"
        first = source_digest(source)
        self.assertEqual(first, source_digest(source))
        self.assertRegex(first, r"^[0-9a-f]{64}$")

    def test_different_sources_produce_different_digests(self):
        self.assertNotEqual(source_digest("甲"), source_digest("乙"))


class ParseHtmlTests(unittest.TestCase):
    def test_semantic_blocks_ignore_css_coordinates(self):
        html = """
        <html><body>
          <h2 style="position:absolute;left:99px">第一章 春归</h2>
          <p class="body">第一段。</p>
          <blockquote>引文。</blockquote>
          <time datetime="2026-08-17">2026年8月17日</time>
        </body></html>
        """
        result = parse_html(html)
        self.assertEqual(
            ["chapter-title", "body", "quote", "date"],
            [block["type"] for block in result["blocks"]],
        )
        serialized = repr(result)
        self.assertNotIn("99px", serialized)
        self.assertNotIn("position", serialized)
        self.assertNotIn("left", serialized)

    def test_headings_and_inline_roles_map_to_blocks(self):
        html = """
        <h1>书名</h1>
        <h3>小节</h3>
        <aside>旁注</aside>
        <address>落款</address>
        <section>
          <p>段一</p>
        </section>
        """
        result = parse_html(html)
        self.assertEqual(
            ["book-title", "section-title", "note", "signature", "body"],
            [block["type"] for block in result["blocks"]],
        )

    def test_figure_is_passive_and_preserves_image_caption_order(self):
        html = """
        <figure>
          <img src="cover.tif" alt="封面底图">
          <figcaption>图 1 封面</figcaption>
        </figure>
        """
        result = parse_html(html)
        self.assertEqual(["image", "caption"], [block["type"] for block in result["blocks"]])
        self.assertEqual("封面底图", result["blocks"][0]["text"])
        self.assertEqual({"src": "cover.tif"}, result["blocks"][0]["attributes"])
        self.assertEqual("图 1 封面", result["blocks"][1]["text"])
        self.assertEqual({}, result["blocks"][1]["attributes"])

    def test_image_keeps_only_src_and_alt(self):
        html = (
            '<img src="photo.tif" alt="合影" width="1200" height="800" '
            'data-src="draft.jpg" onerror="alert(1)">'
        )
        result = parse_html(html)
        block = result["blocks"][0]
        self.assertEqual("image", block["type"])
        self.assertEqual("合影", block["text"])
        self.assertEqual({"src": "photo.tif"}, block["attributes"])
        self.assertNotIn("width", block["attributes"])
        self.assertNotIn("height", block["attributes"])
        self.assertNotIn("1200", repr(result))
        self.assertNotIn("onerror", repr(result))

    def test_image_without_alt_has_empty_text_and_src_only(self):
        result = parse_html('<img src="bg.tif">')
        self.assertEqual("", result["blocks"][0]["text"])
        self.assertEqual({"src": "bg.tif"}, result["blocks"][0]["attributes"])

    def test_each_active_tag_is_rejected_with_tag_name(self):
        for tag in REJECTED_HTML_TAGS:
            with self.subTest(tag=tag):
                with self.assertRaisesRegex(ValueError, tag):
                    parse_html(f"<{tag}>content</{tag}><p>正文</p>")

    def test_empty_active_tag_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "style"):
            parse_html("<style></style><p>正文</p>")

    def test_entities_and_whitespace_are_normalized(self):
        html = """
        <p>第一段  &amp;&nbsp;  第二段，换行
        续行。</p>
        """
        result = parse_html(html)
        self.assertEqual("第一段 & 第二段，换行 续行。", result["blocks"][0]["text"])

    def test_unknown_wrappers_do_not_create_blocks(self):
        html = """
        <div class="wrapper">
          <article>
            <h2>章</h2>
            <p>正文。</p>
          </article>
        </div>
        """
        result = parse_html(html)
        self.assertEqual(["chapter-title", "body"], [block["type"] for block in result["blocks"]])

    def test_plain_text_outside_known_elements_is_dropped(self):
        result = parse_html("<div>裸文本</div><p>正文。</p>")
        self.assertEqual(["body"], [block["type"] for block in result["blocks"]])
        self.assertEqual("正文。", result["blocks"][0]["text"])

    def test_empty_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "block|empty|short"):
            parse_html("")

    def test_source_without_any_block_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "block|empty|short"):
            parse_html("<div><span></span></div>")

    def test_empty_paragraph_does_not_create_a_block(self):
        result = parse_html("<p></p><p>非空段。</p>")
        self.assertEqual(["body"], [block["type"] for block in result["blocks"]])
        self.assertEqual("非空段。", result["blocks"][0]["text"])

    def test_unclosed_content_tag_still_emits_its_text(self):
        result = parse_html("<p>未闭合段落")
        self.assertEqual(["body"], [block["type"] for block in result["blocks"]])
        self.assertEqual("未闭合段落", result["blocks"][0]["text"])


class ParseMarkdownTests(unittest.TestCase):
    def test_headings_quote_and_body_keep_document_order(self):
        source = """# 书名

## 第一章 春归

正文第一段。

> 引文一段。

正文第二段。
"""
        result = parse_markdown(source)
        self.assertEqual(
            ["book-title", "chapter-title", "body", "quote", "body"],
            [block["type"] for block in result["blocks"]],
        )
        self.assertEqual("书名", result["blocks"][0]["text"])
        self.assertEqual("第一章 春归", result["blocks"][1]["text"])
        self.assertEqual("正文第一段。", result["blocks"][2]["text"])
        self.assertEqual("引文一段。", result["blocks"][3]["text"])
        self.assertEqual("正文第二段。", result["blocks"][4]["text"])

    def test_section_heading_and_multiline_paragraph_join(self):
        source = """### 小节

第一行
第二行。
"""
        result = parse_markdown(source)
        self.assertEqual(
            ["section-title", "body"], [block["type"] for block in result["blocks"]]
        )
        self.assertEqual("第一行 第二行。", result["blocks"][1]["text"])

    def test_multiline_quote_joins_into_one_quote(self):
        source = """> 第一引行
> 第二引行
"""
        result = parse_markdown(source)
        self.assertEqual(["quote"], [block["type"] for block in result["blocks"]])
        self.assertEqual("第一引行 第二引行", result["blocks"][0]["text"])

    def test_dates_signatures_and_images_are_never_guessed(self):
        source = """# 书
2026年8月17日

终于收到样书。
"""
        result = parse_markdown(source)
        self.assertEqual(["book-title", "body", "body"], [block["type"] for block in result["blocks"]])

    def test_empty_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "block|empty|short"):
            parse_markdown("")

    def test_source_without_any_block_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "block|empty|short"):
            parse_markdown("   \n\n ")

    def test_unordered_list_lines_are_plain_body(self):
        source = """- 第一项
- 第二项
"""
        result = parse_markdown(source)
        self.assertEqual(["body"], [block["type"] for block in result["blocks"]])
        self.assertEqual("- 第一项 - 第二项", result["blocks"][0]["text"])


class ContentIRContractTests(unittest.TestCase):
    def html_result(self):
        return parse_html("<h1>书</h1><p>正文。</p>")

    def test_root_fields_are_exact(self):
        result = self.html_result()
        self.assertEqual({"schema_version", "source_type", "source_sha256", "blocks"}, set(result))
        self.assertEqual("1.0", result["schema_version"])
        self.assertEqual("html", result["source_type"])
        self.assertEqual(source_digest("<h1>书</h1><p>正文。</p>"), result["source_sha256"])

    def test_markdown_root_source_type(self):
        result = parse_markdown("# 书")
        self.assertEqual("markdown", result["source_type"])
        self.assertEqual(source_digest("# 书"), result["source_sha256"])

    def test_every_block_has_type_text_attributes(self):
        result = self.html_result()
        for block in result["blocks"]:
            self.assertEqual({"type", "text", "attributes"}, set(block))
            self.assertIn(block["type"], ALLOWED_TYPES)
            self.assertIsInstance(block["text"], str)
            self.assertIsInstance(block["attributes"], dict)

    def test_parse_results_are_schema_valid(self):
        for result in (self.html_result(), parse_markdown("## 章\n\n正文。")):
            self.assertEqual([], validate_data(result, "book-content-ir"))

    def test_schema_closes_root_to_unexpected_properties(self):
        result = self.html_result()
        result["unexpected"] = True
        errors = validate_data(result, "book-content-ir")
        self.assertTrue(errors)
        self.assertIn("Additional properties are not allowed", "\n".join(errors))

    def test_schema_closes_block_to_unexpected_properties(self):
        result = self.html_result()
        result["blocks"][0]["unexpected"] = True
        errors = validate_data(result, "book-content-ir")
        self.assertTrue(errors)
        self.assertIn("Additional properties are not allowed", "\n".join(errors))

    def test_schema_requires_attributes_values_to_be_strings(self):
        result = self.html_result()
        result["blocks"][0]["attributes"] = {"src": 123}
        errors = validate_data(result, "book-content-ir")
        self.assertTrue(errors)
        self.assertIn("not of type 'string'", "\n".join(errors))

    def test_schema_forbids_empty_text_on_non_image_blocks(self):
        result = self.html_result()
        result["blocks"][1]["text"] = ""
        self.assertTrue(validate_data(result, "book-content-ir"))

    def test_schema_allows_empty_text_on_image_blocks(self):
        result = parse_html('<img src="bg.tif">')
        self.assertEqual([], validate_data(result, "book-content-ir"))

    def test_schema_rejects_unknown_block_types(self):
        from copy import deepcopy

        result = self.html_result()
        result["blocks"][0]["type"] = "cover"
        errors = validate_data(result, "book-content-ir")
        self.assertTrue(errors)
        self.assertIn("cover", "\n".join(errors))

    def test_schema_rejects_unknown_source_type(self):
        result = self.html_result()
        result["source_type"] = "docx"
        self.assertTrue(validate_data(result, "book-content-ir"))

    def test_invalid_internal_result_raises_value_error_from_parser(self):
        html = "<div>没有语义块</div>"
        with self.assertRaises(ValueError):
            parse_html(html)


if __name__ == "__main__":
    unittest.main()