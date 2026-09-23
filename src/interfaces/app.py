"""UI 入口：持有根容器，负责页面切换。"""
import flet as ft


class App:
    def __init__(self, page: ft.Page):
        self.page = page
        self.config_path = "config.json"
        self.output_dir = "./output"

        self.container = ft.Container(expand=True)
        page.add(self.container)
        self.show_home()

    # ---------- 页面切换 ----------

    def show_home(self):
        from .home_page import HomePage
        self.container.content = HomePage(
            page=self.page,
            config_path=self.config_path,
            output_dir=self.output_dir,
            on_open_task=self.show_task,
            on_open_settings=self.show_settings,
            on_config_changed=self._on_config_changed,
        ).build()
        self.page.update()

    def show_task(self, plugin):
        from .task_page import TaskPage
        self.container.content = TaskPage(
            page=self.page,
            plugin=plugin,
            output_dir=self.output_dir,
            on_back=self.show_home,
        ).build()
        self.page.update()

    def show_settings(self):
        from .settings_page import SettingsPage
        self.container.content = SettingsPage(
            page=self.page,
            config_path=self.config_path,
            output_dir=self.output_dir,
            on_back=self.show_home,
            on_config_changed=self._on_config_changed,
        ).build()
        self.page.update()

    # ---------- 回调 ----------

    def _on_config_changed(self, config_path: str, output_dir: str):
        self.config_path = config_path
        self.output_dir = output_dir


def run():
    def main(page: ft.Page):
        page.title = "Recipe Generator"
        page.window.width = 900
        page.window.height = 700
        page.window.min_width = 640
        page.window.min_height = 480
        App(page)

    ft.app(target=main)