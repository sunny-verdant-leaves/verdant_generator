"""测试两个示例插件。"""
import pytest

from verdant_generator.plugins import LocalizerPlugin, RecipeGeneratorPlugin


class TestRecipeGenerator:
    def test_basic(self, tmp_path):
        tpl = tmp_path / "{tree}.json"
        tpl.write_text('{"item": "{modid}:{tree}_planks"}', encoding="utf-8")

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["oak", "crimson"],
        )
        outputs = plugin.run()

        assert len(outputs) == 2
        by_name = {f.filename: f.content for f in outputs}
        assert by_name["oak.json"] == '{"item": "minecraft:oak_planks"}'
        assert by_name["crimson.json"] == '{"item": "minecraft:crimson_planks"}'

    def test_full_id_derives_short_name(self, tmp_path):
        """完整 ID 会被拆成短名。"""
        tpl = tmp_path / "{tree}.json"
        tpl.write_text('{"item": "{modid}:{tree}_planks"}', encoding="utf-8")

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["minecraft:oak", "biomesoplenty:fir"],
        )
        outputs = plugin.run()
        by_name = {f.filename: f.content for f in outputs}

        assert "oak.json" in by_name
        assert "fir.json" in by_name
        assert by_name["oak.json"] == '{"item": "minecraft:oak_planks"}'
        assert by_name["fir.json"] == '{"item": "biomesoplenty:fir_planks"}'

    def test_modid_no_colon(self, tmp_path):
        """{modid} 不带冒号，模板里手动拼冒号。"""
        tpl = tmp_path / "tpl.txt"
        tpl.write_text("{modid}:{tree}", encoding="utf-8")

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["minecraft:oak", "biomesoplenty:fir"],
        )
        outputs = plugin.run()
        by_name = {f.filename: f.content for f in outputs}

        # 同名文件只保留最后一个
        assert "tpl.txt" in by_name
        assert by_name["tpl.txt"] == "biomesoplenty:fir"

    def test_output_name_template_with_modid(self, tmp_path):
        """用 {modid}_{tree} 做输出名，文件名带模组前缀。"""
        tpl = tmp_path / "raw.txt"
        tpl.write_text('{"item": "{modid}:{tree}_planks"}', encoding="utf-8")

        plugin = RecipeGeneratorPlugin(
            template_path=str(tpl),
            trees=["minecraft:oak", "biomesoplenty:fir"],
            output_name_template="{modid}_{tree}.json",
        )
        outputs = plugin.run()
        by_name = {f.filename: f.content for f in outputs}

        assert "minecraft_oak.json" in by_name
        assert "biomesoplenty_fir.json" in by_name
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
        """短名输入，用 default_namespace 补 modid。"""
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
        """完整 ID 输入，自动派生 modid。"""
        tpl = tmp_path / "tpl.txt"
        tpl.write_text(
            "{modid}:{material_id}|{material_zh_cn}",
            encoding="utf-8",
        )

        plugin = LocalizerPlugin(
            template_path=str(tpl),
            materials={
                "minecraft:oak": "橡木",
                "biomesoplenty:fir": "冷杉",
            },
            output_name_template="{modid}_{material_id}.txt",
        )
        outputs = plugin.run()
        by_name = {f.filename: f.content for f in outputs}

        assert "minecraft_oak.txt" in by_name
        assert "biomesoplenty_fir.txt" in by_name
        assert by_name["minecraft_oak.txt"] == "minecraft:oak|橡木"
        assert by_name["biomesoplenty_fir.txt"] == "biomesoplenty:fir|冷杉"

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
        """材质专属规则互不污染。"""
        tpl = tmp_path / "{material_id}.txt"
        tpl.write_text("{material_id}|{material_zh_cn}", encoding="utf-8")

        plugin = LocalizerPlugin(
            template_path=str(tpl),
            materials={"oak": "橡木", "andesite": "安山岩"},
            per_material_replacements={
                "oak": {"oak": "OAK"},
                "andesite": {"andesite": "AND"},
            },
        )
        outputs = plugin.run()
        by_name = {f.filename: f.content for f in outputs}

        assert by_name["oak.txt"] == "OAK|橡木"
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