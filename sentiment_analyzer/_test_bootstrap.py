"""冷启动测试"""
from preprocess.alias_resolver import resolve_comments

# 保存原始
import json, shutil
shutil.copy("data/cleaned_comments.json", "data/cleaned_before_bootstrap.json")

# 空词典自举
texts, resolver, discoveries = resolve_comments(
    "data/cleaned_comments.json",
    auto_save=False,
)

stats = resolver.get_stats()
print(f"\n=== L0自举结果 ===")
print(f"实体: {stats['entities']}, 别名总数: {stats['total_aliases']}")
for key, entry in resolver.entries.items():
    print(f"  [{entry['source']}] {entry['canonical']} <- {entry['aliases']}")

# 恢复原始数据
shutil.copy("data/cleaned_before_bootstrap.json", "data/cleaned_comments.json")
print("\n--- 已恢复原始数据 ---")
