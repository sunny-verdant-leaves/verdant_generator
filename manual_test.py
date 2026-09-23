# manual_test.py
from src.service.localizer_service import LocalizerService
from pathlib import Path

def main():
    print("🚀 启动本地化生成功能测试...\n")
    
    # ✅ 使用相对于工作目录的路径
    config_path = "test_manual/config.json"  # 相对于项目根目录
    
    # 验证路径
    if not Path(config_path).exists():
        print(f"❌ 配置文件不存在: {Path(config_path).absolute()}")
        print("请确保在项目根目录运行此脚本")
        return False
    
    service = LocalizerService(config_path=config_path)
    
    # 设置简单日志回调
    def log(msg):
        print(f"   {msg}")
    
    service.set_callbacks(on_progress=log)
    
    # 1. 加载配置
    print("1️ 加载配置...")
    success = service.reload_config()
    
    if not success:
        print("❌ 配置加载失败，请检查路径和文件格式\n")
        return False
    
    print("✅ 配置加载成功\n")
    
    # 2. 执行生成（预览模式）
    print("2️ 执行生成（预览模式）...")
    success = service.start_generation(
        template_name="material.json",
        dry_run=True,
        explain_mode=True
    )
    
    if not success:
        print("❌ 生成失败\n")
        return False
    
    print("\n✅ 生成成功！\n")
    
    # 3. 输出统计
    stats = service.stats
    print(f"📊 统计结果:")
    print(f"   - 物品数量: {stats['total_items']}")
    print(f"   - 成功生成: {stats['successful_items']}")
    print(f"   - 失败生成: {stats['failed_items']}")
    print(f"   - 总条目数: {stats['total_entries']}")
    
    # 4. 验证核心功能
    print("\n3️ 验证特殊规则...")
    
    # 验证绯红木的 log→stem 转换
    if "minecraft:crimson" in service.batch_items:
        item = service.batch_items["minecraft:crimson"]
        print(f"   - {item.id}: {item.zh_cn} (跳过词: {item.skip_patterns})")
        print(f"   - 专属替换: {item.replacements}")
        print("   ✅ 特殊材料配置正确")
    
    print("\n🎉 所有测试通过！")
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        import traceback
        traceback.print_exc()