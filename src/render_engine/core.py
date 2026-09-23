"""核心引擎：数据 + 组合 + 渲染 + 输出 + 管线。"""
import itertools
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

Combination = Dict[str, str]
PostProcessor = Callable[[str, Combination], str]
Packer = Callable[[str, List[Tuple[Combination, str]]], List["OutputFile"]]


@dataclass(frozen=True)
class Variable:
    name: str
    values: List[str]


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


@dataclass
class Strategy:
    """一个生成策略：用哪些变量 + 怎么打包输出。"""
    variables: List[str]
    packer: Packer


# ---------- 组合 ----------
def cartesian(variables: List[Variable]) -> List[Combination]:
    if not variables:
        return [{}]
    names = [v.name for v in variables]
    value_lists = [v.values for v in variables]
    return [dict(zip(names, vs)) for vs in itertools.product(*value_lists)]


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
    return [OutputFile(render(template_name, c), t) for c, t in results]


def pack_merged(filename, results, joiner="\n"):
    """所有组合合并成一个文件。"""
    return [OutputFile(filename, joiner.join(t for _, t in results))]


def pack_grouped(group_by, name_template, results, joiner="\n"):
    """按某个变量分组，每组一个文件。"""
    groups: Dict[str, Tuple[Combination, List[str]]] = {}
    for combo, text in results:
        key = combo.get(group_by, "_default")
        groups.setdefault(key, (combo, []))[1].append(text)
    return [
        OutputFile(render(name_template, combo), joiner.join(texts))
        for combo, texts in groups.values()
    ]


# ---------- 管线 ----------
def run(
    template: Template,
    pool: Dict[str, Variable],
    strategy: Strategy,
    post: Optional[PostProcessor] = None,
) -> List[OutputFile]:
    """一任务一模板：模板 + 变量池 + 策略 → 一批 OutputFile。"""
    variables = [pool[n] for n in strategy.variables]
    combos = cartesian(variables)

    results = []
    for combo in combos:
        text = render(template.content, combo)
        if post:
            text = post(text, combo)
        results.append((combo, text))

    return strategy.packer(template.path.name, results)