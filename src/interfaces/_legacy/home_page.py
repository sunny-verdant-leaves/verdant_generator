import flet as ft
from src.interfaces.base_page import BasePage


class HomePage(BasePage):
    """
    HomePage - 首页（占位UI）
    职责：纯UI展示，欢迎信息
    """
    
    def __init__(self, router, page: ft.Page):
        super().__init__(router, page)
        # 不依赖任何Service
    
    def build(self) -> ft.Control:
        """纯UI展示"""
        return ft.Container(
            content=ft.Column([
                ft.Text("🏠 MC Recipe Generator", size=30, weight=ft.FontWeight.BOLD),
                ft.Text("欢迎使用配方生成工具！", size=16),
                ft.Divider(height=30),
                ft.Text("✨ 核心功能：", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("• ⚙️ 设置页：管理配置和模板", size=14),
                ft.Text("• 🚀 生成器：批量生成配方", size=14),
                ft.Text("• 📄 本地化：批量生成翻译（开发中）", size=14),
                ft.Divider(height=30),
                ft.Text("📝 使用流程：", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("1. 在【设置】页加载配置", size=14),
                ft.Text("2. 扫描并选择模板", size=14),
                ft.Text("3. 在【生成器】页开始生成", size=14),
            ], expand=True, spacing=15),
            padding=ft.padding.only(top=40, left=20, right=20)
        )