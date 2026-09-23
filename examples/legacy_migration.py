"""旧配置迁移脚本。

用法：
    python examples/legacy_migration.py <旧配置.json> [输出.json]

自动识别 type：
    "material_id" → localizer 插件（需要 material_zh_cn）
    "tree"        → recipe_generator 插件（只需要 tree ID）

关键规则：
    - 每组的 extra["*"] 只对本组的材质生效（不做全局合并）
    - 材质专属规则 = 本组通配规则 + 材质自己的规则（后者覆盖前者）
    - extra 的 key 先查短名，再查完整 ID
"""
import json
import sys
from pathlib import Path


def _split_id(full_id: str, default_ns: str):
    """拆分完整 ID → (短名, 命名空间)。命名空间不带冒号。"""
    if ":" in full_id:
        ns, short = full_id.split(":", 1)
    else:
        ns, short = default_ns.rstrip(":"), full_id
    return short, ns


def _normalize_ns(ns: str) -> str:
    """去掉尾部冒号。"""
    return ns.rstrip(":")


def _extract_zh(extra: dict, short: str, full: str) -> str:
    """从 extra 提取中文名。先查短名，再查完整 ID。"""
    for key in (short, full):
        if key in extra and "material_zh_cn" in extra[key]:
            return extra[key]["material_zh_cn"]
    return ""


def _extract_rules(extra: dict, short: str, full: str) -> dict:
    """从 extra 提取材质专属替换（去掉 material_zh_cn）。
    先查短名，再查完整 ID。
    """
    rules = extra.get(short) or extra.get(full) or {}
    return {k: v for k, v in rules.items() if k != "material_zh_cn"}


def migrate(old: dict) -> dict:
    default_ns = old.get("default_namespace", "minecraft:") or "minecraft:"
    default_ns_clean = _normalize_ns(default_ns)
    template_dir = old.get("template_dir", ".")
    template_files = old.get("template_files", [])

    materials = {}       # {完整 ID: 中文名}
    all_ids = []         # 所有出现过的完整 ID（保序去重）
    per_material = {}    # {短名: {old: new}}，组通配 + 专属规则合并
    all_types = set()

    for group in old.get("replacements", []):
        all_types.add(group.get("type", ""))
        extra = group.get("extra", {})

        # 本组通配规则：只作用于本组材质
        group_wildcard = dict(extra.get("*", {}))

        for full_id in group.get("values", []):
            if full_id not in all_ids:
                all_ids.append(full_id)

            short, _ = _split_id(full_id, default_ns_clean)

            zh = _extract_zh(extra, short, full_id)
            if zh:
                materials[full_id] = zh

            # 材质最终规则 = 组通配 + 材质专属（专属覆盖通配）
            own_rules = _extract_rules(extra, short, full_id)
            merged = {**group_wildcard, **own_rules}
            if merged:
                per_material[short] = merged

    # 决定插件类型
    if "material_id" in all_types:
        plugin_type = "localizer"
    elif "tree" in all_types:
        plugin_type = "recipe_generator"
    else:
        raise ValueError(f"无法识别的 type: {all_types}")

    # 每个 template_file 生成一个插件
    plugins = []
    for tpl_file in template_files:
        tpl_path = str(Path(template_dir) / tpl_file).replace("\\", "/")

        if plugin_type == "localizer":
            plugin = {
                "type": "localizer",
                "template": tpl_path,
                "output_name": tpl_file,
                "default_namespace": default_ns_clean,
                "materials": materials,
                "replacements": {},                 # 不再用全局替换
                "per_material_replacements": per_material,
            }
        else:  # recipe_generator
            plugin = {
                "type": "recipe_generator",
                "template": tpl_path,
                "output_name": tpl_file,
                "default_namespace": default_ns_clean,
                "trees": all_ids,
            }
        plugins.append(plugin)

    return {"plugins": plugins}


def main():
    if len(sys.argv) < 2:
        print("用法: python legacy_migration.py <旧配置.json> [输出.json]")
        sys.exit(1)

    old_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("config_new.json")

    if not old_path.exists():
        print(f"❌ 旧配置不存在: {old_path}")
        sys.exit(1)

    old = json.loads(old_path.read_text(encoding="utf-8"))
    new = migrate(old)
    out_path.write_text(
        json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"✅ 生成新配置: {out_path}")
    print(f"   插件数量: {len(new['plugins'])}")
    for p in new["plugins"]:
        n = len(p.get("materials", p.get("trees", [])))
        print(f"   - {p['type']} | template={p['template']} | 材质/树={n}")


if __name__ == "__main__":
    main()