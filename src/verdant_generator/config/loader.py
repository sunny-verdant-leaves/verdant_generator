"""配置加载：JSON → Plugin 实例。"""
import json
from pathlib import Path
from typing import List

from verdant_generator.render_engine import Plugin
from verdant_generator.plugins import LocalizerPlugin, RecipeGeneratorPlugin


def _make_recipe_generator(data: dict) -> RecipeGeneratorPlugin:
    return RecipeGeneratorPlugin(
        template_path=data["template"],
        trees=data["trees"],
        output_name_template=data.get("output_name"),
        default_namespace=data.get("default_namespace", "minecraft"),
    )


def _make_localizer(data: dict) -> LocalizerPlugin:
    return LocalizerPlugin(
        template_path=data["template"],
        materials=data["materials"],
        output_name_template=data.get("output_name"),
        default_namespace=data.get("default_namespace", "minecraft"),
        replacements=data.get("replacements"),
        per_material_replacements=data.get("per_material_replacements"),
    )


PLUGIN_FACTORIES = {
    "recipe_generator": _make_recipe_generator,
    "localizer": _make_localizer,
}


def load_plugin(data: dict) -> Plugin:
    plugin_type = data.get("type")
    if plugin_type not in PLUGIN_FACTORIES:
        raise KeyError(f"未知插件类型: {plugin_type}")
    return PLUGIN_FACTORIES[plugin_type](data)


def load_plugins(data: list) -> List[Plugin]:
    return [load_plugin(item) for item in data]


def load_config(path: str) -> dict:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    return {"plugins": load_plugins(raw.get("plugins", []))}