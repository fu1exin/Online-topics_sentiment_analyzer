from sentiment.analyzer import analyze_comments, analyze_per_entity

analyze_comments()
analyze_per_entity()
print("\n=== 实体情感统计 ===")
import json
with open("data/sentiment_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)
es = data.get("entity_sentiment", {})
for name in sorted(es, key=lambda n: es[n]["total"], reverse=True):
    e = es[name]
    print(f"  {name:<14} 提及{e['total']:>3}  正向{e['positive']:>3}  中立{e['neutral']:>3}  负向{e['negative']:>3}  均分{e['avg_score']:.3f}")
