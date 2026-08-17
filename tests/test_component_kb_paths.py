import base64
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ai.book_component_kb as component_kb

from ai.book_component_kb.paths import (
    load_json,
    read_image_metadata,
    safe_relative_file,
    sha256_file,
)


JPEG_8_BY_12 = (
    "/9j/4AAQSkZJRgABAQAASABIAAD/4QBMRXhpZgAATU0AKgAAAAgAAYdpAAQAAAAB"
    "AAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAACKADAAQAAAABAAAADAAAAAD/"
    "7QA4UGhvdG9zaG9wIDMuMAA4QklNBAQAAAAAAAA4QklNBCUAAAAAABDUHYzZjwCyBOmA"
    "CZjs+EJ+/8AAEQgADAAIAwEiAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgME"
    "BQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGh"
    "CCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpj"
    "ZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrC"
    "w8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+v/EAB8BAAMBAQEBAQEB"
    "AQEAAAAAAAABAgMEBQYHCAkKC//EALURAAIBAgQEAwQHBQQEAAECdwABAgMRBAUhMQYS"
    "QVEHYXETIjKBCBRCkaGxwQkjM1LwFWJy0QoWJDThJfEXGBkaJicoKSo1Njc4OTpDREV"
    "GR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoKDhIWGh4iJipKTlJWWl5iZmqKjpKW"
    "mp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uLj5OXm5+jp6vLz9PX29/j5+v/"
    "bAEMAAgICAgICAwICAwUDAwMFBgUFBQUGCAYGBgYGCAoICAgICAgKCgoKCgoKCgwMDAwM"
    "DA4ODg4ODw8PDw8PDw8PD//bAEMBAgICBAQEBwQEBxALCQsQEBAQEBAQEBAQEBAQEBAQ"
    "EBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEP/dAAQAAf/aAAwD"
    "AQACEQMRAD8A/n/ooooA/9k="
)


class ComponentKnowledgeBasePathTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.sandbox = Path(self.temp_dir.name)
        self.root = self.sandbox / "assets"
        self.root.mkdir()
        self.fixture_jpeg = self.root / "cover.png"
        self.fixture_jpeg.write_bytes(base64.b64decode(JPEG_8_BY_12))
        self.inside = self.root / "inside.jpg"
        self.inside.write_bytes(b"ordinary asset")
        self.outside = self.sandbox / "outside.jpg"
        self.outside.write_bytes(b"outside asset")
        self.outside_image = self.sandbox / "outside.png"
        self.outside_image.write_bytes(base64.b64decode(JPEG_8_BY_12))
        self.outside_record = self.sandbox / "outside.json"
        self.outside_record.write_text('{"record_id": "outside"}', encoding="utf-8")

    def test_safe_relative_file_returns_an_existing_regular_file_under_root(self):
        self.assertEqual(self.inside.resolve(), safe_relative_file(self.root, "inside.jpg"))

    def test_safe_relative_file_rejects_absolute_traversal_missing_and_directory_paths(self):
        for relative in (str(self.outside.resolve()), "../outside.jpg", "nested/../inside.jpg", "missing.jpg", "."):
            with self.subTest(relative=relative):
                with self.assertRaises(ValueError):
                    safe_relative_file(self.root, relative)

    def test_safe_relative_file_rejects_escape_and_symlink(self):
        link = self.root / "linked.jpg"
        link.symlink_to(self.outside)
        with self.assertRaises(ValueError):
            safe_relative_file(self.root, "linked.jpg")
        internal_link = self.root / "internal-link.jpg"
        internal_link.symlink_to(self.inside)
        with self.assertRaises(ValueError):
            safe_relative_file(self.root, "internal-link.jpg")

    def test_safe_relative_file_rejects_an_intermediate_directory_symlink(self):
        directory = self.root / "nested"
        directory.mkdir()
        (directory / "inside.jpg").write_bytes(b"nested asset")
        outside_directory = self.sandbox / "outside-directory"
        outside_directory.mkdir()
        (outside_directory / "inside.jpg").write_bytes(b"outside nested asset")
        linked_directory = self.root / "linked-directory"
        linked_directory.symlink_to(outside_directory, target_is_directory=True)
        with self.assertRaises(ValueError):
            safe_relative_file(self.root, "linked-directory/inside.jpg")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO support is unavailable")
    def test_safe_relative_file_rejects_a_fifo_without_opening_it_for_data(self):
        fifo = self.root / "stream"
        os.mkfifo(fifo)
        with self.assertRaises(ValueError):
            safe_relative_file(self.root, "stream")

    def test_sha256_file_hashes_raw_file_bytes(self):
        self.assertEqual(hashlib.sha256(b"ordinary asset").hexdigest(), sha256_file(self.inside))

    def test_load_json_returns_an_object(self):
        record = self.root / "record.json"
        expected = {"record_id": "COV-CN-0001", "count": 2}
        record.write_text(json.dumps(expected), encoding="utf-8")
        self.assertEqual(expected, load_json(record))

    def test_load_json_rejects_non_object_json(self):
        record = self.root / "list.json"
        record.write_text("[]", encoding="utf-8")
        with self.assertRaises(ValueError):
            load_json(record)

    def test_load_json_rejects_nonstandard_json_constants(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                record = self.root / f"{constant}.json"
                record.write_text(f'{{"value": {constant}}}', encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_json(record)

    def test_image_metadata_reads_actual_bytes(self):
        meta = read_image_metadata(self.fixture_jpeg)
        self.assertEqual({"width": 8, "height": 12, "mime_type": "image/jpeg"}, meta)

    def test_image_metadata_rejects_an_undecodable_jpeg_header(self):
        corrupt = self.root / "corrupt.jpg"
        corrupt.write_bytes(b"\xff\xd8\xff\xe0not-a-decodable-jpeg")
        with self.assertRaises(ValueError):
            read_image_metadata(corrupt)

    def test_sha256_file_rejects_a_safe_path_replaced_by_an_outside_symlink(self):
        safe_path = safe_relative_file(self.root, "inside.jpg")
        self.inside.unlink()
        self.inside.symlink_to(self.outside)
        with self.assertRaises(ValueError):
            sha256_file(safe_path)

    def test_load_json_rejects_a_safe_path_replaced_by_an_outside_symlink(self):
        record = self.root / "record.json"
        record.write_text('{"record_id": "inside"}', encoding="utf-8")
        safe_path = safe_relative_file(self.root, "record.json")
        record.unlink()
        record.symlink_to(self.outside_record)
        with self.assertRaises(ValueError):
            load_json(safe_path)

    def test_image_metadata_rejects_a_safe_path_replaced_by_an_outside_symlink(self):
        safe_path = safe_relative_file(self.root, "cover.png")
        self.fixture_jpeg.unlink()
        self.fixture_jpeg.symlink_to(self.outside_image)
        with self.assertRaises(ValueError):
            read_image_metadata(safe_path)

    def test_sha256_file_rejects_a_safe_path_when_an_intermediate_directory_is_replaced(self):
        directory = self.root / "nested"
        directory.mkdir()
        asset = directory / "inside.jpg"
        asset.write_bytes(b"inside nested asset")
        safe_path = safe_relative_file(self.root, "nested/inside.jpg")
        outside_directory = self.sandbox / "outside-directory"
        outside_directory.mkdir()
        (outside_directory / "inside.jpg").write_bytes(b"outside nested asset")
        directory.rename(self.root / "nested-original")
        directory.symlink_to(outside_directory, target_is_directory=True)
        with self.assertRaises(ValueError):
            sha256_file(safe_path)

    def test_sha256_file_rejects_a_safe_path_when_the_leaf_is_replaced_by_another_regular_file(self):
        safe_path = safe_relative_file(self.root, "inside.jpg")
        replacement = self.root / "replacement.jpg"
        replacement.write_bytes(b"replacement asset")
        replacement.replace(self.inside)
        with self.assertRaises(ValueError):
            sha256_file(safe_path)

    def test_sha256_file_rejects_a_safe_path_when_an_intermediate_directory_is_replaced_by_a_directory(self):
        directory = self.root / "nested"
        directory.mkdir()
        (directory / "inside.jpg").write_bytes(b"original nested asset")
        safe_path = safe_relative_file(self.root, "nested/inside.jpg")
        replacement = self.root / "replacement-nested"
        replacement.mkdir()
        (replacement / "inside.jpg").write_bytes(b"replacement nested asset")
        directory.rename(self.root / "nested-original")
        replacement.rename(directory)
        with self.assertRaises(ValueError):
            sha256_file(safe_path)

    def test_sha256_file_rejects_a_safe_path_when_the_root_directory_is_replaced_by_a_directory(self):
        safe_path = safe_relative_file(self.root, "inside.jpg")
        replacement_root = self.sandbox / "replacement-root"
        replacement_root.mkdir()
        (replacement_root / "inside.jpg").write_bytes(b"replacement root asset")
        self.root.rename(self.sandbox / "assets-original")
        replacement_root.rename(self.root)
        with self.assertRaises(ValueError):
            sha256_file(safe_path)

    def test_safe_path_derivations_return_plain_paths_without_the_original_identity_contract(self):
        safe_path = safe_relative_file(self.root, "inside.jpg")
        plain_path_type = type(Path())
        derived_paths = (
            safe_path.parent,
            safe_path.resolve(),
            safe_path.with_suffix(".png"),
            safe_path / "child.jpg",
        )
        for derived in derived_paths:
            with self.subTest(derived=derived):
                self.assertIs(type(derived), plain_path_type)

    def test_sha256_file_closes_a_raw_path_descriptor_when_fstat_fails(self):
        original_open = os.open
        original_fstat = os.fstat
        opened_fds = []

        def track_open(*args, **kwargs):
            file_fd = original_open(*args, **kwargs)
            opened_fds.append(file_fd)
            return file_fd

        with (
            patch("ai.book_component_kb.paths.os.open", side_effect=track_open),
            patch("ai.book_component_kb.paths.os.fstat", side_effect=OSError("injected fstat failure")),
        ):
            with self.assertRaises(ValueError):
                sha256_file(self.inside)

        self.assertEqual(1, len(opened_fds))
        with self.assertRaises(OSError):
            original_fstat(opened_fds[0])

    def test_package_exports_the_four_public_path_functions(self):
        self.assertEqual(
            ["sha256_file", "safe_relative_file", "read_image_metadata", "load_json"],
            component_kb.__all__,
        )
        self.assertIs(sha256_file, component_kb.sha256_file)


if __name__ == "__main__":
    unittest.main()
