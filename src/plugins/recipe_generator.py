"""配方生成插件 - 复现旧项目 RecipeService 的功能。

支持：
    - 单变量（如 tree）或多变量笛卡尔积
    - 自定义过滤器（等价于旧项目的 skip_patterns）
    - 自定义 packer（默认 per_combination）
"""
from typing import List, Optional

from src.render_engine import (
    Filter, Packer, Plugin, Strategy, pack_per_combination,
)


class RecipeGeneratorPlugin(Plugin):
    """根据变量池里的变量，批量生成配方文件。"""

    def __init__(
        self,
        template_path: str,
        variable_names: Optional[List[str]] = None,
        filters: Optional[List[Filter]] = None,
        packer: Optional[Packer] = None,
    ):
        """
        :param template_path: 模板文件路径
        :param variable_names: 参与组合的变量名列表，默认 ["tree"]
        :param filters: 过滤器列表，任一返回 False 则丢弃该组合
        :param packer: 自定义打包函数，默认 pack_per_combination
        """
        self._template_path = template_path
        self._variable_names = variable_names or ["tree"]
        self._filters = filters or []
        self._packer = packer or pack_per_combination

    @property
    def name(self) -> str:
        return "recipe_generator"

    @property
    def description(self) -> str:
        return f"根据 {'/'.join(self._variable_names)} 生成配方文件"

    def template_path(self) -> str:
        return self._template_path

    def strategy(self) -> Strategy:
        return Strategy(
            variables=self._variable_names,
            packer=self._packer,
            filters=self._filters,
        )