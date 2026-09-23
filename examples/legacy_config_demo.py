"""端到端验证：配置 → Scheduler → Plugin → 磁盘。

运行：
    python examples/legacy_config_demo.py
"""
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from src.scheduler import Scheduler


TREES = [
    "minecraft:oak",
    "minecraft:crimson",
    "minecraft:warped",
    "biomesoplenty:fir",
]

MATERIALS = {
    "minecraft:oak": "橡木",
    "minecraft:crimson": "绯红",
    "minecraft:warped": "诡异",
    "biomesoplenty:fir": "冷杉",
}

PER_MATERIAL_REPLACEMENTS = {
    "minecraft:crimson": {"_log": "_stem"},
    "minecraft:warped": {"_log": "_stem"},
}

RECIPE_TEMPLATE_NAME = "{tree}_recipe.json"
RECIPE_TEMPLATE_CONTENT = """{
  "type": "minecraft:crafting_shaped",
  "pattern": ["##", "##"],
  "key": {
    "#": {"item": "{tree}_planks"}
  },
  "result": {"item": "{tree}_chest_boat"}
}
"""

LOCALIZATION_TEMPLATE_NAME = "{material_id}_localization.json"
LOCALIZATION_TEMPLATE_CONTENT = """{
    "block.pfm.{material_id}_chair": "基本{material_zh_cn}椅子",
    "block.pfm.{material_id}_table": "{material_zh_cn}桌子",
    "block.pfm.{material_id}_log": "{material_zh_cn}原木"
}
"""


def _posix(p: Path) -> str:
    return str(p).replace("\\", "/")


def build_workdir(workdir: Path) -> Path:
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)

    tpl_dir = workdir / "templates"
    tpl_dir.mkdir()

    (tpl_dir / RECIPE_TEMPLATE_NAME).write_text(
        RECIPE_TEMPLATE_CONTENT, encoding="utf-8"
    )
    (tpl_dir / LOCALIZATION_TEMPLATE_NAME).write_text(
        LOCALIZATION_TEMPLATE_CONTENT, encoding="utf-8"
    )

    config = {
        "plugins": [
            {
                "type": "recipe_generator",
                "template": _posix(tpl_dir / RECIPE_TEMPLATE_NAME),
                "trees": TREES,
            },
            {
                "type": "localizer",
                "template": _posix(tpl_dir / LOCALIZATION_TEMPLATE_NAME),
                "materials": MATERIALS,
                "per_material_replacements": PER_MATERIAL_REPLACEMENTS,
            },
        ],
    }
    config_path = workdir / "config.json"
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return config_path


def print_header(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main():
    workdir = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).parent / "_demo_workdir"
    )

    print_header("1. 准备工作目录")
    config_path = build_workdir(workdir)
    print(f"  工作目录: {workdir}")

    print_header("2. 执行调度")
    output_dir = workdir / "output"
    scheduler = Scheduler(base_output_dir=output_dir, dry_run=False)
    report = scheduler.run_config_file(config_path)

    print(f"  写入: {report.total_written} 个文件")
    print(f"  失败: {report.total_failed} 项")
    for name, msg in report.errors:
        print(f"    [{name}] {msg}")

    print_header("3. 输出目录结构")
    for path in sorted(output_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(output_dir)
            print(f"  {rel}")

    print_header("4. 关键验证：crimson 的 _log → _stem")
    crimson = output_dir / "localizer" / "minecraft_crimson_localization.json"
    if crimson.exists():
        content = crimson.read_text(encoding="utf-8")
        print("  内容:")
        for line in content.splitlines():
            print(f"    {line}")
        if "_stem" in content and "crimson_log" not in content:
            print("\n  ✅ _log → _stem 生效")
        else:
            print("\n  ❌ 后处理异常")

    print_header("完成")
    print("  🎉 全部成功" if not report.has_failure else "  ⚠️  有错误")
    sys.exit(1 if report.has_failure else 0)


if __name__ == "__main__":
    main()