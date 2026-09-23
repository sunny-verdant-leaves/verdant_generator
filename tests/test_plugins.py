"""测试两个示例插件。"""
import pytest

from verdant_generator.plugins import LocalizerPlugin, RecipeGeneratorPlugin


class TestRecipeGenerator:
    def test_basic(self, tmp_path):
        tpl = tmp_path / "{tree}.json"
        tpl.write_text('{"item": "{tree}_planks"}', encoding="utf-8")

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["oak", "crimson"],
        )
        outputs = plugin.run()

        assert len(outputs) == 2
        by_name = {f.filename: f.content for f in outputs}
        assert by_name["oak.json"] == '{"item": "oak_planks"}'
        assert by_name["crimson.json"] == '{"item": "crimson_planks"}'

    def test_full_id_derives_short_name(self, tmp_path):
        """完整 ID 会被拆成短名，{tree} 得到短名。"""
        tpl = tmp_path / "{tree}.json"
        tpl.write_text('{"item": "{tree}_planks"}', encoding="utf-8")

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["minecraft:oak", "biomesoplenty:fir"],
        )
        outputs = plugin.run()
        by_name = {f.filename: f.content for f in outputs}

        # 文件名用短名
        assert "oak.json" in by_name
        assert "fir.json" in by_name
        # 内容也是短名
        assert by_name["oak.json"] == '{"item": "oak_planks"}'
        assert by_name["fir.json"] == '{"item": "fir_planks"}'

    def test_modid_and_modid_safe_available(self, tmp_path):
        """完整 ID 会派生 {modid} 和 {modid_safe}。"""
        tpl = tmp_path / "tpl.txt"
        tpl.write_text(
            "{modid}{tree}|{modid_safe}|{tree}",
            encoding="utf-8",
        )

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["minecraft:oak", "biomesoplenty:fir"],
        )
        outputs = plugin.run()
        by_name = {f.filename: f.content for f in outputs}

        # 默认输出名模板是模板文件名 "tpl.txt"（不含占位符）
        # 所有组合会写同名文件，只保留最后一个——这是设计如此
        assert "tpl.txt" in by_name
        assert by_name["tpl.txt"] == "biomesoplenty:fir|biomesoplenty_|fir"

    def test_output_name_template_with_modid(self, tmp_path):
        """用 {modid}{tree} 做输出名，文件名里会带命名空间（被 safe 化）。"""
        tpl = tmp_path / "raw.txt"
        tpl.write_text('{"item": "{modid}{tree}_planks"}', encoding="utf-8")

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["minecraft:oak", "biomesoplenty:fir"],
            output_name_template="{modid}{tree}.json",
        )
        outputs = plugin.run()
        by_name = {f.filename: f.content for f in outputs}

        # 文件名里的 : 被 safe 化为 _
        assert "minecraft_oak.json" in by_name
        assert "biomesoplenty_fir.json" in by_name
        # 内容里的 : 保留
        assert by_name["minecraft_oak.json"] == '{"item": "minecraft:oak_planks"}'
        assert by_name["biomesoplenty_fir.json"] == '{"item": "biomesoplenty:fir_planks"}'

    def test_filters(self, tmp_path):
        tpl = tmp_path / "{tree}.txt"
        tpl.write_text("{tree}", encoding="utf-8")

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["oak", "stone", "crimson"],
            filters=[lambda c: c["tree"] != "stone"],
        )
        outputs = plugin.run()
        names = {f.filename for f in outputs}

        assert names == {"oak.txt", "crimson.txt"}

    def test_name_and_description(self):
        plugin = RecipeGeneratorPlugin(template_path="x.json", trees=["a", "b"])
        assert plugin.name == "recipe_generator"
        assert "2" in plugin.description


class TestLocalizer:
    def test_basic_short_name(self, tmp_path):
        """短名输入，用 default_namespace 补。"""
        tpl = tmp_path / "{material_id}.json"
        tpl.write_text('"{material_zh_cn}"', encoding="utf-8")

        plugin = LocalizerPlugin(
            template_path=str(tpl),
            materials={"oak": "橡木", "crimson": "绯红"},
        )
        outputs = plugin.run()

        assert len(outputs) == 2
        by_name = {f.filename: f.content for f in outputs}
        assert by_name["oak.json"] == '"橡木"'
        assert by_name["crimson.json"] == '"绯红"'

    def test_full_id_input(self, tmp_path):
        """完整 ID 输入，自动派生 modid / modid_safe。"""
        tpl = tmp_path / "tpl.txt"
        tpl.write_text(
            "{modid}{material_id}|{modid_safe}|{material_zh_cn}",
            encoding="utf-8",
        )

        plugin = LocalizerPlugin(
            template_path=str(tpl),
            materials={
                "minecraft:oak": "橡木",
                "biomesoplenty:fir": "冷杉",
            },
            output_name_template="{modid}{material_id}.txt",
        )
        outputs = plugin.run()
        by_name = {f.filename: f.content for f in outputs}

        # 文件名 safe 化（: → _）
        assert "minecraft_oak.txt" in by_name
        assert "biomesoplenty_fir.txt" in by_name
        # 内容里 : 保留；modid_safe 对 minecraft 是空
        assert by_name["minecraft_oak.txt"] == "minecraft:oak||橡木"
        assert by_name["biomesoplenty_fir.txt"] == \
            "biomesoplenty:fir|biomesoplenty_|冷杉"

    def test_post_processor_global(self, tmp_path):
        tpl = tmp_path / "{material_id}.txt"
        tpl.write_text("{material_zh_cn}原木", encoding="utf-8")

        plugin = LocalizerPlugin(
            template_path=str(tpl),
            materials={"crimson": "绯红"},
            replacements={"原木": "菌柄"},
        )
        outputs = plugin.run()
        assert outputs[0].content == "绯红菌柄"

    def test_post_processor_per_material(self, tmp_path):
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

    def test_post_processor_isolated_per_group(self, tmp_path):
        """材质专属规则互不污染：oak 的规则不作用于 andesite，反之亦然。"""
        # 模板里同时出现 material_id 和 material_zh_cn
        # 这样一条规则可以对键名生效，另一条对内容生效，更清晰
        tpl = tmp_path / "{material_id}.txt"
        tpl.write_text("{material_id}|{material_zh_cn}", encoding="utf-8")

        plugin = LocalizerPlugin(
            template_path=str(tpl),
            materials={"oak": "橡木", "andesite": "安山岩"},
            per_material_replacements={
                # oak 的规则：把 key 里的 oak 换成 OAK
                "oak": {"oak": "OAK"},
                # andesite 的规则：把 key 里的 andesite 换成 AND
                "andesite": {"andesite": "AND"},
            },
        )
        outputs = plugin.run()
        by_name = {f.filename: f.content for f in outputs}

        # oak 只受 oak 的规则影响
        assert by_name["oak.txt"] == "OAK|橡木"
        # andesite 只受 andesite 的规则影响
        assert by_name["andesite.txt"] == "AND|安山岩"

    def test_no_post_processor_when_empty(self, tmp_path):
        tpl = tmp_path / "x.txt"
        tpl.write_text("{material_zh_cn}", encoding="utf-8")

        plugin = LocalizerPlugin(
            template_path=str(tpl),
            materials={"oak": "橡木"},
        )
        assert plugin.post_processor() is None

    def test_name_and_description(self):
        plugin = LocalizerPlugin(
            template_path="x.json",
            materials={"oak": "橡木", "birch": "白桦"},
        )
        assert plugin.name == "localizer"
        assert "2" in plugin.description