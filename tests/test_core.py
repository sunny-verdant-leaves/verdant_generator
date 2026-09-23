"""测试 render / safe_filename。"""
import pytest

from verdant_generator.render_engine import render, safe_filename


class TestRender:
    def test_basic_replacement(self):
        assert render("item.{tree}_planks", {"tree": "oak"}) == "item.oak_planks"

    def test_multiple_placeholders(self):
        assert render("{a}-{b}-{a}", {"a": "X", "b": "Y"}) == "X-Y-X"

    def test_unknown_placeholder_kept_by_default(self):
        assert render("{known} and {unknown}", {"known": "yes"}) == "yes and {unknown}"

    def test_strict_mode_raises_on_missing(self):
        with pytest.raises(KeyError) as exc:
            render("{a} {b}", {"a": "1"}, strict=True)
        assert "b" in str(exc.value)

    def test_strict_mode_passes_when_all_present(self):
        assert render("{a}", {"a": "1"}, strict=True) == "1"

    def test_no_placeholder_returns_original(self):
        assert render("plain text", {"x": "y"}) == "plain text"

    def test_invalid_placeholder_name_ignored(self):
        assert render("{1abc} {abc}", {"1abc": "X", "abc": "Y"}) == "{1abc} Y"

    def test_placeholder_with_underscore_and_digits(self):
        assert render("{tree_id_2}", {"tree_id_2": "oak"}) == "oak"

    def test_chinese_placeholder_value(self):
        assert render("block.{material}_chair", {"material": "橡木"}) == "block.橡木_chair"

    def test_does_not_touch_colon(self):
        assert render("{a}:{b}/{c}", {"a": "x", "b": "y", "c": "z"}) == "x:y/z"


class TestSafeFilename:
    def test_colon_replaced(self):
        assert safe_filename("minecraft:oak.json") == "minecraft_oak.json"

    def test_illegal_chars_replaced(self):
        assert safe_filename('a<b>c"d|e?f*g.json') == "a_b_c_d_e_f_g.json"

    def test_slash_kept(self):
        assert safe_filename("sub/dir/file.txt") == "sub/dir/file.txt"

    def test_trailing_dot_and_space_removed(self):
        assert safe_filename("file.  ") == "file"

    def test_chinese_unchanged(self):
        assert safe_filename("橡木.json") == "橡木.json"