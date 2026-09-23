"""本地化生成插件。

配置示例：
    {
        "type": "localizer",
        "template": "templates/{material_id}.json",
        "materials": {"oak": "橡木", "crimson": "绯红"},
        "replacements": {"原木": "木"},
        "per_material_replacements": {
            "crimson": {"_log": "_stem"}
        }
    }
"""
from typing import Dict, Optional

from src.render_engine import (
    Combination, OutputFile, Packer, Plugin, PostProcessor,
    pack_per_combination,
)


class LocalizerPlugin(Plugin):
    """一对一材质对，每个材质一个组合。"""

    def __init__(
        self,
        template_path: str,
        materials: Dict[str, str],
        replacements: Optional[Dict[str, str]] = None,
        per_material_replacements: Optional[Dict[str, Dict[str, str]]] = None,
        packer: Optional[Packer] = None,
    ):
        self._template_path = template_path
        self._materials = materials
        self._replacements = replacements or {}
        self._per_material = per_material_replacements or {}
        self._packer = packer

    @property
    def name(self) -> str:
        return "localizer"

    @property
    def description(self) -> str:
        return f"根据 {len(self._materials)} 个材质生成翻译"

    def template_path(self) -> str:
        return self._template_path

    def replacements(self):
        return [
            {"material_id": mid, "material_zh_cn": zh}
            for mid, zh in self._materials.items()
        ]

    def post_processor(self) -> Optional[PostProcessor]:
        global_repl = dict(self._replacements)
        per_material = {k: dict(v) for k, v in self._per_material.items()}

        if not global_repl and not per_material:
            return None

        def process(text: str, combo: Combination) -> str:
            for old, new in global_repl.items():
                text = text.replace(old, new)
            mid = combo.get("material_id", "")
            for old, new in per_material.get(mid, {}).items():
                text = text.replace(old, new)
            return text

        return process

    def packer(self) -> Packer:
        return self._packer or pack_per_combination