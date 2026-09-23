"""端到端验证：用真实配置跑通"配方生成 + 本地化"两个旧场景。

运行：
    python examples/legacy_config_demo.py

可选参数：
    python examples/legacy_config_demo.py <工作目录>

默认工作目录：examples/_demo_workdir/
运行后目录结构：
    _demo_workdir/
    ├── templates/
    │   ├── {tree}_recipe.json
    │   └── {material_id}_localization.json
    ├── config.json
    └── output/
        ├── recipe_generator/
        │   ├── minecraft_oak_recipe.json
        │   ├── minecraft_crimson_recipe.json
        │   └── ...
        └── localizer/
            ├── minecraft_oak_localization.json
            ├── minecraft_crimson_localization.json
            └── ...
"""
import json
import shutil
import sys
from pathlib import Path

# 让脚本能直接 import src
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from src.scheduler import Scheduler


# ============================================================================
# 配置内容
# ============================================================================

VARIABLES = {
    "tree": [
        "minecraft:oak",
        "minecraft:crimson",
        "minecraft:warped",
        "biomesoplenty:fir",
    ],
}

STRATEGIES = {
    "per_tree": {
        "variables": ["tree"],
        "packer": "per_combination",
    },
}

# ---- 配方模板（模拟旧项目的 {tree}.json）----
RECIPE_TEMPLATE_NAME = "{tree}_recipe.json"
RECIPE_TEMPLATE_CONTENT = """{
  "type": "minecraft:crafting_shaped",
  "pattern": [
    "##",
    "##"
  ],
  "key": {
    "#": {
      "item": "{tree}_planks"
    }
  },
  "result": {
    "item": "{tree}_chest_boat"
  }
}
"""

# ---- 本地化模板（模拟旧项目的 material.json）----
# 文件名带 {material_id} 占位符，让每个材质输出到独立文件
LOCALIZATION_TEMPLATE_NAME = "{material_id}_localization.json"
LOCALIZATION_TEMPLATE_CONTENT = """{
    "block.pfm.{material_id}_chair": "基本{material_zh_cn}椅子",
    "block.pfm.{material_id}_table": "{material_zh_cn}桌子",
    "block.pfm.{material_id}_log": "{material_zh_cn}原木"
}
"""

# ---- 材质对（material_id → 中文名）----
MATERIALS = {
    "minecraft:oak": "橡木",
    "minecraft:crimson": "绯红",
    "minecraft:warped": "诡异",
    "biomesoplenty:fir": "冷杉",
}

# ---- 材质专属替换：crimson/warped 的 _log → _stem ----
PER_MATERIAL_REPLACEMENTS = {
    "minecraft:crimson": {"_log": "_stem"},
    "minecraft:warped": {"_log": "_stem"},
}


# ============================================================================
# 构建文件
# ============================================================================

def build_workdir(workdir: Path) -> Path:
    """在工作目录里准备模板和配置，返回 config.json 路径。"""
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)

    tpl_dir = workdir / "templates"
    tpl_dir.mkdir()

    # 写模板
    (tpl_dir / RECIPE_TEMPLATE_NAME).write_text(
        RECIPE_TEMPLATE_CONTENT, encoding="utf-8"
    )
    (tpl_dir / LOCALIZATION_TEMPLATE_NAME).write_text(
        LOCALIZATION_TEMPLATE_CONTENT, encoding="utf-8"
    )

    # 写配置
    config = {
        "variables": VARIABLES,
        "strategies": STRATEGIES,
        "plugins": [
            {
                "type": "recipe_generator",
                "template": _posix(tpl_dir / RECIPE_TEMPLATE_NAME),
                "variables": ["tree"],
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


def _posix(path: Path) -> str:
    """统一路径为正斜杠，避免 JSON 里的反斜杠转义问题。"""
    return str(path).replace("\\", "/")


# ============================================================================
# 打印
# ============================================================================

def print_header(title: str):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_tree(root: Path):
    """打印目录树。"""
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root)
            size = path.stat().st_size
            print(f"  {rel}  ({size} B)")


def print_file(path: Path, max_lines: int = 8):
    """打印文件内容，超过 max_lines 截断。"""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    print(f"\n--- {path.name} ---")
    for line in lines[:max_lines]:
        print(f"  {line}")
    if len(lines) > max_lines:
        print(f"  ... (共 {len(lines)} 行)")


# ============================================================================
# 主流程
# ============================================================================

def main():
    workdir = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).parent / "_demo_workdir"
    )

    print_header("1. 准备工作目录")
    config_path = build_workdir(workdir)
    print(f"  工作目录: {workdir}")
    print(f"  配置文件: {config_path}")
    print("\n  模板文件:")
    for tpl in sorted((workdir / "templates").iterdir()):
        print(f"    {tpl.name}")

    print_header("2. 加载配置")
    with config_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    print(f"  变量: {list(raw['variables'].keys())}")
    print(f"  策略: {list(raw['strategies'].keys())}")
    print(f"  插件: {[p['type'] for p in raw['plugins']]}")

    print_header("3. 执行调度")
    output_dir = workdir / "output"
    scheduler = Scheduler(base_output_dir=output_dir, dry_run=False)
    report = scheduler.run_config_file(config_path)

    print(f"  写入: {report.total_written} 个文件")
    print(f"  失败: {report.total_failed} 项")
    if report.errors:
        print("\n  错误:")
        for name, msg in report.errors:
            print(f"    [{name}] {msg}")

    print_header("4. 输出目录结构")
    print_tree(output_dir)

    print_header("5. 配方生成结果（每个 tree 一个文件）")
    recipe_dir = output_dir / "recipe_generator"
    if recipe_dir.exists():
        for f in sorted(recipe_dir.iterdir()):
            if f.is_file():
                print_file(f, max_lines=6)

    print_header("6. 本地化结果（每个材质一个文件）")
    loc_dir = output_dir / "localizer"
    if loc_dir.exists():
        for f in sorted(loc_dir.iterdir()):
            if f.is_file():
                print_file(f, max_lines=8)

    print_header("7. 关键验证：crimson/warped 的 _log → _stem")
    crimson_file = loc_dir / "minecraft_crimson_localization.json"
    if crimson_file.exists():
        content = crimson_file.read_text(encoding="utf-8")
        if "_stem" in content:
            print("  ✅ crimson 含 _stem")
        else:
            print("  ❌ crimson 未含 _stem")
        if '"block.pfm.minecraft:crimson_log"' in content:
            print("  ❌ crimson 仍含 _log 键（后处理失败）")
        else:
            print("  ✅ crimson 无 _log 键残留")
    else:
        print(f"  ⚠️  文件不存在: {crimson_file}")

    print_header("完成")
    if report.has_failure:
        print("  ⚠️  有错误，请检查上方输出")
        sys.exit(1)
    else:
        print("  🎉 全部成功")


if __name__ == "__main__":
    main()