"""
analyzer.py —— 情感分析模块
使用 SnowNLP 对每条评论打分，按阈值三分类，选出极值评论。
"""

import json
import os
from snownlp import SnowNLP
from config import POSITIVE_THRESHOLD, NEGATIVE_THRESHOLD


def analyze_single(text):
    """
    对单条文本打分。
    返回: (score, label)
      score: 0~1 浮点数
      label: "positive" / "neutral" / "negative"
    """
    try:
        s = SnowNLP(text)
        score = s.sentiments
    except Exception:
        score = 0.5  # 异常时视为中立

    if score >= POSITIVE_THRESHOLD:
        label = "positive"
    elif score <= NEGATIVE_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"

    return score, label


def analyze_comments(
    cleaned_path="data/cleaned_comments.json",
    out_path="data/sentiment_results.json",
):
    """
    读取清洗后评论，逐条情感打分+分类。
    返回: (results_list, stats_dict)
    """
    if not os.path.exists(cleaned_path):
        print(f"[情感] 文件不存在: {cleaned_path}")
        return [], {}

    with open(cleaned_path, "r", encoding="utf-8") as f:
        comments = json.load(f)

    results = []
    stats = {"positive": 0, "neutral": 0, "negative": 0}

    for item in comments:
        text = item["message"]
        score, label = analyze_single(text)
        results.append({
            "message": text,
            "score": round(score, 4),
            "label": label,
        })
        stats[label] += 1

    # 找极值评论
    sorted_asc = sorted(results, key=lambda x: x["score"])
    most_negative = sorted_asc[:5]
    most_positive = sorted(results, key=lambda x: x["score"], reverse=True)[:5]

    # 写出结果
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    output = {
        "stats": stats,
        "total": len(results),
        "most_positive": most_positive,
        "most_negative": most_negative,
        "all": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = len(results)
    print(f"[情感] 完成。共 {total} 条")
    if total > 0:
        print(f"  正向: {stats['positive']} ({stats['positive']/total*100:.1f}%)")
        print(f"  中立: {stats['neutral']} ({stats['neutral']/total*100:.1f}%)")
        print(f"  负向: {stats['negative']} ({stats['negative']/total*100:.1f}%)")
        print(f"\n  最正面评论示例:")
        for c in most_positive[:3]:
            print(f"    [{c['score']:.4f}] {c['message'][:50]}...")
        print(f"\n  最负面评论示例:")
        for c in most_negative[:3]:
            print(f"    [{c['score']:.4f}] {c['message'][:50]}...")
    else:
        print("  [!] 无评论数据，请检查爬虫是否获取到数据")

    return results, stats


if __name__ == "__main__":
    analyze_comments()
