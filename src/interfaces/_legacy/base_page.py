
import flet as ft
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BasePage(ABC):
    """页面基类：仅负责UI构建和组件管理"""
    
    def __init__(self, router: Any, page: ft.Page):
        self.router = router
        self.page = page
        self.components: Dict[str, ft.Control] = {}
    
    def add_component(self, name: str, component: ft.Control) -> ft.Control:
        """注册组件"""
        self.components[name] = component
        return component
    
    def get_component(self, name: str) -> Optional[ft.Control]:
        """获取已注册的组件"""
        return self.components.get(name)
    
    @abstractmethod
    def build(self) -> ft.Control:
        """子类实现：返回页面UI结构"""
        pass