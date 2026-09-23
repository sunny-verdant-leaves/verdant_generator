"""任务执行页：显示插件信息、执行、日志、统计。"""
import subprocess
import sys
import threading
from pathlib import Path

import flet as ft

from verdant_generator.io import write_outputs


class TaskPage:
    def __init__(self, page: ft.Page, plugin, output_dir: str, on_back):
        self.page = page
        self.plugin = plugin
        self.output_dir = output_dir
        self.on_back = on_back

        self.dry_run_checkbox = ft.Checkbox(
            label="预览模式（不写入文件）", value=False
        )
        self.run_btn = ft.ElevatedButton(
            "🚀 执行",
            icon=ft.icons.PLAY_ARROW,
            on_click=self._handle_run,
            disabled=False,
        )
        self.open_btn = ft.ElevatedButton(
            "📁 打开输出目录",
            icon=ft.icons.FOLDER_OPEN,
            on_click=self._handle_open_output,
        )
        self.log_view = ft.ListView(
            expand=True,
            spacing=3,
            padding=10,
            auto_scroll=True,
        )
        self.stats_text = ft.Text(
            "尚未执行",
            size=13,
            weight=ft.FontWeight.BOLD,
        )

    def build(self) -> ft.Control:
        try:
            combo_count = len(self.plugin.replacements())
        except Exception as ex:
            combo_count = f"计算失败: {ex}"

        return ft.Container(
            content=ft.Column([
                self._build_header(),
                ft.Divider(),
                self._build_info(combo_count),
                self._build_controls(),
                ft.Divider(),
                ft.Text("日志", size=14, weight=ft.FontWeight.W_500),
                ft.Container(
                    content=self.log_view,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=6,
                    expand=True,
                ),
                self._build_stats(),
            ], expand=True, spacing=10),
            padding=20,
            expand=True,
        )

    # ---------- 组件 ----------

    def _build_header(self):
        return ft.Row([
            ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                tooltip="返回",
                on_click=lambda e: self.on_back(),
            ),
            ft.Text(
                f"📦 {self.plugin.name}",
                size=22,
                weight=ft.FontWeight.BOLD,
                expand=True,
            ),
        ])

    def _build_info(self, combo_count):
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    self.plugin.description or "(无描述)",
                    size=13,
                    color=ft.colors.GREY_700,
                ),
                ft.Text(
                    f"输出目录: {self.output_dir}/{self.plugin.output_subdir()}",
                    size=12,
                    color=ft.colors.GREY_600,
                ),
                ft.Text(
                    f"组合数: {combo_count}",
                    size=12,
                    color=ft.colors.GREY_600,
                ),
            ], spacing=3),
            padding=10,
            bgcolor=ft.colors.GREY_100,
            border_radius=6,
        )

    def _build_controls(self):
        return ft.Row([
            self.dry_run_checkbox,
            self.run_btn,
            self.open_btn,
        ], spacing=15)

    def _build_stats(self):
        return ft.Container(
            content=self.stats_text,
            padding=10,
            bgcolor=ft.colors.BLUE_50,
            border_radius=6,
        )

    # ---------- 事件 ----------

    def _log(self, message: str, color=None):
        self.log_view.controls.append(ft.Text(message, size=12, color=color))
        self.log_view.update()

    def _handle_run(self, e):
        dry_run = self.dry_run_checkbox.value
        self.run_btn.disabled = True
        self.page.update()

        self.log_view.controls.clear()
        self.log_view.update()

        threading.Thread(
            target=self._run_in_background,
            args=(dry_run,),
            daemon=True,
        ).start()

    def _run_in_background(self, dry_run: bool):
        try:
            self._log(f"⏳ 开始执行 {self.plugin.name}...")
            if dry_run:
                self._log("👁️  预览模式（不会写入文件）")

            outputs = self.plugin.run()
            self._log(f"  生成 {len(outputs)} 个 OutputFile")

            out_dir = Path(self.output_dir) / self.plugin.output_subdir()
            report = write_outputs(outputs, out_dir, dry_run=dry_run)

            for path in report.written:
                self._log(f"  {'[预览] ' if dry_run else ''}{path.name}")
            for failed_file, msg in report.failed:
                self._log(
                    f"  ❌ {failed_file.filename}: {msg}",
                    ft.colors.RED_600,
                )

            self.stats_text.value = (
                f"✅ 写入 {len(report.written)} | 失败 {len(report.failed)}"
            )
            self.stats_text.color = (
                ft.colors.GREEN_700 if not report.has_failure
                else ft.colors.RED_700
            )
            self._log("\n🎉 完成", ft.colors.GREEN_700)

        except Exception as ex:
            import traceback
            self._log(f"❌ 执行失败: {ex}", ft.colors.RED_600)
            self._log(traceback.format_exc(), ft.colors.RED_400)
            self.stats_text.value = f"❌ 失败: {ex}"
            self.stats_text.color = ft.colors.RED_700

        finally:
            self.run_btn.disabled = False
            self.page.update()

    def _handle_open_output(self, e):
        out_dir = Path(self.output_dir) / self.plugin.output_subdir()
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", str(out_dir.absolute())])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(out_dir.absolute())])
            else:
                subprocess.Popen(["xdg-open", str(out_dir.absolute())])
        except Exception as ex:
            self._log(f"❌ 无法打开目录: {ex}", ft.colors.RED_600)