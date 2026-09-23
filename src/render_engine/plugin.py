"""插件抽象：声明意图 + 可选覆盖。"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .core import OutputFile, PostProcessor, Strategy, Template, Variable, run


class Plugin(ABC):
    """渲染插件基类。

    子类必须声明 name / template_path / strategy_name。
    可选覆盖 description / post_processor / run。
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
        """使用哪个模板文件。"""
        ...

    @abstractmethod
    def strategy_name(self) -> str:
        """使用哪个 Strategy。"""
        ...

    def post_processor(self) -> Optional[PostProcessor]:
        """可选：对每个渲染结果做后处理。"""
        return None

    def run(
        self,
        pool: Dict[str, Variable],
        strategies: Dict[str, Strategy],
    ) -> List[OutputFile]:
        """默认管线：一任务一模板。复杂插件可覆盖。"""
        template = Template.load(self.template_path())
        strategy = strategies[self.strategy_name()]
        return run(template, pool, strategy, self.post_processor())