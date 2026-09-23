"""测试三种 packer 和 safe_filename。"""
import pytest

from verdant_generator.render_engine import (
    OutputFile,
    pack_grouped,
    pack_merged,
    pack_per_combination,
    safe_filename,
)


class TestPackPerCombination:
    def test_one_file_per_combo(self):
        results = [
            ({"tree": "oak"}, "content-oak"),
            ({"tree": "crimson"}, "content-crimson"),
        ]
        outputs = pack_per_combination("{tree}.json", results)
        assert len(outputs) == 2
        assert outputs[0].filename == "oak.json"
        assert outputs[0].content == "content-oak"
        assert outputs[1].filename == "crimson.json"

    def test_filename_without_placeholder(self):
        results = [({"x": "1"}, "a"), ({"x": "2"}, "b")]
        outputs = pack_per_combination("fixed.json", results)
        # 文件名相同，但仍是两个 OutputFile（不会自动合并）
        assert len(outputs) == 2
        assert all(f.filename == "fixed.json" for f in outputs)

    def test_empty_results(self):
        assert pack_per_combination("{tree}.json", []) == []


class TestPackMerged:
    def test_all_merged_into_one(self):
        results = [
            ({"x": "1"}, "line1"),
            ({"x": "2"}, "line2"),
        ]
        outputs = pack_merged("all.txt", results)
        assert len(outputs) == 1
        assert outputs[0].filename == "all.txt"
        assert outputs[0].content == "line1\nline2"

    def test_custom_joiner(self):
        results = [({}, "a"), ({}, "b")]
        outputs = pack_merged("out.txt", results, joiner=" | ")
        assert outputs[0].content == "a | b"

    def test_empty_results(self):
        outputs = pack_merged("empty.txt", [])
        assert len(outputs) == 1
        assert outputs[0].content == ""


class TestPackGrouped:
    def test_group_by_single_key(self):
        results = [
            ({"tree": "oak", "cat": "chair"}, "oak-chair"),
            ({"tree": "oak", "cat": "table"}, "oak-table"),
            ({"tree": "crimson", "cat": "chair"}, "crimson-chair"),
        ]
        outputs = pack_grouped("tree", "{tree}.txt", results)

        assert len(outputs) == 2
        by_name = {f.filename: f.content for f in outputs}
        assert by_name["oak.txt"] == "oak-chair\noak-table"
        assert by_name["crimson.txt"] == "crimson-chair"

    def test_custom_joiner(self):
        results = [
            ({"tree": "oak", "cat": "a"}, "1"),
            ({"tree": "oak", "cat": "b"}, "2"),
        ]
        outputs = pack_grouped("tree", "{tree}.txt", results, joiner="|")
        assert outputs[0].content == "1|2"

    def test_missing_group_key_uses_default(self):
        results = [({"other": "x"}, "content")]
        outputs = pack_grouped("tree", "{tree}.txt", results)
        # group key 缺失，_default 分组；但 name_template 里的 {tree} 无法替换
        assert len(outputs) == 1
        assert outputs[0].filename == "{tree}.txt"  # 占位符保留

    def test_empty_results(self):
        assert pack_grouped("tree", "{tree}.txt", []) == []


class TestSafeFilename:
    def test_colon_replaced(self):
        assert safe_filename("minecraft:oak.json") == "minecraft_oak.json"

    def test_backslash_and_illegal_chars(self):
        assert safe_filename('a<b>c"d|e?f*g.json') == "a_b_c_d_e_f_g.json"

    def test_slash_kept_for_subdirs(self):
        assert safe_filename("sub/dir/file.txt") == "sub/dir/file.txt"

    def test_trailing_dot_and_space_removed(self):
        assert safe_filename("file.  ") == "file"

    def test_chinese_unchanged(self):
        assert safe_filename("橡木.json") == "橡木.json"

    def test_pack_applies_safe_filename(self):
        results = [({"tree": "minecraft:oak"}, "x")]
        outputs = pack_per_combination("{tree}.json", results)
        assert outputs[0].filename == "minecraft_oak.json"


class TestSafeFilenameContract:
    """钉死 safe_filename 的边界：只处理文件名，内容不动。"""

    def test_content_keeps_colon(self, tmp_path):
        """内容里的 : 必须保留，不能被 safe 化。"""
        results = [
            ({"tree": "minecraft:oak"},
             '{"item": "minecraft:oak_planks"}'),
        ]
        outputs = pack_per_combination("{tree}.json", results)
        # 文件名被 safe 化
        assert outputs[0].filename == "minecraft_oak.json"
        # 内容里的 : 保留
        assert '"minecraft:oak_planks"' in outputs[0].content

    def test_content_keeps_slash(self):
        """内容里的 / 必须保留。"""
        results = [({"x": "a/b"}, "path: a/b")]
        outputs = pack_per_combination("out.txt", results)
        assert outputs[0].content == "path: a/b"

    def test_filename_slash_kept_as_subdir(self):
        """文件名里的 / 表示子目录，不被替换。"""
        results = [({"x": "1"}, "c")]
        outputs = pack_per_combination("sub/{x}/file.txt", results)
        assert outputs[0].filename == "sub/1/file.txt"

    def test_render_does_not_touch_colon(self):
        """render 只替换占位符，不做任何字符转换。"""
        from verdant_generator.render_engine import render
        result = render("{a}:{b}/{c}", {"a": "x", "b": "y", "c": "z"})
        assert result == "x:y/z"

    def test_render_does_not_touch_underscore(self):
        from verdant_generator.render_engine import render
        result = render("{a}_{b}", {"a": "x", "b": "y"})
        assert result == "x_y"