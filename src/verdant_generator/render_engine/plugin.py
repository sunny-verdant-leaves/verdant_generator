"""插件抽象：声明意图 + 生成替换列表 + 渲染 + 打包。

设计意图
--------
引擎不关心"变量怎么组合"、"模板用于什么场景"。
插件做三件事，其余全部走默认实现：

    1. 声明：name / template_path / replacements
    2. 可选干预：output_name_template / output_subdir /
                 post_processor / packer
    3. 执行：run()（默认管线，复杂插件可覆盖）

"组合"的职责完全在插件里。引擎不提供笛卡尔积、不做变量归一化，
因为真实场景里组合往往带依赖（如 modid 依赖 tree），
统一抽象反而会造成错配，让插件自己决定最干净。
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from .core import (
    Combination, OutputFile, Packer, PostProcessor, Template,
    pack_per_combination, render,
)


class Plugin(ABC):
    """渲染插件基类。

    子类必须实现：
        name            插件名（同时作为默认输出子目录）
        template_path   模板文件路径
        replacements    替换列表（每个元素是一次渲染的变量赋值）

    可选覆盖：
        description           描述
        output_name_template  输出文件名模板
        output_subdir         输出子目录
        post_processor        对每个渲染结果做后处理
        packer                如何把结果打包成 OutputFile 列表
        run                   整条管线（极少需要覆盖）
    """

    # ---------- 必须实现 ----------

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名。也是默认的输出子目录名。"""
        ...

    @abstractmethod
    def template_path(self) -> str:
        """模板文件的真实路径。

        这是磁盘上实际存在的文件，可能带占位符（如 "{tree}.json"），
        也可能不带（如 "material.json"）。
        """
        ...

    @abstractmethod
    def replacements(self) -> List[Combination]:
        """返回所有要渲染的组合。

        每个组合是一个 dict，如 {"tree": "minecraft:oak"}。
        怎么生成由插件自己决定：
            - 单变量循环
            - 一对一映射
            - 分组展开
            - 笛卡尔积（如果真需要）
        引擎不关心。
        """
        ...

    # ---------- 可选覆盖 ----------

    @property
    def description(self) -> str:
        """插件描述，显示在 UI 或日志里。"""
        return ""

    def output_name_template(self) -> str:
        """输出文件名模板。

        默认用模板文件自身的名字（template_path 的最后一段）。
        覆盖它可以实现"模板文件叫什么"和"输出文件名长什么样"解耦。

        示例：
            template_path = "templates/raw.json"
            output_name_template = "{tree}_{category}.json"
            → 输出文件 oak_chair.json / oak_table.json ...
        """
        return Path(self.template_path()).name

    def output_subdir(self) -> str:
        """输出子目录（相对于 base_output_dir）。默认用插件名。

        多个插件共用一个 base_output_dir 时，各写各的子目录，互不干扰。
        """
        return self.name

    def post_processor(self) -> Optional[PostProcessor]:
        """对每个渲染结果做后处理。

        返回 None 表示不做后处理。
        返回的函数签名是 (text, combo) -> text，
        可以访问当前组合，做"仅对某个材质生效"的替换。

        复杂后处理（需要跨文件、跨轮次的），不要塞这里——
        用多 Job 反刍，把上一轮输出作为下一轮输入。
        """
        return None

    def packer(self) -> Packer:
        """如何把 (combo, text) 列表打包成 OutputFile 列表。

        默认每个组合一个文件（pack_per_combination）。
        其他常见选择：
            - pack_merged：所有组合合并成一个文件
            - pack_grouped：按某个变量分组，每组一个文件
        """
        return pack_per_combination

    # ---------- 默认管线 ----------

    def run(self) -> List[OutputFile]:
        """默认管线：加载模板 → 逐组合渲染 → 后处理 → 打包。

        步骤：
            1. 从 template_path 读模板内容
            2. 从 replacements 拿组合列表
            3. 逐组合 render，内容里的 {name} 替换为 combo[name]
            4. 逐组合执行 post_processor（如果提供了）
            5. 用 packer 把结果打包成文件列表

        插件如果对整条管线有特殊需求（比如要先反刍一次），
        可以覆盖这个方法，但绝大多数插件不该覆盖。
        """
        template = Template.load(self.template_path())
        combos = self.replacements()
        post = self.post_processor()
        packer = self.packer()
        name_tpl = self.output_name_template()

        results = []
        for combo in combos:
            text = render(template.content, combo)
            if post:
                text = post(text, combo)
            results.append((combo, text))

        return packer(name_tpl, results)