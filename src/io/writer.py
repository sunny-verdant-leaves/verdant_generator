"""文件写入：把 OutputFile 列表落到磁盘。

设计原则：
    - 单个文件失败不影响其他文件（记录到 report）
    - 支持 dry_run（只返回路径，不真写）
    - 自动创建子目录（文件名里带 / 时）
    - UTF-8 编码
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

from src.render_engine import OutputFile


@dataclass
class WriteReport:
    """一次写入的结果。"""
    written: List[Path] = field(default_factory=list)
    failed: List[Tuple[OutputFile, str]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.written) + len(self.failed)

    @property
    def has_failure(self) -> bool:
        return len(self.failed) > 0


def write_outputs(
    outputs: List[OutputFile],
    output_dir,
    dry_run: bool = False,
    encoding: str = "utf-8",
) -> WriteReport:
    """把一批 OutputFile 写入 output_dir。

    :param outputs:    待写文件列表
    :param output_dir: 目标目录（不存在会自动创建）
    :param dry_run:    True 时只算路径，不真写
    :param encoding:   文件编码
    :return:           WriteReport
    """
    report = WriteReport()
    base = Path(output_dir)

    if not dry_run:
        try:
            base.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # 整个目录建不了，全部记为失败
            for f in outputs:
                report.failed.append((f, f"无法创建输出目录: {e}"))
            return report

    for output in outputs:
        target = base / output.filename

        if dry_run:
            report.written.append(target)
            continue

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(output.content, encoding=encoding)
            report.written.append(target)
        except OSError as e:
            report.failed.append((output, str(e)))

    return report