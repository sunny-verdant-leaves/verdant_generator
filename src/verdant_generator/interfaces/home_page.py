"""任务列表页：显示所有插件，点击进入执行页。"""
import flet as ft
from pathlib import Path

from verdant_generator.config import load_config


class HomePage:
    def __init__(
        self,
        page: ft.Page,
        config_path: str,
        output_dir: str,
        on_open_task,
        on_open_settings,
        on_config_changed,
    ):
        self.page = page
        self.config_path = config_path
        self.output_dir = output_dir
        self.on_open_task = on_open_task
        self.on_open_settings = on_open_settings
        self.on_config_changed = on_config_changed

        self.status_text = ft.Text("", size=12, color=ft.colors.GREY_600)
        self.plugin_list = ft.Column(
            spacing=10, scroll=ft.ScrollMode.AUTO, expand=True
        )

    def build(self) -> ft.Control:
        self._reload_plugins()

        return ft.Container(
            content=ft.Column([
                self._build_header(),
                ft.Divider(),
                self.plugin_list,
                self.status_text,
            ], expand=True, spacing=10),
            padding=20,
            expand=True,
        )

    # ---------- 组件 ----------

    def _build_header(self) -> ft.Control:
        config_field = ft.TextField(
            label="配置文件",
            value=self.config_path,
            expand=True,
            dense=True,
            text_size=13,
        )

        def on_pick(e):
            def on_result(ev: ft.FilePickerResultEvent):
                if ev.files and len(ev.files) > 0:
                    config_field.value = ev.files[0].path
                    self._apply_config_change(config_field.value)

            picker = ft.FilePicker(on_result=on_result)
            self.page.overlay.append(picker)
            self.page.update()
            picker.pick_files(
                dialog_title="选择配置文件",
                allowed_extensions=["json"],
                file_type=ft.FilePickerFileType.CUSTOM,
            )

        def on_reload(e):
            self._apply_config_change(config_field.value)

        return ft.Column([
            ft.Text("📋 任务列表", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([
                config_field,
                ft.IconButton(
                    icon=ft.icons.FOLDER_OPEN,
                    tooltip="浏览",
                    on_click=on_pick,
                ),
                ft.ElevatedButton(
                    "重新加载",
                    icon=ft.icons.REFRESH,
                    on_click=on_reload,
                ),
                ft.IconButton(
                    icon=ft.icons.SETTINGS,
                    tooltip="设置",
                    on_click=lambda e: self.on_open_settings(),
                ),
            ], spacing=5),
        ], spacing=10)

    def _build_plugin_card(self, plugin) -> ft.Control:
        try:
            combo_count = len(plugin.replacements())
        except Exception:
            combo_count = "?"

        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        f"📦 {plugin.name}",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        plugin.description or "(无描述)",
                        size=12,
                        color=ft.colors.GREY_600,
                    ),
                    ft.Text(
                        f"组合数: {combo_count} | 输出: "
                        f"{self.output_dir}/{plugin.output_subdir()}",
                        size=11,
                        color=ft.colors.GREY_500,
                    ),
                ], expand=True, spacing=3),
                ft.ElevatedButton(
                    "▶ 执行",
                    on_click=lambda e, p=plugin: self.on_open_task(p),
                ),
            ], spacing=10),
            padding=15,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=8,
        )

    # ---------- 逻辑 ----------

    def _reload_plugins(self):
        self.plugin_list.controls.clear()

        path = Path(self.config_path)
        if not path.exists():
            self.plugin_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        f"⚠️ 配置文件不存在: {path.absolute()}",
                        color=ft.colors.ORANGE_700,
                    ),
                    padding=20,
                )
            )
            self.status_text.value = "请选择有效的配置文件"
            self.status_text.color = ft.colors.ORANGE_700
            return

        try:
            config = load_config(str(path))
        except Exception as ex:
            self.plugin_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        f"❌ 加载失败: {ex}",
                        color=ft.colors.RED_700,
                    ),
                    padding=20,
                )
            )
            self.status_text.value = "配置加载失败"
            self.status_text.color = ft.colors.RED_700
            return

        plugins = config.get("plugins", [])
        if not plugins:
            self.plugin_list.controls.append(
                ft.Container(
                    content=ft.Text("配置里没有任何插件", color=ft.colors.GREY_600),
                    padding=20,
                )
            )
        else:
            for plugin in plugins:
                self.plugin_list.controls.append(self._build_plugin_card(plugin))

        self.status_text.value = f"✅ 已加载 {len(plugins)} 个插件"
        self.status_text.color = ft.colors.GREEN_700

    def _apply_config_change(self, new_path: str):
        self.config_path = new_path
        self.on_config_changed(new_path, self.output_dir)
        self._reload_plugins()
        self.page.update()