
import flet as ft
from typing import Callable, Dict

class BaseRouter:
    """
    可复用的页面路由组件
    
    使用方式：
    1. 创建路由实例
    2. 用add_route()注册页面
    3. 用go()切换页面
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.routes: Dict[str, Callable[[], ft.Control]] = {}
        self.current_route = None
        
        # 创建Header
        self.header = ft.Container(
            content=ft.Row([], spacing=0),  # 按钮动态生成
            bgcolor=ft.colors.BLUE_GREY_900,
            padding=10,
        )
        
        # 创建内容区（弹性填充）
        self.content_area = ft.Container(
            content=ft.Text("请选择一个页面", text_align=ft.TextAlign.CENTER),
            expand=True,
        )
        
        # 组装布局
        page.add(
            ft.Column([
                self.header,        # 顶部导航（固定高度）
                self.content_area,  # 内容区（弹性填充）
            ], expand=True, spacing=0)
        )
    
    def add_route(self, name: str, title: str, icon: ft.Icon, builder: Callable[[], ft.Control]):
        """
        注册一个路由
        
        Args:
            name: 路由名称（如 "home", "generator"）
            title: 显示在按钮上的文字
            icon: 按钮图标
            builder: 返回页面内容的函数
        """
        self.routes[name] = {
            "title": title,
            "icon": icon,
            "builder": builder,
        }
        
        # 重新生成Header（添加新按钮）
        self._rebuild_header()
    
    def _rebuild_header(self):
        """重新生成导航栏按钮"""
        buttons = []
        for name, route in self.routes.items():
            is_active = self.current_route == name
            
            buttons.append(
                ft.TextButton(
                    content=ft.Row([
                        ft.Icon(route["icon"], color="white"),
                        ft.Text(route["title"], color="white"),
                    ], spacing=5),
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.BLUE if is_active else "transparent",
                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    ),
                    on_click=lambda e, n=name: self.go(n),
                )
            )
        
        self.header.content = ft.Row(buttons, alignment=ft.MainAxisAlignment.CENTER)
        self.page.update()
    
    def go(self, name: str):
        """切换到指定路由"""
        if name not in self.routes:
            return
        
        self.current_route = name
        
        # 获取页面内容（通过builder函数动态创建）
        content = self.routes[name]["builder"]()
        
        # 使用动画切换
        self.content_area.content = ft.AnimatedSwitcher(
            content,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=300,
        )
        
        # 更新Header高亮
        self._rebuild_header()
        
        self.page.update()
