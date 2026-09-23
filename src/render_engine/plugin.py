"""插件抽象：声明意图 + 生成替换列表 + 渲染 + 打包。"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .core import (
    Combination, OutputFile, Packer, PostProcessor, Template,
    pack_per_combination, render,
)


class Plugin(ABC):
    """渲染插件基类。

    子类必须声明：
        name           插件名
        template_path  用哪个模板
        replacements   替换列表（每个元素是一次渲染的变量赋值）
    可选覆盖：
        description      描述
        output_subdir    输出子目录（默认 = name）
        post_processor   后处理
        packer           打包函数（默认 pack_per_combination）
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
    def replacements(self) -> List[Combination]:
        """返回所有要渲染的组合。

        每个组合是一个 dict，如 {"tree": "minecraft:oak"}。
        由插件自己决定怎么生成——单变量循环、一对一映射、笛卡尔积
        都行，引擎不关心。
        """
        ...

    def output_subdir(self) -> str:
        """输出子目录（相对于 base_output_dir）。默认用插件名。"""
        return self.name

    def post_processor(self) -> Optional[PostProcessor]:
        return None

    def packer(self) -> Packer:
        return pack_per_combination

    def run(self) -> List[OutputFile]:
        """默认管线：加载模板 → 逐组合渲染 → 打包。"""
        template = Template.load(self.template_path())
        combos = self.replacements()
        post = self.post_processor()
        packer = self.packer()

        results = []
        for combo in combos:
            text = render(template.content, combo)
            if post:
                text = post(text, combo)
            results.append((combo, text))

        return packer(template.path.name, results)