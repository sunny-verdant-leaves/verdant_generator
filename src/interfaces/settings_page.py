"""设置页：显示配置内容和输出目录，先做只读版。"""
import json
from pathlib import Path

import flet as ft


class SettingsPage:
    def __init__(
        self,
        page: ft.Page,
        config_path: str,
        output_dir: str,
        on_back,
        on_config_changed,
    ):
        self.page = page
        self.config_path = config_path
        self.output_dir = output_dir
        self.on_back = on_back
        self.on_config_changed = on_config_changed

    def build(self) -> ft.Control:
        return ft.Container(
            content=ft.Column([
                self._build_header(),
                ft.Divider(),
                self._build_config_info(),
                ft.Divider(),
                ft.Text("原始配置内容", size=14, weight=ft.FontWeight.W_500),
                ft.Container(
                    content=ft.TextField(
                        value=self._read_config(),
                        multiline=True,
                        read_only=True,
                        text_size=12,
                        expand=True,
                        min_lines=15,
                    ),
                    expand=True,
                ),
            ], expand=True, spacing=10),
            padding=20,
            expand=True,
        )

    def _build_header(self):
        return ft.Row([
            ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                tooltip="返回",
                on_click=lambda e: self.on_back(),
            ),
            ft.Text("⚙️ 设置", size=22, weight=ft.FontWeight.BOLD),
        ])

    def _build_config_info(self):
        return ft.Column([
            ft.Text(
                f"配置文件: {self.config_path}",
                size=12,
                color=ft.colors.GREY_700,
            ),
            ft.Text(
                f"输出目录: {self.output_dir}",
                size=12,
                color=ft.colors.GREY_700,
            ),
            ft.Text(
                "（编辑功能开发中，当前仅显示）",
                size=11,
                color=ft.colors.ORANGE_600,
                italic=True,
            ),
        ], spacing=3)

    def _read_config(self) -> str:
        path = Path(self.config_path)
        if not path.exists():
            return f"// 配置文件不存在: {path.absolute()}"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as ex:
            return f"// 读取失败: {ex}"