"""调度器：读配置 → 跑插件 → 写文件。"""
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

from verdant_generator.config import load_config
from verdant_generator.io import WriteReport, write_outputs


@dataclass
class ScheduleReport:
    plugin_reports: Dict[str, WriteReport] = field(default_factory=dict)
    errors: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def total_written(self) -> int:
        return sum(len(r.written) for r in self.plugin_reports.values())

    @property
    def total_failed(self) -> int:
        failed = sum(len(r.failed) for r in self.plugin_reports.values())
        return failed + len(self.errors)

    @property
    def has_failure(self) -> bool:
        return bool(self.errors) or any(
            r.has_failure for r in self.plugin_reports.values()
        )


class Scheduler:
    def __init__(self, base_output_dir, dry_run: bool = False):
        self.base_output_dir = Path(base_output_dir)
        self.dry_run = dry_run

    def run_config_file(self, config_path) -> ScheduleReport:
        return self.run(load_config(str(config_path)))

    def run(self, config: dict) -> ScheduleReport:
        report = ScheduleReport()
        for plugin in config.get("plugins", []):
            name = plugin.name
            try:
                outputs = plugin.run()
                out_dir = self.base_output_dir / plugin.output_subdir()
                report.plugin_reports[name] = write_outputs(
                    outputs, out_dir, dry_run=self.dry_run
                )
            except Exception as e:
                report.errors.append((name, f"{e}\n{traceback.format_exc()}"))
        return report