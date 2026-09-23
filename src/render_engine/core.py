"""核心引擎：数据 + 渲染 + 输出。

已砍掉：
    - Variable 类（变量由插件自己管理）
    - Strategy 类（packer 由插件直接提供）
    - cartesian() 函数（组合由插件自己生成）
    - run() 函数（管线并入 Plugin.run）
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple


Combination = Dict[str, str]
PostProcessor = Callable[[str, Combination], str]
Packer = Callable[[str, List[Tuple[Combination, str]]], List["OutputFile"]]


# Windows 文件名非法字符
_ILLEGAL_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')


def safe_filename(name: str) -> str:
    """把渲染后的文件名变成合法文件名。

    - 替换 Windows 保留字符为下划线
    - 保留 / （表示子目录）
    - 去掉每段末尾的空格和点
    """
    result = _ILLEGAL_CHARS.sub("_", name)
    parts = [p.rstrip(" .") for p in result.split("/")]
    return "/".join(parts)


@dataclass
class Template:
    path: Path
    content: str

    @classmethod
    def load(cls, path) -> "Template":
        p = Path(path)
        return cls(p, p.read_text(encoding="utf-8"))


@dataclass
class OutputFile:
    filename: str
    content: str


# ---------- 渲染 ----------
_PLACEHOLDER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def render(text: str, combo: Combination, strict: bool = False) -> str:
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
def pack_per_combination(template_name, results):
    """每个组合一个文件。"""
    return [
        OutputFile(safe_filename(render(template_name, c)), t)
        for c, t in results
    ]


def pack_merged(filename, results, joiner="\n"):
    """所有组合合并成一个文件。"""
    return [OutputFile(safe_filename(filename), joiner.join(t for _, t in results))]


def pack_grouped(group_by, name_template, results, joiner="\n"):
    """按某个变量分组，每组一个文件。"""
    groups: Dict[str, Tuple[Combination, List[str]]] = {}
    for combo, text in results:
        key = combo.get(group_by, "_default")
        groups.setdefault(key, (combo, []))[1].append(text)
    return [
        OutputFile(safe_filename(render(name_template, combo)), joiner.join(texts))
        for combo, texts in groups.values()
    ]