"""边缘情况：_log→_stem、filters、分组、合并、自定义 packer。"""
import pytest

from verdant_generator.plugins import LocalizerPlugin, RecipeGeneratorPlugin
from verdant_generator.render_engine import (
    OutputFile,
    pack_grouped, pack_merged, pack_per_combination,
)


class TestLogToStem:
    def test_crimson_only(self, tmp_path):
        tpl = tmp_path / "{material_id}.txt"
        tpl.write_text("{material_id}_log", encoding="utf-8")

        plugin = LocalizerPlugin(
            template_path=str(tpl),
            materials={"oak": "橡木", "crimson": "绯红"},
            per_material_replacements={"crimson": {"_log": "_stem"}},
        )
        outputs = plugin.run()
        by_name = {f.filename: f.content for f in outputs}
        assert by_name["oak.txt"] == "oak_log"
        assert by_name["crimson.txt"] == "crimson_stem"

    def test_global_and_per_material_combined(self, tmp_path):
        tpl = tmp_path / "out.txt"
        tpl.write_text("木原木_log", encoding="utf-8")

        plugin = LocalizerPlugin(
            template_path=str(tpl),
            materials={"crimson": "绯红"},
            replacements={"木原木": "木头"},
            per_material_replacements={"crimson": {"_log": "_stem"}},
        )
        outputs = plugin.run()
        assert outputs[0].content == "木头_stem"


class TestFilters:
    def test_multiple_filters_and(self, tmp_path):
        tpl = tmp_path / "out.txt"
        tpl.write_text("{tree}", encoding="utf-8")

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["oak", "stone", "dirt", "birch"],
            filters=[
                lambda c: c["tree"] != "stone",
                lambda c: c["tree"] != "dirt",
            ],
        )
        outputs = plugin.run()
        contents = {f.content for f in outputs}
        assert contents == {"oak", "birch"}


class TestCustomPacker:
    def test_merged(self, tmp_path):
        tpl = tmp_path / "out.txt"
        tpl.write_text("{tree}", encoding="utf-8")

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["oak", "crimson", "birch"],
            packer=lambda name, results: pack_merged("_all.txt", results, joiner=" | "),
        )
        outputs = plugin.run()
        assert len(outputs) == 1
        assert outputs[0].filename == "_all.txt"
        assert outputs[0].content == "oak | crimson | birch"

    def test_grouped(self, tmp_path):
        tpl = tmp_path / "out.txt"
        tpl.write_text("{tree}", encoding="utf-8")

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["oak", "crimson"],
            packer=lambda name, results: pack_grouped(
                "tree", "{tree}.txt", results, joiner="\n"
            ),
        )
        outputs = plugin.run()
        assert len(outputs) == 2

    def test_per_material_with_summary(self, tmp_path):
        tpl = tmp_path / "{material_id}.json"
        tpl.write_text('"{material_zh_cn}"', encoding="utf-8")

        def pack_with_summary(template_name, results):
            per = pack_per_combination(template_name, results)
            summary = "\n".join(f.content for f in per)
            return per + [OutputFile("_all.json", summary)]

        plugin = LocalizerPlugin(
            template_path=str(tpl),
            materials={"oak": "橡木", "crimson": "绯红"},
            packer=pack_with_summary,
        )
        outputs = plugin.run()
        names = {f.filename for f in outputs}
        assert names == {"oak.json", "crimson.json", "_all.json"}