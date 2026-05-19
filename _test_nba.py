"""NBA 话题完整测试 (跳过可视化以避免 numpy/Py313 崩溃)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.weibo_crawler import crawl_comments
from preprocess.cleaner import clean_comments
from preprocess.alias_resolver import resolve_comments
from preprocess.segmenter import segment_comments
from sentiment.analyzer import analyze_comments, analyze_per_entity

print("=" * 60)
print("  NBA 活塞vs骑士 舆情分析")
print("=" * 60)

# 1. 爬虫
print("\n[1/6] 爬取评论...")
comments = crawl_comments()
if not comments:
    print("[!] 无评论数据")
    exit(1)

# 2. 清洗
print("\n[2/6] 清洗...")
clean_comments()

# 3. 别名
print("\n[3/6] 别名归一化...")
resolve_comments()

# 4. 分词
print("\n[4/6] 分词...")
segment_comments()

# 5. 情感
print("\n[5/6] 情感分析...")
analyze_comments()

# 6. 实体
print("\n[6/6] 实体级情感...")
analyze_per_entity()

# 输出
import json
with open("data/sentiment_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)
es = data.get("entity_sentiment", {})
if es:
    print("\n" + "=" * 60)
    print("  NBA 球员情感总览")
    print("=" * 60)
    print(f"  {'球员':<12} {'提及':>4} {'正向':>5} {'中立':>5} {'负向':>5} {'均分':>6}")
    print(f"  {'-'*38}")
    for name in sorted(es, key=lambda n: es[n]["total"], reverse=True):
        e = es[name]
        print(f"  {name:<12} {e['total']:>4} {e['positive']:>5} {e['neutral']:>5} "
              f"{e['negative']:>5} {e['avg_score']:>6.3f}")
else:
    print("\n[!] 无实体数据—可能别名词典未匹配")
