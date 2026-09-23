"""本地化生成插件 - 复现旧项目 LocalizerService 的功能。

支持：
    - 一对一的材质对（material_id → material_zh_cn），不做笛卡尔积
    - 全局后处理替换（replacements）
    - 按材质区分的后处理替换（per_material_replacements）
      对应旧项目里 "crimson 的 _log → _stem" 这类规则
    - 自定义 packer，默认 per_combination
"""
from typing import Callable, Dict, List, Optional

from src.render_engine import (
    Combination, OutputFile, Plugin, PostProcessor, Strategy, Variable,
    pack_per_combination,
)


class LocalizerPlugin(Plugin):
    """根据材质对，批量生成翻译文件。"""

    def __init__(
        self,
        template_path: str,
        materials: Dict[str, str],
        replacements: Optional[Dict[str, str]] = None,
        per_material_replacements: Optional[Dict[str, Dict[str, str]]] = None,
        packer: Optional[Callable[[str, list], List[OutputFile]]] = None,
    ):
        """
        :param template_path: 模板文件路径
        :param materials: {material_id: material_zh_cn} 一一对应
        :param replacements: 全局后处理替换 {old: new}，按 dict 顺序应用
        :param per_material_replacements: 按材质区分的替换
                                           {material_id: {old: new}}
                                           全局替换先执行，再执行专属替换
        :param packer: 自定义打包函数，默认 pack_per_combination
        """
        self._template_path = template_path
        self._materials = materials
        self._replacements = replacements or {}
        self._per_material = per_material_replacements or {}
        self._packer = packer or pack_per_combination

    @property
    def name(self) -> str:
        return "localizer"

    @property
    def description(self) -> str:
        return f"根据 {len(self._materials)} 个材质生成翻译文件"

    def template_path(self) -> str:
        return self._template_path

    def strategy(self) -> Strategy:
        # 组合由 build_combinations 自己算，variables 留空
        return Strategy(variables=[], packer=self._packer)

    def build_combinations(self, pool: Dict[str, Variable]) -> List[Combination]:
        """覆盖默认：一对一材质对，不做笛卡尔积。"""
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
            # 1. 全局替换
            for old, new in global_repl.items():
                text = text.replace(old, new)
            # 2. 材质专属替换
            mid = combo.get("material_id", "")
            for old, new in per_material.get(mid, {}).items():
                text = text.replace(old, new)
            return text

        return process