import flet as ft
from pathlib import Path
from src.interfaces.base_page import BasePage
from src.service.recipe_service import RecipeService
from typing import Optional, List, Dict, Any


class GeneratorPage(BasePage):
    """
    GeneratorPage - 生成器页（内部绑定事件）
    职责：UI展示 + 直接调用RecipeService
    """
    
    def __init__(self, router, page: ft.Page, recipe_service: RecipeService):
        super().__init__(router, page)
        self.recipe_service = recipe_service  # 重命名，更清晰
        
        # 设置回调（保持不变）
        self.recipe_service.set_callbacks(
            on_progress=self._on_progress,
            on_complete=self._on_complete,
            on_error=self._on_error
        )
    
    def build(self) -> ft.Control:
        """构建UI并直接绑定事件"""
        # 加载配置按钮（可选：从SettingsService同步配置）
        load_btn = self.add_component(
            "load_config_btn",
            ft.ElevatedButton(
                "🔄 同步配置",
                icon=ft.icons.SYNC,
                on_click=self._handle_load_config
            )
        )
        
        # 控制面板
        dry_run_checkbox = self.add_component(
            "dry_run_checkbox",
            ft.Checkbox(label="预览模式", value=True)
        )
        
        explain_checkbox = self.add_component(
            "explain_checkbox",
            ft.Checkbox(label="解释模式", value=False)
        )
        
        generate_btn = self.add_component(
            "generate_btn",
            ft.ElevatedButton(
                "🚀 开始生成",
                expand=True,
                on_click=self._handle_generate
            )
        )
        
        cancel_btn = self.add_component(
            "cancel_btn",
            ft.ElevatedButton(
                "🛑 取消",
                expand=True,
                disabled=True
            )
        )
        
        open_btn = self.add_component(
            "open_btn",
            ft.ElevatedButton(
                "📁 打开输出目录",
                expand=True,
                on_click=self._handle_open_output_dir
            )
        )
        
        # 日志区域
        log_view = self.add_component(
            "log_view",
            ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=True)
        )
        
        # 统计区域
        stats_container = self.add_component(
            "stats_container",
            ft.Container(
                content=ft.Text("总数: 0 个文件", size=14, weight=ft.FontWeight.BOLD),
                padding=10,
                bgcolor="#DDDDEE",
                border_radius=5,
            )
        )
        
        # 布局组装
        control_panel = ft.Container(
            content=ft.Column([
                ft.Text("⚙️ 配方生成器", size=24, weight=ft.FontWeight.BOLD),
                load_btn,
                ft.Row([dry_run_checkbox, explain_checkbox], spacing=20),
                ft.Row([generate_btn, cancel_btn, open_btn], spacing=10),
            ], spacing=15),
            padding=20,
            bgcolor="#DDDDEE",
            height=250,
        )
        
        return ft.Column([
            control_panel,
            log_view,
            stats_container,
        ], expand=True, spacing=10)
    
    # ==================== 事件处理器 ====================
    
    def _handle_load_config(self, e: ft.ControlEvent):
        """同步配置按钮点击 - 现在只需一行"""
        success = self.recipe_service.reload_config()
        
        if success:
            template_count = len(self.recipe_service.config.template_files)
            self.log_message(f"✅ 配置已同步，加载了 {template_count} 个模板")
        else:
            self.log_message("⚠️ 请先在设置页配置模板", is_error=True)
    
    def _handle_generate(self, e: ft.ControlEvent):
        """生成按钮点击"""
        # 获取参数
        dry_run = self.get_component("dry_run_checkbox").value
        explain_mode = self.get_component("explain_checkbox").value
        
        # 禁用按钮
        generate_btn = self.get_component("generate_btn")
        generate_btn.disabled = True
        cancel_btn = self.get_component("cancel_btn")
        cancel_btn.disabled = False
        self.page.update()
        
        # 清空日志
        log_view = self.get_component("log_view")
        log_view.controls.clear()
        
        # 启动生成
        success = self.recipe_service.start_generation(dry_run=dry_run, explain_mode=explain_mode)
        
        if not success:
            self.log_message("❌ 启动失败，请检查配置", is_error=True)
            generate_btn.disabled = False
            cancel_btn.disabled = True
            self.page.update()
    
    def _handle_open_output_dir(self, e: ft.ControlEvent):
        """打开输出目录"""
        try:
            output_dir = Path(self.recipe_service.get_output_directory())
            if output_dir.exists():
                import subprocess
                subprocess.Popen(f'explorer "{output_dir.absolute()}"')
                self.log_message("📂 已打开目录", is_info=True)
            else:
                self.log_message("⚠️ 输出目录不存在", is_warning=True)
        except Exception as ex:
            self.log_message(f"❌ 无法打开目录: {ex}", is_error=True)
    
    # ==================== Service回调 ====================
    
    def _on_progress(self, message: str):
        """进度回调"""
        log_view = self.get_component("log_view")
        log_view.controls.append(ft.Text(message, size=12))
        log_view.update()
    
    def _on_complete(self, stats: Dict[str, Any]):
        """完成回调"""
        self._on_progress(f"\n✅ 生成完成！总计: {stats['total']} 个文件")
        
        # 恢复按钮
        generate_btn = self.get_component("generate_btn")
        generate_btn.disabled = False
        cancel_btn = self.get_component("cancel_btn")
        cancel_btn.disabled = True
        
        # 更新统计
        stats_container = self.get_component("stats_container")
        stats_container.content = ft.Text(
            f"总数: {stats['total']} 个文件",
            size=14,
            weight=ft.FontWeight.BOLD
        )
        self.page.update()
    
    def _on_error(self, error: Exception):
        """错误回调"""
        self._on_progress(f"\n❌ 错误: {error}")
        
        # 恢复按钮
        generate_btn = self.get_component("generate_btn")
        generate_btn.disabled = False
        cancel_btn = self.get_component("cancel_btn")
        cancel_btn.disabled = True
        self.page.update()
    
    # ==================== 辅助方法 ====================
    
    def log_message(self, message: str, is_error: bool = False, is_warning: bool = False, is_info: bool = False):
        """日志消息"""
        log_view = self.get_component("log_view")
        color = "red" if is_error else ("orange" if is_warning else ("blue" if is_info else None))
        log_view.controls.append(ft.Text(message, size=12, color=color))
        log_view.update()
    
    def register_generate_event(self, handler: callable):
        """注册生成事件（兼容性，实际已在build中绑定）"""
        # 此方法保留，但不再被run_flet调用
        pass
    
    def register_cancel_event(self, handler: callable):
        """注册取消事件（兼容性）"""
        pass