"""Flet UI 入口。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


def patch_proactor_del():
    """
    Python 3.8 + Windows 下静默 ProactorEventLoop.__del__ 的 RuntimeError。
    3.9+ 官方已修复，无需补丁。
    """
    if sys.version_info < (3, 9) and sys.platform == "win32":
        import functools
        from asyncio.proactor_events import _ProactorBasePipeTransport

        original_del = _ProactorBasePipeTransport.__del__

        @functools.wraps(original_del)
        def silent_del(self):
            try:
                original_del(self)
            except RuntimeError as e:
                if str(e) != "Event loop is closed":
                    raise

        _ProactorBasePipeTransport.__del__ = silent_del


patch_proactor_del()


from verdant_generator.interfaces import run

if __name__ == "__main__":
    run()