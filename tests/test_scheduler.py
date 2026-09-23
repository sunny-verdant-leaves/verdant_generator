"""测试调度器。"""
import json
from pathlib import Path

import pytest

from verdant_generator.render_engine import Plugin
from verdant_generator.scheduler import ScheduleReport, Scheduler


class StubPlugin(Plugin):
    _next_name = "stub"

    def __init__(self, template_path, combos=None, subdir=None):
        self._template_path = template_path
        self._combos = combos or [{"x": "a"}]
        self._subdir = subdir

    @property
    def name(self):
        return self._next_name

    def template_path(self):
        return self._template_path

    def replacements(self):
        return self._combos

    def output_subdir(self):
        return self._subdir or self.name


class BoomPlugin(Plugin):
    @property
    def name(self):
        return "boom"

    def template_path(self):
        return "no_such_template.txt"

    def replacements(self):
        return [{}]


class TestScheduleReport:
    def test_empty(self):
        r = ScheduleReport()
        assert r.total_written == 0
        assert not r.has_failure


class TestScheduler:
    def _tpl(self, tmp_path, name, content):
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_single_plugin(self, tmp_path):
        tpl = self._tpl(tmp_path, "{x}.txt", "val={x}")
        plugin = StubPlugin(
            template_path=str(tpl),
            combos=[{"x": "a"}, {"x": "b"}],
            subdir="out",
        )
        out_dir = tmp_path / "output"

        report = Scheduler(out_dir).run({"plugins": [plugin]})

        assert not report.has_failure
        assert report.total_written == 2
        assert (out_dir / "out" / "a.txt").read_text(encoding="utf-8") == "val=a"

    def test_error_isolated(self, tmp_path):
        tpl = self._tpl(tmp_path, "{x}.txt", "{x}")
        good = StubPlugin(template_path=str(tpl), combos=[{"x": "a"}])
        bad = BoomPlugin()

        report = Scheduler(tmp_path / "output").run({"plugins": [bad, good]})

        assert report.has_failure
        assert len(report.errors) == 1
        assert report.errors[0][0] == "boom"
        assert report.total_written == 1

    def test_dry_run(self, tmp_path):
        tpl = self._tpl(tmp_path, "{x}.txt", "{x}")
        plugin = StubPlugin(template_path=str(tpl))
        out_dir = tmp_path / "output"

        report = Scheduler(out_dir, dry_run=True).run({"plugins": [plugin]})

        assert report.total_written == 1
        assert not out_dir.exists()

    def test_empty_plugins(self, tmp_path):
        report = Scheduler(tmp_path / "output").run({"plugins": []})
        assert report.total_written == 0
        assert not report.has_failure

    def test_run_config_file(self, tmp_path):
        tpl = self._tpl(tmp_path, "{tree}.txt", "{tree}")
        config = {
            "plugins": [
                {
                    "type": "recipe_generator",
                    "template": str(tpl).replace("\\", "/"),
                    "trees": ["a", "b"],
                },
            ],
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        out_dir = tmp_path / "output"

        report = Scheduler(out_dir).run_config_file(config_path)

        assert not report.has_failure, report.errors
        assert report.total_written == 2
        assert (out_dir / "recipe_generator" / "a.txt").exists()