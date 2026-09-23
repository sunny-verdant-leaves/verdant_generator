# src/interfaces/localizer_page.py

import flet as ft
from pathlib import Path
from src.interfaces.base_page import BasePage
from src.service.localizer_service import LocalizerService
from typing import Optional, List, Dict, Any


class LocalizerPage(BasePage):
    """
    LocalizerPage - 批量本地化生成页
    职责：UI展示 + 事件绑定 + 调用LocalizerService
    """
    
    def __init__(self, router, page: ft.Page, localizer_service: Optional[LocalizerService] = None):
        super().__init__(router, page)
        # 默认配置路径
        self.default_config_path = "test_manual/config.json"
        self.localizer_service = localizer_service or LocalizerService()
        
        # 设置服务回调
        self.localizer_service.set_callbacks(
            on_progress=self._on_progress,
            on_complete=self._on_complete,
            on_error=self._on_error
        )
        
        # UI组件引用
        self._template_dropdown: Optional[ft.Dropdown] = None
        self._batch_list_view: Optional[ft.ListView] = None
    
    def build(self) -> ft.Control:
        """构建完整UI界面"""
        
        # ===== 配置文件选择区域 =====
        config_path_label = ft.Text(
            "📄 配置文件路径",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_900
        )
        
        config_path_textfield = self.add_component(
            "config_path_textfield",
            ft.TextField(
                label="输入配置文件路径",
                value=self.default_config_path,  # 默认值
                hint_text="例如: config/localization.json",
                expand=True,
                text_size=14,
                dense=True,
                suffix_icon=ft.icons.FILE_OPEN,
                on_change=self._on_config_path_change,  # 路径变更时验证
            )
        )
        
        config_path_row = ft.Row(
            [
                config_path_textfield,
                self.add_component(
                    "browse_config_btn",
                    ft.IconButton(
                        icon=ft.icons.FOLDER_OPEN,
                        tooltip="浏览配置文件",
                        on_click=self._handle_browse_config
                    )
                )
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        # ===== 顶部控制面板 =====
        load_config_btn = self.add_component(
            "load_config_btn",
            ft.ElevatedButton(
                "🔄 加载配置",
                icon=ft.icons.SYNC,
                on_click=self._handle_load_config
            )
        )
        
        template_dropdown = self.add_component(
            "template_dropdown",
            ft.Dropdown(
                label="选择模板文件",
                options=[],
                disabled=True,
                expand=True
            )
        )
        
        # ===== BatchItem 列表 =====
        batch_list_header = ft.Container(
            content=ft.Text("📦 BatchItem 列表 (0 项)", size=16, weight=ft.FontWeight.BOLD),
            padding=ft.padding.only(bottom=10)
        )
        
        batch_list_view = self.add_component(
            "batch_list_view",
            ft.ListView(
                expand=True,
                spacing=5,
                padding=10,
                auto_scroll=False
            )
        )
        
        batch_list_container = ft.Container(
            content=ft.Column([
                batch_list_header,
                batch_list_view
            ], expand=True),
            border=ft.border.all(1, ft.colors.GREY_400),
            border_radius=5,
            padding=10,
            height=300,
        )
        
        # ===== 生成控制面板 =====
        dry_run_checkbox = self.add_component(
            "dry_run_checkbox",
            ft.Checkbox(label="预览模式（不保存文件）", value=True)
        )
        
        explain_checkbox = self.add_component(
            "explain_checkbox",
            ft.Checkbox(label="解释模式（显示详细替换）", value=False)
        )
        
        generate_btn = self.add_component(
            "generate_btn",
            ft.ElevatedButton(
                "🚀 开始生成",
                icon=ft.icons.PLAY_ARROW,
                expand=True,
                disabled=True,
                on_click=self._handle_generate
            )
        )
        
        open_output_btn = self.add_component(
            "open_output_btn",
            ft.ElevatedButton(
                "📁 打开输出目录",
                icon=ft.icons.FOLDER_OPEN,
                expand=True,
                disabled=True,
                on_click=self._handle_open_output_dir
            )
        )
        
        control_panel = ft.Container(
            content=ft.Column([
                ft.Text("⚙️ 生成控制", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([dry_run_checkbox, explain_checkbox], spacing=20),
                ft.Row([generate_btn, open_output_btn], spacing=10)
            ], spacing=15),
            padding=20,
            bgcolor="#DDDDEE",
            border_radius=5
        )
        
        # ===== 日志输出区域 =====
        log_view = self.add_component(
            "log_view",
            ft.ListView(
                expand=True,
                spacing=5,
                padding=10,
                auto_scroll=True,
                height=200
            )
        )
        
        log_container = ft.Container(
            content=ft.Column([
                ft.Text("📋 生成日志", size=16, weight=ft.FontWeight.BOLD),
                log_view
            ], expand=True),
            border=ft.border.all(1, ft.colors.GREY_400),
            border_radius=5,
            padding=10
        )
        
        # ===== 统计信息 =====
        stats_container = self.add_component(
            "stats_container",
            ft.Container(
                content=ft.Text(
                    "📊 统计: 0 物品 | 0 成功 | 0 失败 | 0 条目",
                    size=14,
                    weight=ft.FontWeight.BOLD
                ),
                padding=10,
                bgcolor="#E3F2FD",
                border_radius=5,
            )
        )
        
        # ===== 主布局组装 =====
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("📄 批量本地化工具", size=24, weight=ft.FontWeight.BOLD),
                    config_path_label,
                    config_path_row,
                    load_config_btn,
                    template_dropdown,
                ], spacing=15),
                padding=20,
                bgcolor="#DDDDEE",
                border_radius=5,
            ),
            batch_list_container,
            control_panel,
            log_container,
            stats_container,
        ], expand=True, spacing=15, scroll=ft.ScrollMode.AUTO)
    
    # ==================== 事件处理 ====================
    
    def _on_config_path_change(self, e: ft.ControlEvent):
        """配置文件路径变更时验证"""
        path = e.control.value.strip()
        if not path:
            return
        
        path_obj = Path(path)
        if not path_obj.exists():
            e.control.error_text = "文件不存在"
        elif not path_obj.is_file():
            e.control.error_text = "不是有效的文件"
        elif path_obj.suffix.lower() != '.json':
            e.control.error_text = "必须是JSON文件"
        else:
            e.control.error_text = None
        self.page.update()
    
    def _handle_browse_config(self, e: ft.ControlEvent):
        """浏览配置文件（Flet 目前不支持原生文件选择器，提供说明）"""
        self.log_message("ℹ️  提示: 请在文本框中手动输入配置文件路径", is_info=True)
        # 未来可使用: https://pypi.org/project/flet-file-picker/
    
    def _handle_load_config(self, e: ft.ControlEvent):
        """加载配置按钮点击"""
        # 获取用户输入的路径（优先使用文本框中的）
        config_path_textfield = self.get_component("config_path_textfield")
        custom_path = config_path_textfield.value.strip()
        
        # 如果没有输入路径，使用默认值
        if not custom_path:
            custom_path = self.default_config_path
            config_path_textfield.value = custom_path
        
        self.log_message(f"⏳ 正在加载配置: {custom_path}")
        
        # 验证路径
        path_obj = Path(custom_path)
        if not path_obj.exists():
            self.log_message(f"❌ 配置文件不存在: {custom_path}", is_error=True)
            return
        
        # 禁用按钮防止重复点击
        load_btn = self.get_component("load_config_btn")
        load_btn.disabled = True
        self.page.update()
        
        # 重新初始化服务（带新路径）
        self.localizer_service = LocalizerService(config_path=custom_path)
        self.localizer_service.set_callbacks(
            on_progress=self._on_progress,
            on_complete=self._on_complete,
            on_error=self._on_error
        )
        
        # 执行加载
        success = self.localizer_service.reload_config()
        
        if success:
            # 更新模板下拉框
            templates = self.localizer_service.get_available_templates()
            dropdown = self.get_component("template_dropdown")
            dropdown.options = [ft.dropdown.Option(name) for name in templates]
            dropdown.disabled = len(templates) == 0
            
            # 更新BatchItem列表
            self._update_batch_list_view()
            
            # 启用生成按钮
            generate_btn = self.get_component("generate_btn")
            generate_btn.disabled = len(templates) == 0
            
            open_btn = self.get_component("open_output_btn")
            open_btn.disabled = False
            
            self.log_message(f"✅ 配置加载成功！共 {len(templates)} 个模板，{len(self.localizer_service.batch_items)} 个物品")
            
            # 更新统计
            self._update_stats()
        else:
            self.log_message("❌ 配置加载失败，请检查文件格式和内容", is_error=True)
        
        # 恢复按钮
        load_btn.disabled = False
        self.page.update()
    
    def _update_batch_list_view(self):
        """更新BatchItem列表显示"""
        batch_list = self.get_component("batch_list_view")
        batch_list.controls.clear()
        
        # 按类别分组显示
        for item in sorted(self.localizer_service.batch_items.values(), key=lambda x: x.id):
            # 创建列表项
            item_control = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.LABEL, size=16, color=ft.colors.BLUE),
                    ft.Text(item.id, size=14, weight=ft.FontWeight.BOLD, width=150),
                    ft.Text(item.zh_cn, size=14, color=ft.colors.GREY_700),
                    ft.Container(
                        content=ft.Text(item.category, size=12, color=ft.colors.WHITE),
                        bgcolor=ft.colors.GREEN_400,
                        border_radius=10,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2)
                    ),
                ], alignment=ft.MainAxisAlignment.START, spacing=10),
                padding=ft.padding.symmetric(vertical=5, horizontal=10),
                border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.GREY_300))
            )
            batch_list.controls.append(item_control)
        
        # 更新标题
        header = ft.Text(
            f"📦 BatchItem 列表 ({len(self.localizer_service.batch_items)} 项)",
            size=16,
            weight=ft.FontWeight.BOLD
        )
        batch_list.parent.controls[0].content = header
    
    def _handle_generate(self, e: ft.ControlEvent):
        """生成按钮点击"""
        dropdown = self.get_component("template_dropdown")
        if not dropdown.value:
            self.log_message("❌ 请先选择模板文件", is_error=True)
            return
        
        # 获取参数
        dry_run = self.get_component("dry_run_checkbox").value
        explain_mode = self.get_component("explain_checkbox").value
        
        # 禁用按钮
        generate_btn = self.get_component("generate_btn")
        generate_btn.disabled = True
        self.page.update()
        
        # 清空日志
        log_view = self.get_component("log_view")
        log_view.controls.clear()
        
        # 执行生成
        self.log_message(f"⏳ 开始生成本地化条目...")
        success = self.localizer_service.start_generation(
            template_name=dropdown.value,
            dry_run=dry_run,
            explain_mode=explain_mode
        )
        
        if not success:
            self.log_message("❌ 生成失败，请查看错误信息", is_error=True)
        
        # 恢复按钮
        generate_btn.disabled = False
        self.page.update()
    
    def _handle_open_output_dir(self, e: ft.ControlEvent):
        """打开输出目录"""
        try:
            output_dir = Path(self.localizer_service.get_output_directory())
            if output_dir.exists():
                import subprocess
                subprocess.Popen(f'explorer "{output_dir.absolute()}"')
                self.log_message("📂 已打开输出目录", is_info=True)
            else:
                self.log_message("⚠️ 输出目录不存在", is_warning=True)
        except Exception as ex:
            self.log_message(f"❌ 无法打开目录: {ex}", is_error=True)
    
    # ==================== Service回调 ====================
    
    def _on_progress(self, message: str):
        """进度回调"""
        self.log_message(message)
    
    def _on_complete(self, stats: Dict[str, Any]):
        """完成回调"""
        self.log_message(f"\n✅ 生成完成！")
        self.log_message(f"   成功: {stats['successful_items']} 个物品")
        self.log_message(f"   失败: {stats['failed_items']} 个物品")
        self.log_message(f"   总计: {stats['total_entries']} 个本地化条目")
        
        self._update_stats()
        
        # 恢复按钮
        generate_btn = self.get_component("generate_btn")
        generate_btn.disabled = False
        self.page.update()
    
    def _on_error(self, error: Exception):
        """错误回调"""
        self.log_message(f"❌ 错误: {error}", is_error=True)
        
        # 恢复按钮
        generate_btn = self.get_component("generate_btn")
        generate_btn.disabled = False
        self.page.update()
    
    # ==================== 辅助方法 ====================
    
    def _update_stats(self):
        """更新统计信息"""
        stats = self.localizer_service.stats
        stats_container = self.get_component("stats_container")
        stats_container.content = ft.Text(
            f"📊 统计: {stats['total_items']} 物品 | {stats['successful_items']} 成功 | {stats['failed_items']} 失败 | {stats['total_entries']} 条目",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_900
        )
        stats_container.update()
    
    def log_message(self, message: str, is_error: bool = False, 
                   is_warning: bool = False, is_info: bool = False):
        """添加日志消息"""
        log_view = self.get_component("log_view")
        color = "red" if is_error else ("orange" if is_warning else ("blue" if is_info else None))
        prefix = ""
        if is_error:
            prefix = "❌ "
        elif is_warning:
            prefix = "⚠️  "
        elif is_info:
            prefix = "ℹ️  "
        
        log_view.controls.append(
            ft.Text(f"{prefix}{message}", size=12, color=color)
        )
        log_view.update()