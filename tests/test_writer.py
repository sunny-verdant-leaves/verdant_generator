"""测试文件写入。"""
from pathlib import Path

import pytest

from verdant_generator.io import WriteReport, write_outputs
from verdant_generator.render_engine import OutputFile


class TestWriteOutputs:
    def test_writes_single_file(self, tmp_path: Path):
        outputs = [OutputFile("a.txt", "hello")]
        report = write_outputs(outputs, tmp_path)

        assert report.total == 1
        assert not report.has_failure
        assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "hello"

    def test_writes_multiple_files(self, tmp_path: Path):
        outputs = [
            OutputFile("a.txt", "A"),
            OutputFile("b.txt", "B"),
            OutputFile("c.txt", "C"),
        ]
        report = write_outputs(outputs, tmp_path)

        assert report.total == 3
        assert not report.has_failure
        assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "A"
        assert (tmp_path / "b.txt").read_text(encoding="utf-8") == "B"
        assert (tmp_path / "c.txt").read_text(encoding="utf-8") == "C"

    def test_creates_output_dir(self, tmp_path: Path):
        target = tmp_path / "nested" / "deep"
        outputs = [OutputFile("x.txt", "X")]
        report = write_outputs(outputs, target)

        assert not report.has_failure
        assert (target / "x.txt").read_text(encoding="utf-8") == "X"

    def test_creates_subdirs_from_filename(self, tmp_path: Path):
        """文件名里带 / 时，自动创建子目录。"""
        outputs = [OutputFile("sub/dir/file.txt", "content")]
        report = write_outputs(outputs, tmp_path)

        assert not report.has_failure
        target = tmp_path / "sub" / "dir" / "file.txt"
        assert target.read_text(encoding="utf-8") == "content"

    def test_utf8_chinese_content(self, tmp_path: Path):
        outputs = [OutputFile("zh.txt", "橡木桌子")]
        report = write_outputs(outputs, tmp_path)

        assert not report.has_failure
        assert (tmp_path / "zh.txt").read_text(encoding="utf-8") == "橡木桌子"

    def test_overwrites_existing(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("old", encoding="utf-8")
        outputs = [OutputFile("a.txt", "new")]
        report = write_outputs(outputs, tmp_path)

        assert not report.has_failure
        assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "new"

    def test_empty_list(self, tmp_path: Path):
        report = write_outputs([], tmp_path)
        assert report.total == 0
        assert not report.has_failure

    def test_dry_run_does_not_write(self, tmp_path: Path):
        outputs = [OutputFile("a.txt", "content")]
        report = write_outputs(outputs, tmp_path, dry_run=True)

        assert report.total == 1
        assert not report.has_failure
        # 路径被记录，但文件没真的写
        assert len(report.written) == 1
        assert report.written[0] == tmp_path / "a.txt"
        assert not (tmp_path / "a.txt").exists()

    def test_dry_run_does_not_create_dir(self, tmp_path: Path):
        target = tmp_path / "not_created"
        outputs = [OutputFile("a.txt", "x")]
        write_outputs(outputs, target, dry_run=True)
        assert not target.exists()

    def test_report_paths_are_absolute(self, tmp_path: Path):
        outputs = [OutputFile("a.txt", "x")]
        report = write_outputs(outputs, tmp_path)
        assert report.written[0].is_absolute()


class TestWriteReport:
    def test_total(self):
        from pathlib import Path
        r = WriteReport()
        r.written = [Path("a"), Path("b")]
        r.failed = [(OutputFile("c", ""), "err")]
        assert r.total == 3

    def test_has_failure_false(self):
        r = WriteReport()
        r.written = [Path("a")]
        assert not r.has_failure

    def test_has_failure_true(self):
        r = WriteReport()
        r.failed = [(OutputFile("c", ""), "err")]
        assert r.has_failure