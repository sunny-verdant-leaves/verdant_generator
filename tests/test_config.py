"""测试配置加载。"""
import json
from pathlib import Path

import pytest

from verdant_generator.config import load_config, load_plugin, load_plugins
from verdant_generator.plugins import LocalizerPlugin, RecipeGeneratorPlugin


class TestLoadPlugin:
    def test_recipe_generator(self):
        p = load_plugin({
            "type": "recipe_generator",
            "template": "templates/{tree}.json",
            "trees": ["minecraft:oak", "minecraft:crimson"],
        })
        assert isinstance(p, RecipeGeneratorPlugin)
        assert p.template_path() == "templates/{tree}.json"

    def test_localizer(self):
        p = load_plugin({
            "type": "localizer",
            "template": "templates/x.json",
            "materials": {"oak": "橡木"},
        })
        assert isinstance(p, LocalizerPlugin)

    def test_localizer_with_replacements(self):
        p = load_plugin({
            "type": "localizer",
            "template": "x.json",
            "materials": {"crimson": "绯红"},
            "replacements": {"原木": "菌柄"},
            "per_material_replacements": {"crimson": {"_log": "_stem"}},
        })
        assert isinstance(p, LocalizerPlugin)

    def test_unknown_type_raises(self):
        with pytest.raises(KeyError, match="未知插件类型"):
            load_plugin({"type": "no_such_plugin"})

    def test_missing_type_raises(self):
        with pytest.raises(KeyError):
            load_plugin({"template": "x.json"})


class TestLoadPlugins:
    def test_multiple(self):
        result = load_plugins([
            {"type": "recipe_generator", "template": "a.json", "trees": []},
            {"type": "localizer", "template": "b.json", "materials": {}},
        ])
        assert len(result) == 2

    def test_empty(self):
        assert load_plugins([]) == []


class TestLoadConfig:
    def test_full(self, tmp_path):
        config = {
            "plugins": [
                {"type": "recipe_generator", "template": "x.json", "trees": ["a"]},
            ],
        }
        path = tmp_path / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")

        result = load_config(str(path))
        assert set(result.keys()) == {"plugins"}
        assert len(result["plugins"]) == 1

    def test_empty_config(self, tmp_path):
        path = tmp_path / "config.json"
        path.write_text("{}", encoding="utf-8")
        result = load_config(str(path))
        assert result["plugins"] == []

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            load_config("no_such_file.json")


class TestEndToEnd:
    def test_recipe_generator_via_config(self, tmp_path):
        tpl_dir = tmp_path / "templates"
        tpl_dir.mkdir()
        (tpl_dir / "{tree}.json").write_text(
            '{"item": "{tree}_planks"}', encoding="utf-8"
        )

        config = {
            "plugins": [
                {
                    "type": "recipe_generator",
                    "template": str(tpl_dir / "{tree}.json").replace("\\", "/"),
                    "trees": ["oak", "crimson"],
                },
            ],
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        loaded = load_config(str(config_path))
        plugin = loaded["plugins"][0]
        outputs = plugin.run()

        assert len(outputs) == 2
        by_name = {f.filename: f.content for f in outputs}
        assert by_name["oak.json"] == '{"item": "oak_planks"}'
        assert by_name["crimson.json"] == '{"item": "crimson_planks"}'

    def test_localizer_via_config(self, tmp_path):
        tpl_dir = tmp_path / "templates"
        tpl_dir.mkdir()
        template_file = tpl_dir / "{material_id}.json"
        template_file.write_text(
            '{"block.pfm.{material_id}_log": "{material_zh_cn}原木"}',
            encoding="utf-8",
        )

        config = {
            "plugins": [
                {
                    "type": "localizer",
                    "template": str(template_file).replace("\\", "/"),
                    "materials": {"crimson": "绯红", "oak": "橡木"},
                    "per_material_replacements": {"crimson": {"_log": "_stem"}},
                },
            ],
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        loaded = load_config(str(config_path))
        plugin = loaded["plugins"][0]
        outputs = plugin.run()

        by_name = {f.filename: f.content for f in outputs}
        assert by_name["crimson.json"] == '{"block.pfm.crimson_stem": "绯红原木"}'
        assert by_name["oak.json"] == '{"block.pfm.oak_log": "橡木原木"}'