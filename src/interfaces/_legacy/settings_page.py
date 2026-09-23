import flet as ft
import asyncio
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor  # 新增：兼容旧版本
from src.interfaces.base_page import BasePage
from src.service.settings_service import SettingsService


class SettingsPage(BasePage):
    """
    设置页面 - 负责UI展示和用户交互
    所有的耗时操作（如文件扫描）都会用后台线程处理，避免界面卡死
    """
    
    # 类级别的线程池，所有实例共享，避免创建过多线程
    _executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="SettingsWorker")
    
    def __init__(self, router, page: ft.Page, service: SettingsService):
        super().__init__(router, page)
        self.service = service
        
        self._template_checkboxes: Dict[str, ft.Checkbox] = {}
        self._selected_count_text: ft.Text = ft.Text("已选择: 0 个模板", size=14)
        self._status_text: ft.Text = ft.Text("等待加载配置...", size=12, color=ft.colors.ORANGE)
        self._refresh_btn: Optional[ft.ElevatedButton] = None
        self._save_btn: Optional[ft.ElevatedButton] = None
    
    def build(self) -> ft.Control:
        print("🔍 [SettingsPage] 代码执行到: build()")  # 调试
        
        if not self.service.has_config():
            self.service.load_config()
        
        # ... 所有UI代码保持不变 ...
        config_file_field = self.add_component(
            "config_file_field",
            ft.TextField(
                label="配置文件路径",
                value="config.json",
                expand=True,
                disabled=False,
                on_change=self._on_config_path_change
            )
        )
        
        load_config_btn = self.add_component(
            "load_config_btn",
            ft.ElevatedButton(
                "📂 加载配置",
                icon=ft.icons.FOLDER_OPEN,
                on_click=self._handle_load_config
            )
        )
        
        output_dir_field = self.add_component(
            "output_dir_field",
            ft.TextField(
                label="输出目录",
                expand=True,
                disabled=False,
                on_change=self._on_output_dir_change
            )
        )
        
        template_dir_field = self.add_component(
            "template_dir_field",
            ft.TextField(
                label="模板目录",
                height=80,
                disabled=False,
                on_change=self._on_template_dir_change
            )
        )
        
        default_ns_field = self.add_component(
            "default_ns_field",
            ft.TextField(
                label="默认命名空间",
                expand=True,
                disabled=False,
                on_change=self._on_namespace_change
            )
        )
        
        template_list_view = self.add_component(
            "template_list_view",
            ft.ListView(spacing=5, padding=10, auto_scroll=True, height=300)
        )
        
        self._refresh_btn = self.add_component(
            "refresh_btn", 
            ft.ElevatedButton(
                "🔄 刷新模板列表",
                icon=ft.icons.REFRESH,
                disabled=False,
                on_click=self._handle_refresh_templates
            )
        )
        
        rules_list_view = self.add_component(
            "rules_list_view",
            ft.ListView(spacing=5, padding=10, height=200)
        )
        
        self._save_btn = self.add_component(
            "save_btn",
            ft.ElevatedButton(
                "💾 保存配置",
                expand=True,
                bgcolor=ft.colors.BLUE,
                color="white",
                disabled=False,
                on_click=self._handle_save_config
            )
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("⚙️ 配置文件设置", size=24, weight=ft.FontWeight.BOLD),
                ft.Row([config_file_field, load_config_btn], spacing=10),
                ft.Divider(),
                ft.Text("基础设置", size=18, weight=ft.FontWeight.BOLD),
                output_dir_field,
                template_dir_field,
                default_ns_field,
                ft.Divider(),
                ft.Text("模板文件管理", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([self._refresh_btn, self._selected_count_text], 
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self._status_text,
                template_list_view,
                ft.Divider(),
                ft.Text("替换规则", size=18, weight=ft.FontWeight.BOLD),
                rules_list_view,
                ft.Divider(),
                self._save_btn,
            ], expand=True, spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(20),
        )
    
    # ==================== 事件处理器 ====================
    
    def _handle_load_config(self, e: ft.ControlEvent):
        print("🔍 [SettingsPage] 代码执行到: _handle_load_config")  # 调试
        
        config_field = self.get_component("config_file_field")
        config_path = config_field.value if config_field else "config.json"
        
        success = self.service.load_config(config_path)
        if success:
            self._update_ui_from_service()
            self.page.run_task(self._scan_templates_async)
            self.show_status_message("✅ 配置加载成功", is_error=False)
        else:
            self.show_status_message("⚠️ 加载失败，使用默认配置", is_error=True)
    
    def _handle_refresh_templates(self, e: ft.ControlEvent):
        print("🔍 [SettingsPage] 代码执行到: _handle_refresh_templates")  # 调试
        self.page.run_task(self._scan_templates_async)
    
    def _handle_save_config(self, e: ft.ControlEvent):
        print("🔍 [SettingsPage] 代码执行到: _handle_save_config")  # 调试
        # 保存操作交给异步函数处理
        self.page.run_task(self._save_config_async)
    
    async def _save_config_async(self):
        """异步保存配置"""
        self._update_service_from_ui()
        
        errors = self.service.validate_config()
        if errors:
            self.show_status_message(f"❌ {errors[0]}", is_error=True)
            return
        
        config_field = self.get_component("config_file_field")
        save_path = config_field.value if config_field else "config.json"
        
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            self._executor, 
            self.service.save_config, 
            save_path
        )
        
        if success:
            await self._show_save_success_animation()
            self.show_status_message("✅ 配置已保存", is_error=False)
        else:
            self.show_status_message("❌ 保存失败", is_error=True)
    
    def _on_config_path_change(self, e: ft.ControlEvent):
        pass
    
    def _on_output_dir_change(self, e: ft.ControlEvent):
        pass
    
    def _on_template_dir_change(self, e: ft.ControlEvent):
        print("🔍 [SettingsPage] 代码执行到: _on_template_dir_change")  # 调试
        self.show_status_message("⏳ 检测到目录变更，正在自动刷新...", is_error=False)
        self.page.run_task(self._scan_templates_async)
    
    def _on_namespace_change(self, e: ft.ControlEvent):
        pass
    
    # ==================== 异步任务 ====================
    
    async def _scan_templates_async(self):
        """异步扫描模板文件"""
        print("🔍 [SettingsPage] 代码执行到: _scan_templates_async 开始")  # 调试
        
        if not self.service.has_config():
            print("🔍 [SettingsPage] 扫描取消：无配置")  # 调试
            return
        
        self.set_refresh_button_loading(True)
        self.show_status_message("⏳ 正在扫描模板...", is_error=False)
        
        try:
            # 兼容Python 3.6-3.8：手动在线程中执行
            loop = asyncio.get_event_loop()
            templates = await loop.run_in_executor(
                self._executor, 
                self.service.scan_templates
            )
            
            print(f"🔍 [SettingsPage] 扫描完成，找到 {len(templates)} 个模板")  # 调试
            self._update_template_list(templates, f"✅ 扫描成功，找到 {len(templates)} 个模板")
        except Exception as e:
            print(f"🔍 [SettingsPage] 扫描失败: {e}")  # 调试
            self.show_status_message(f"❌ 扫描失败: {str(e)}", is_error=True)
        finally:
            self.set_refresh_button_loading(False)
    
    # ==================== UI更新方法 ====================
    
    def _update_ui_from_service(self):
        if not self.service.has_config():
            return
        
        config_dict = self.service.get_config_dict()
        self.get_component("output_dir_field").value = config_dict["output_dir"]
        self.get_component("template_dir_field").value = config_dict["template_dir"]
        self.get_component("default_ns_field").value = config_dict["default_namespace"]
        
        self._update_selected_count()
        self.page.update()
    
    def _update_service_from_ui(self):
        output_dir = self.get_component("output_dir_field").value
        template_dir = self.get_component("template_dir_field").value
        namespace = self.get_component("default_ns_field").value
        
        self.service.update_config_from_form(output_dir, template_dir, namespace)
    
    def _update_template_list(self, templates: List[Path], status_message: str = ""):
        print(f"🔍 [SettingsPage] 更新模板列表UI: {len(templates)} 项")  # 调试
        
        list_view = self.get_component("template_list_view")
        list_view.controls.clear()
        self._template_checkboxes.clear()
        
        selected_templates = self.service.get_selected_templates()
        
        for template_path in sorted(templates):
            filename = template_path.name
            is_checked = filename in selected_templates
            
            checkbox = ft.Checkbox(
                value=is_checked,
                label=filename,
                on_change=lambda e, fn=filename: self._on_template_checkbox_change(fn, e.control.value)
            )
            self._template_checkboxes[filename] = checkbox
            
            list_tile = ft.ListTile(
                leading=checkbox,
                title=ft.Text(filename, size=14),
                selected=is_checked,
                height=100,
                on_click=lambda e, fn=filename: self._on_template_tile_click(fn)
            )
            list_view.controls.append(list_tile)
        
        self._status_text.value = status_message
        self._status_text.color = ft.colors.GREEN if "成功" in status_message else ft.colors.ORANGE
        self._update_selected_count()
        self.page.update()
    
    def _update_selected_count(self):
        count = len(self.service.get_selected_templates())
        self._selected_count_text.value = f"已选择: {count} 个模板"
        self._selected_count_text.color = ft.colors.RED if count == 0 else ft.colors.GREY_600
        self._selected_count_text.update()
    
    def show_status_message(self, message: str, is_error: bool = False):
        print(f"🔍 [SettingsPage] 状态消息: {message}")  # 调试
        
        self._status_text.value = message
        self._status_text.color = ft.colors.RED if is_error else ft.colors.ORANGE
        self._status_text.update()
    
    def set_refresh_button_loading(self, loading: bool):
        if loading:
            self._refresh_btn.text = "⏳ 扫描中..."
            self._refresh_btn.disabled = True
        else:
            self._refresh_btn.text = "🔄 刷新模板列表"
            self._refresh_btn.disabled = False
        self.page.update()
    
    # ==================== 辅助方法 ====================
    
    def _on_template_tile_click(self, filename: str):
        checkbox = self._template_checkboxes.get(filename)
        if checkbox:
            checkbox.value = not checkbox.value
            checkbox.update()
            self._on_template_checkbox_change(filename, checkbox.value)
    
    def _on_template_checkbox_change(self, filename: str, is_checked: bool):
        if is_checked:
            self.service.add_template(filename)
            self.show_status_message(f"➕ 已添加: {filename}", is_error=False)
        else:
            self.service.remove_template(filename)
            self.show_status_message(f"➖ 已移除: {filename}", is_error=False)
        
        self._update_selected_count()
    
    async def _show_save_success_animation(self):
        """保存成功动画 - async版本"""
        original_text = self._save_btn.text
        original_bgcolor = self._save_btn.bgcolor
        
        self._save_btn.text = "✅ 保存成功"
        self._save_btn.bgcolor = ft.colors.GREEN
        self.page.update()
        
        # 异步等待3秒，不阻塞UI
        await asyncio.sleep(3)
        
        self._save_btn.text = original_text
        self._save_btn.bgcolor = original_bgcolor
        self.page.update()
