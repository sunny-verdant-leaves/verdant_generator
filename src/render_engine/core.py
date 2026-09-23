"""核心引擎：数据 + 渲染 + 输出。

设计原则
--------
引擎只管三件与场景无关的事：
    1. 把 {name} 换成 combo[name]（render）
    2. 把渲染结果打包成 OutputFile 列表（pack_*）
    3. 保证文件名在 Windows / macOS / Linux 上都合法（safe_filename）

引擎不做的事（这些全在 Plugin 里）：
    - 不做变量归一化（Variable 已删）
    - 不做组合规则（cartesian 已删）
    - 不做派生值（modid / modid_safe 由插件给出）
    - 不做后处理编排（Plugin.post_processor 负责）

这样引擎的行为完全可预测：同样的 template + combo，
无论谁来调用，结果都一样。
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple


# 类型别名：让 Plugin / packer 的签名一目了然
Combination = Dict[str, str]
"""一个替换组合，如 {"tree": "minecraft:oak"}。"""

PostProcessor = Callable[[str, Combination], str]
"""后处理器签名：渲染结果 + 当前组合 → 新文本。

接受 combo 是为了支持"仅对某个材质生效"的替换，
比如 crimson 的 _log → _stem，其他材质不动。
"""

Packer = Callable[[str, List[Tuple[Combination, str]]], List["OutputFile"]]
"""打包器签名：文件名模板 + [(组合, 文本)] → 文件列表。

文件名模板由 Plugin.output_name_template() 提供，
不是模板文件自身的路径。
"""


# Windows 文件名非法字符：< > : " | ? *
# 同时排除控制字符（\x00-\x1f），因为文件系统在多个平台都拒绝
_ILLEGAL_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')


def safe_filename(name: str) -> str:
    """把渲染后的文件名变成合法文件名。

    只在"文件名"上做转换。内容永远不动——内容里的 : / _ 都是语义的一部分，
    比如 minecraft:oak_planks 是合法的命名空间 ID，不该被改。

    具体规则：
        - Windows 保留字符 → 下划线
        - / 保留：它表示子目录，packer 会据此创建嵌套目录
        - 每段末尾的空格和点去掉：Windows 不允许以它们结尾
        - 中文 / 其他 Unicode 字符不动：现代文件系统都支持

    示例：
        "minecraft:oak.json"    → "minecraft_oak.json"
        "sub/dir/file.txt"      → "sub/dir/file.txt"
        "file.  "               → "file"
        "橡木.json"             → "橡木.json"
    """
    result = _ILLEGAL_CHARS.sub("_", name)
    parts = [p.rstrip(" .") for p in result.split("/")]
    return "/".join(parts)


@dataclass
class Template:
    """纯文本模板：路径 + 内容。

    这里存路径是为了让 Plugin 能拿到文件名做默认输出名，
    不是为了再读一次——内容已经读进内存了。
    """

    path: Path
    content: str

    @classmethod
    def load(cls, path) -> "Template":
        p = Path(path)
        return cls(p, p.read_text(encoding="utf-8"))


@dataclass
class OutputFile:
    """一个待写入的文件。

    filename 可能是相对路径（含 /），writer 会据此创建子目录。
    content 是最终文本，writer 不再做任何转换。
    """

    filename: str
    content: str


# ---------- 渲染 ----------

# 只匹配合法的占位符名：字母或下划线开头，后跟字母/数字/下划线。
# 这样 {1abc} 或 {a-b} 不会被当成占位符，避免误替换模板里的其他花括号内容。
_PLACEHOLDER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def render(text: str, combo: Combination, strict: bool = False) -> str:
    """把 text 里的 {name} 替换为 combo[name]。

    只做占位符替换，不做任何字符转换。内容里的 : / _ 都原样保留。
    这意味着渲染后的文本可能带 Windows 文件名非法字符——
    safe_filename 会在打包阶段单独处理文件名，两者职责不重叠。

    strict=False（默认）：
        未匹配的占位符保留原样，便于排查"这个变量怎么没被替换"。
        生产环境慎用 strict=True，因为模板里可能故意留一些
        不属于当前组合的占位符（如 {category} 在 tree 场景下）。

    strict=True：
        有任何未匹配占位符就抛 KeyError，并列出所有缺失的 key。
        用于单测或对模板完整性要求高的场景。
    """
    missing = set()

    def repl(m):
        key = m.group(1)
        if key in combo:
            return combo[key]
        missing.add(key)
        return m.group(0)

    result = _PLACEHOLDER.sub(repl, text)
    if strict and missing:
        raise KeyError(f"未提供的占位符: {sorted(missing)}")
    return result


# ---------- 输出策略 ----------
#
# 三种 packer 的区别在"输出粒度"：
#   per_combination  每个组合一个文件     （配方 / 本地化默认）
#   merged           所有组合合并成一个   （生成汇总文件）
#   grouped          按某个变量分组       （按材质分组、按类别分组）
#
# 共同点：都对文件名做 safe_filename，不对内容做任何处理。


def pack_per_combination(template_name, results):
    """每个组合一个文件。

    template_name 是文件名模板（如 "{tree}.json"），
    用每个 combo 单独渲染一次，得到每个文件的最终名字。

    如果 template_name 不含占位符（如 "material.json"），
    所有组合会写成同一个文件，后写的覆盖前面的。
    ——这是设计如此，需要每组合一文件时请保证模板名带占位符。
    """
    return [
        OutputFile(safe_filename(render(template_name, c)), t)
        for c, t in results
    ]


def pack_merged(filename, results, joiner="\n"):
    """所有组合合并成一个文件。

    joiner 默认换行。JSON 场景常用 "\n" 拼多段 JSON，
    需要其他分隔符（如 ", "）时传入。
    """
    return [OutputFile(safe_filename(filename), joiner.join(t for _, t in results))]


def pack_grouped(group_by, name_template, results, joiner="\n"):
    """按 group_by 变量的值分组，每组一个文件。

    name_template 里的占位符从"该组第一个组合"取。
    这意味着同组内其他组合的变量值不会出现在文件名里——
    通常用于"按材质分组，组内不需要区分具体类别"的场景。

    group_by 键缺失时归入 "_default" 组，避免 None 当 key 报错。
    """
    groups: Dict[str, Tuple[Combination, List[str]]] = {}
    for combo, text in results:
        key = combo.get(group_by, "_default")
        groups.setdefault(key, (combo, []))[1].append(text)
    return [
        OutputFile(safe_filename(render(name_template, combo)), joiner.join(texts))
        for combo, texts in groups.values()
    ]