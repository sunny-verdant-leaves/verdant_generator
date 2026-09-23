"""本地化生成插件。

支持两种 materials 输入：
    - 完整 ID: {"minecraft:oak": "橡木", "biomesoplenty:fir": "冷杉"}
      → 自动派生 material_id（短名）、modid、modid_safe
    - 短名:   {"oak": "橡木"}
      → 用 default_namespace 补 modid
"""
from pathlib import Path
from typing import Dict, Optional

from src.render_engine import (
    Combination, OutputFile, Packer, Plugin, PostProcessor,
    pack_per_combination,
)


class LocalizerPlugin(Plugin):
    def __init__(
        self,
        template_path: str,
        materials: Dict[str, str],
        output_name_template: Optional[str] = None,
        default_namespace: str = "minecraft",
        replacements: Optional[Dict[str, str]] = None,
        per_material_replacements: Optional[Dict[str, Dict[str, str]]] = None,
        packer: Optional[Packer] = None,
    ):
        self._template_path = template_path
        self._materials = materials
        self._output_name_template = output_name_template
        self._default_ns = default_namespace
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

    def output_name_template(self) -> str:
        if self._output_name_template:
            return self._output_name_template
        return Path(self._template_path).name

    def replacements(self):
        return [self._make_combo(full_id, zh)
                for full_id, zh in self._materials.items()]

    def _make_combo(self, full_id: str, zh: str) -> Combination:
        if ":" in full_id:
            ns, short = full_id.split(":", 1)
        else:
            ns, short = self._default_ns.rstrip(":"), full_id

        ns = ns.rstrip(":")

        if ns == "minecraft":
            modid = "minecraft:"
            modid_safe = ""
        else:
            modid = f"{ns}:"
            modid_safe = f"{ns}_"

        return {
            "material_id": short,
            "modid": modid,
            "modid_safe": modid_safe,
            "material_zh_cn": zh,
        }

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