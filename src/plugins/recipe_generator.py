"""配方生成插件。

配置示例：
    {
        "type": "recipe_generator",
        "template": "templates/{tree}.json",
        "trees": ["minecraft:oak", "minecraft:crimson"]
    }
"""
from typing import Callable, List, Optional

from src.render_engine import (
    Combination, Packer, Plugin, pack_per_combination,
)


class RecipeGeneratorPlugin(Plugin):
    """单变量 tree，每个值一个组合。"""

    def __init__(
        self,
        template_path: str,
        trees: List[str],
        filters: Optional[List[Callable[[Combination], bool]]] = None,
        packer: Optional[Packer] = None,
    ):
        self._template_path = template_path
        self._trees = trees
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

    def replacements(self) -> List[Combination]:
        combos = [{"tree": t} for t in self._trees]
        if self._filters:
            combos = [c for c in combos if all(f(c) for f in self._filters)]
        return combos

    def packer(self) -> Packer:
        return self._packer or pack_per_combination