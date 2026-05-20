"""
analyzer.py —— 情感分析模块
使用 SnowNLP 对每条评论打分，按阈值三分类，选出极值评论。
支持 ECDF（经验累积分布）权重：按点赞分位数加权，免疫极端值。
"""

import json
import os
from config import (
    CLEANED, SENTIMENT, ALIAS_DICT,
    POSITIVE_THRESHOLD, NEGATIVE_THRESHOLD,
    SENTIMENT_BACKEND,
)


def analyze_single(text):
    """
    对单条文本打分。根据 SENTIMENT_BACKEND 自动选择引擎。
    返回: (score, label)
      score: 0~1 浮点数
      label: "positive" / "neutral" / "negative"
    """
    try:
        if SENTIMENT_BACKEND == "cntext":
            score = _cntext_score(text)
        else:
            from snownlp import SnowNLP
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


def _cntext_score(text):
    """
    cntext 情感打分（备选后端）。
    安装: pip install cntext
    项目: https://github.com/hiDaDeng/cntext
    """
    try:
        import cntext as ct
        d = ct.sentiment(text)
        # cntext 返回 {positive: N, negative: N, ...}
        pos = d.get("positive", 0)
        neg = d.get("negative", 0)
        total = pos + neg
        if total == 0:
            return 0.5
        return pos / total
    except ImportError:
        from snownlp import SnowNLP
        return SnowNLP(text).sentiments


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
    cleaned_path=CLEANED,
    out_path=SENTIMENT,
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


def analyze_per_entity(
    results_path=SENTIMENT,
    alias_dict_path=ALIAS_DICT,
):
    """
    按实体拆分情感：对每条评论中的每个实体提取上下文窗口独立打分。
    输出: 追加 entity_sentiment 字段到 sentiment_results.json
    返回: {entity_name: {positive, neutral, negative, total, avg_score}}
    """
    import json as _json
    if not os.path.exists(results_path):
        print("[实体情感] sentiment_results.json 不存在")
        return {}

    entities = {}
    if os.path.exists(alias_dict_path):
        with open(alias_dict_path, "r", encoding="utf-8") as f:
            ad = _json.load(f)
        for key, val in ad.items():
            if key.startswith("_"):
                continue
            canonical = val["canonical"]
            entities[canonical] = {
                "aliases": [canonical] + val.get("aliases", []),
            }

    if not entities:
        print("[实体情感] 别名词典为空，跳过实体级分析")
        return {}

    with open(results_path, "r", encoding="utf-8") as f:
        data = _json.load(f)

    entity_stats = {}
    for canon, info in entities.items():
        stats = {"positive": 0, "neutral": 0, "negative": 0, "scores": []}
        search_terms = info["aliases"]

        for item in data["all"]:
            text = item["message"]
            mentioned = False
            context = text
            for term in search_terms:
                idx = text.find(term)
                if idx >= 0:
                    mentioned = True
                    start = max(0, idx - 30)
                    end = min(len(text), idx + len(term) + 30)
                    context = text[start:end]
                    break

            if mentioned:
                score, label = analyze_single(context)
                stats[label] += 1
                stats["scores"].append(score)

        total = sum(stats[k] for k in ["positive", "neutral", "negative"])
        if total > 0:
            entity_stats[canon] = {
                "positive": stats["positive"],
                "neutral": stats["neutral"],
                "negative": stats["negative"],
                "total": total,
                "avg_score": round(sum(stats["scores"]) / len(stats["scores"]), 4),
            }

    data["entity_sentiment"] = entity_stats
    with open(results_path, "w", encoding="utf-8") as f:
        _json.dump(data, f, ensure_ascii=False, indent=2)

    total = len(entity_stats)
    print(f"[实体情感] 完成。{total} 个实体的独立情感分析")
    if entity_stats:
        print(f"  {'实体':<12} {'总':>4} {'正向':>5} {'中立':>5} {'负向':>5} {'均分':>6}")
        print(f"  {'-'*38}")
        sorted_entities = sorted(entity_stats.items(), key=lambda x: x[1]["total"], reverse=True)
        for name, es in sorted_entities:
            print(f"  {name:<12} {es['total']:>4} {es['positive']:>5} {es['neutral']:>5} "
                  f"{es['negative']:>5} {es['avg_score']:>6.3f}")

    return entity_stats


if __name__ == "__main__":
    analyze_comments()
