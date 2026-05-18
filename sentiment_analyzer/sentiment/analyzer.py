"""
analyzer.py —— 情感分析模块
使用 SnowNLP 对每条评论打分，按阈值三分类，选出极值评论。
支持 ECDF（经验累积分布）权重：按点赞分位数加权，免疫极端值。
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


def _compute_ecdf_weights(likes):
    """
    计算 ECDF 分位数权重。
    输入: 点赞数列表
    输出: 等长权重列表，每个值 = (rank+1)/n，范围 (0, 1]
    
    ECDF 使权重在 [0,1] 间近似均匀分布，天然免疫极端点赞数。
    """
    n = len(likes)
    if n == 0:
        return []
    indexed = [(likes[i], i) for i in range(n)]
    sorted_pairs = sorted(indexed, key=lambda x: x[0])
    weights = [0.0] * n
    for rank, (_, idx) in enumerate(sorted_pairs):
        weights[idx] = (rank + 1) / n      # rank+1 避免最小值为 0
    return weights


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
            "like": item.get("like", 0),
        })
        stats[label] += 1

    # ===== ECDF 权重 =====
    likes = [r["like"] for r in results]
    ecdf_weights = _compute_ecdf_weights(likes)

    weighted_stats = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
    for i, r in enumerate(results):
        w = ecdf_weights[i]
        r["weight"] = round(w, 4)
        weighted_stats[r["label"]] += w

    total_weight = sum(weighted_stats.values())

    # 找极值评论（按情感得分）
    sorted_asc = sorted(results, key=lambda x: x["score"])
    most_negative = sorted_asc[:5]
    most_positive = sorted(results, key=lambda x: x["score"], reverse=True)[:5]

    # 找高赞评论
    most_liked = sorted(results, key=lambda x: x["like"], reverse=True)[:5]

    # 写出结果
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    output = {
        "stats": stats,
        "weighted_stats": {k: round(v, 2) for k, v in weighted_stats.items()},
        "total_weight": round(total_weight, 2),
        "total": len(results),
        "most_positive": most_positive,
        "most_negative": most_negative,
        "most_liked": most_liked,
        "all": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = len(results)
    print(f"[情感] 完成。共 {total} 条")
    if total > 0:
        print(f"  -- 原始数量 --")
        print(f"  正向: {stats['positive']} ({stats['positive']/total*100:.1f}%)")
        print(f"  中立: {stats['neutral']} ({stats['neutral']/total*100:.1f}%)")
        print(f"  负向: {stats['negative']} ({stats['negative']/total*100:.1f}%)")
        print(f"  -- ECDF加权 (点赞越多权重越大) --")
        print(f"  正向: {weighted_stats['positive']:.1f} ({weighted_stats['positive']/total_weight*100:.1f}%)")
        print(f"  中立: {weighted_stats['neutral']:.1f} ({weighted_stats['neutral']/total_weight*100:.1f}%)")
        print(f"  负向: {weighted_stats['negative']:.1f} ({weighted_stats['negative']/total_weight*100:.1f}%)")
        print(f"\n  最正面评论示例 (情感得分最高):")
        for c in most_positive[:3]:
            print(f"    [{c['score']:.4f}] 赞{c['like']} w={c['weight']:.2f} {c['message'][:44]}...")
        print(f"\n  最负面评论示例 (情感得分最低):")
        for c in most_negative[:3]:
            print(f"    [{c['score']:.4f}] 赞{c['like']} w={c['weight']:.2f} {c['message'][:44]}...")
        print(f"\n  最高赞评论:")
        for c in most_liked[:3]:
            print(f"    赞{c['like']} w={c['weight']:.2f} [{c['score']:.4f}] {c['message'][:44]}...")
    else:
        print("  [!] 无评论数据，请检查爬虫是否获取到数据")

    return results, stats, weighted_stats


if __name__ == "__main__":
    analyze_comments()
