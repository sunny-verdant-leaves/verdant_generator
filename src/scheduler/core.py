"""调度器：读配置 → 跑插件 → 写文件。

设计原则：
    - 单个插件失败不影响其他插件（记到 report.errors）
    - 每个插件输出到 base_output_dir / plugin.output_subdir()
    - dry_run 传给 writer
    - 变量池兼容两种输入：Variable 对象 或 裸 list
"""
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

from src.config import load_config
from src.io import WriteReport, write_outputs
from src.render_engine import Variable


@dataclass
class ScheduleReport:
    """一次调度执行的结果。"""
    plugin_reports: Dict[str, WriteReport] = field(default_factory=dict)
    errors: List[Tuple[str, str]] = field(default_factory=list)  # (plugin_name, msg)

    @property
    def total_written(self) -> int:
        return sum(len(r.written) for r in self.plugin_reports.values())

    @property
    def total_failed(self) -> int:
        failed_files = sum(len(r.failed) for r in self.plugin_reports.values())
        return failed_files + len(self.errors)

    @property
    def has_failure(self) -> bool:
        return bool(self.errors) or any(
            r.has_failure for r in self.plugin_reports.values()
        )


class Scheduler:
    """把一个 config 里的所有插件按顺序执行，输出到指定目录。"""

    def __init__(self, base_output_dir, dry_run: bool = False):
        self.base_output_dir = Path(base_output_dir)
        self.dry_run = dry_run

    def run_config_file(self, config_path) -> ScheduleReport:
        """从 JSON 配置文件加载并执行。"""
        config = load_config(str(config_path))
        return self.run(config)

    def run(self, config: dict) -> ScheduleReport:
        """执行已加载的配置。

        :param config: 形如 {"variables": ..., "strategies": ..., "plugins": ...}
        """
        report = ScheduleReport()
        pool = self._normalize_variables(config.get("variables", {}))

        for plugin in config.get("plugins", []):
            name = plugin.name
            try:
                outputs = plugin.run(pool)
                out_dir = self.base_output_dir / plugin.output_subdir()
                report.plugin_reports[name] = write_outputs(
                    outputs, out_dir, dry_run=self.dry_run
                )
            except Exception as e:
                tb = traceback.format_exc()
                report.errors.append((name, f"{e}\n{tb}"))

        return report

    @staticmethod
    def _normalize_variables(pool: dict) -> Dict[str, Variable]:
        """兼容两种输入：Variable 对象 / 裸 list。"""
        result = {}
        for name, val in pool.items():
            if isinstance(val, Variable):
                result[name] = val
            elif isinstance(val, (list, tuple)):
                result[name] = Variable(name, list(val))
            else:
                raise TypeError(
                    f"变量 '{name}' 必须是 Variable 或 list/tuple，"
                    f"得到 {type(val).__name__}"
                )
        return result