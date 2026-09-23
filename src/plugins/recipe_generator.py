"""配方生成插件。

trees 可以是完整 ID（"minecraft:oak"）或短名（"oak"）。
"""
from typing import Callable, List, Optional

from src.render_engine import (
    Combination, Packer, Plugin, pack_per_combination,
)


class RecipeGeneratorPlugin(Plugin):
    def __init__(
        self,
        template_path: str,
        trees: List[str],
        output_name_template: Optional[str] = None,
        default_namespace: str = "minecraft",
        filters: Optional[List[Callable[[Combination], bool]]] = None,
        packer: Optional[Packer] = None,
    ):
        self._template_path = template_path
        self._trees = trees
        self._output_name_template = output_name_template
        self._default_ns = default_namespace
        self._filters = filters or []
        self._packer = packer

    @property
    def name(self) -> str:
        return "recipe_generator"

    @property
    def description(self) -> str:
        return f"根据 {len(self._trees)} 个 tree 生成配方"

    def template_path(self) -> str:
        return self._template_path

    def output_name_template(self) -> str:
        if self._output_name_template:
            return self._output_name_template
        from pathlib import Path
        return Path(self._template_path).name

    def replacements(self):
        combos = [self._make_combo(t) for t in self._trees]
        if self._filters:
            combos = [c for c in combos if all(f(c) for f in self._filters)]
        return combos

    def _make_combo(self, full_id: str) -> Combination:
        if ":" in full_id:
            ns, short = full_id.split(":", 1)
        else:
            ns, short = self._default_ns, full_id

        if ns == "minecraft":
            modid = "minecraft:"
            modid_safe = ""
        else:
            modid = f"{ns}:"
            modid_safe = f"{ns}_"

        return {
            "tree": short,
            "modid": modid,
            "modid_safe": modid_safe,
        }

    def packer(self) -> Packer:
        return self._packer or pack_per_combination