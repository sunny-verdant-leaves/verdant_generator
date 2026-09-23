"""配置加载：JSON → Variable / Strategy / Plugin。

设计原则：
    - JSON 里 packer 只写名字，函数从内置注册表里查（方案 A）
    - 插件构造参数各不同，用工厂注册表翻译 JSON 字段 → 构造参数
    - 需要新 packer / 新插件时，改注册表即可
"""
import json
from pathlib import Path
from typing import Dict, List

from src.render_engine import (
    Plugin, Strategy, Variable,
    pack_per_combination,
)
from src.plugins import LocalizerPlugin, RecipeGeneratorPlugin


# ==================== Packer 注册表 ====================

PACKERS = {
    "per_combination": pack_per_combination,
    # 需要参数的 packer（merged / grouped）暂不支持从 JSON 来
}


# ==================== 插件工厂注册表 ====================

def _make_recipe_generator(data: dict) -> RecipeGeneratorPlugin:
    return RecipeGeneratorPlugin(
        template_path=data["template"],
        variable_names=data.get("variables"),
    )


def _make_localizer(data: dict) -> LocalizerPlugin:
    return LocalizerPlugin(
        template_path=data["template"],
        materials=data["materials"],
        replacements=data.get("replacements"),
        per_material_replacements=data.get("per_material_replacements"),
    )


PLUGIN_FACTORIES = {
    "recipe_generator": _make_recipe_generator,
    "localizer": _make_localizer,
}


# ==================== 加载函数 ====================

def load_variables(data: dict) -> Dict[str, Variable]:
    """{"tree": ["oak", "crimson"]} → {"tree": Variable("tree", [...])}"""
    return {name: Variable(name, values) for name, values in data.items()}


def load_strategy(data: dict) -> Strategy:
    """{"variables": [...], "packer": "per_combination"} → Strategy"""
    packer_name = data["packer"]
    if packer_name not in PACKERS:
        raise KeyError(f"未知 packer: {packer_name}")
    return Strategy(
        variables=data["variables"],
        packer=PACKERS[packer_name],
    )


def load_strategies(data: dict) -> Dict[str, Strategy]:
    return {name: load_strategy(cfg) for name, cfg in data.items()}


def load_plugin(data: dict) -> Plugin:
    """{"type": "recipe_generator", ...} → Plugin 实例"""
    plugin_type = data["type"]
    if plugin_type not in PLUGIN_FACTORIES:
        raise KeyError(f"未知插件类型: {plugin_type}")
    return PLUGIN_FACTORIES[plugin_type](data)


def load_plugins(data: list) -> List[Plugin]:
    return [load_plugin(item) for item in data]


def load_config(path: str) -> dict:
    """从文件加载完整配置。

    返回:
        {
            "variables":  Dict[str, Variable],
            "strategies": Dict[str, Strategy],
            "plugins":    List[Plugin],
        }
    """
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    return {
        "variables": load_variables(raw.get("variables", {})),
        "strategies": load_strategies(raw.get("strategies", {})),
        "plugins": load_plugins(raw.get("plugins", [])),
    }