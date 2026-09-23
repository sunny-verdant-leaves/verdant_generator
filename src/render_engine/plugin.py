"""插件抽象：声明意图 + 可选覆盖。"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .core import (
    Combination, Filter, OutputFile, PostProcessor, Strategy,
    Template, Variable,
    cartesian, render,
)


class Plugin(ABC):
    """渲染插件基类。

    子类必须声明：
        name          插件名
        template_path 用哪个模板
        strategy      用什么策略（变量 + 过滤器 + 打包方式）
    可选覆盖：
        description      描述
        output_subdir    输出子目录（默认 = name）
        build_combinations  自己构造组合（默认走 strategy）
        post_processor   后处理
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    def description(self) -> str:
        return ""

    @abstractmethod
    def template_path(self) -> str:
        ...

    @abstractmethod
    def strategy(self) -> Strategy:
        ...

    def output_subdir(self) -> str:
        """输出子目录名（相对于 base_output_dir）。默认用插件名。"""
        return self.name

    def build_combinations(self, pool: Dict[str, Variable]) -> List[Combination]:
        """默认实现：从策略里读变量 + 过滤器，做笛卡尔积。"""
        s = self.strategy()
        variables = [pool[n] for n in s.variables]
        return cartesian(variables, s.filters)

    def post_processor(self) -> Optional[PostProcessor]:
        return None

    def run(self, pool: Dict[str, Variable]) -> List[OutputFile]:
        """默认管线：一任务一模板。复杂插件可覆盖。"""
        template = Template.load(self.template_path())
        combos = self.build_combinations(pool)
        post = self.post_processor()

        results = []
        for combo in combos:
            text = render(template.content, combo)
            if post:
                text = post(text, combo)
            results.append((combo, text))

        return self.strategy().packer(template.path.name, results)