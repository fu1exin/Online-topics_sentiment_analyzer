"""
visualize 包 —— 可视化模块
pie_chart.py    情感分布饼图
wordcloud_gen.py 正向/负向词云
"""

import os
import json
import matplotlib
matplotlib.use("Agg")                   # 非交互后端，适合脚本
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from config import FONT_PATH, OUTPUT_DIR, PIE_COLORS


# ============================================================
# 饼图
# ============================================================

def draw_pie_chart(results_path="data/sentiment_results.json"):
    """
    读取情感分析结果，绘制原始 + ECDF加权 双饼图。
    输出: output/pie_chart.png
    """
    if not os.path.exists(results_path):
        print("[可视化] sentiment_results.json 不存在，跳过饼图")
        return

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False

    labels = ["正向", "中立", "负向"]
    raw_stats = data["stats"]
    raw_sizes = [raw_stats["positive"], raw_stats["neutral"], raw_stats["negative"]]

    w_stats = data.get("weighted_stats", raw_stats)
    w_sizes = [w_stats["positive"], w_stats["neutral"], w_stats["negative"]]
    total_w = data.get("total_weight", data["total"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

    # 左：原始计数
    ax1.pie(raw_sizes, labels=labels, colors=PIE_COLORS,
            autopct="%1.1f%%", startangle=90, pctdistance=0.6,
            textprops={"fontsize": 13})
    ax1.set_title(f"原始分布 (共 {data['total']} 条)", fontsize=15, pad=16)

    # 右：ECDF加权
    ax2.pie(w_sizes, labels=labels, colors=PIE_COLORS,
            autopct="%1.1f%%", startangle=90, pctdistance=0.6,
            textprops={"fontsize": 13})
    ax2.set_title(f"ECDF加权 (总权 {total_w:.0f})", fontsize=15, pad=16)

    fig.suptitle("评论情感分布对比", fontsize=17, y=1.02)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "pie_chart.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[可视化] 双饼图 (原始+加权) -> {out_path}")


# ============================================================
# 词云
# ============================================================

def _build_wordcloud(texts, out_name, colormap):
    """
    内部: 用 texts 列表生成词云图。
    """
    if not texts:
        print(f"[可视化] 词云数据为空，跳过 {out_name}")
        return

    corpus = " ".join(texts)
    wc = WordCloud(
        font_path=FONT_PATH,
        width=800,
        height=600,
        background_color="white",
        colormap=colormap,
        max_words=100,
        scale=2,
    ).generate(corpus)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, out_name)
    wc.to_file(out_path)
    print(f"[可视化] 词云 → {out_path}")


def draw_wordclouds(
    results_path="data/sentiment_results.json",
    cleaned_path="data/cleaned_comments.json",
):
    """
    读取情感分析结果和清洗后评论，生成正向/负向词云。
    输出: output/wordcloud_positive.png
          output/wordcloud_negative.png
    """
    if not os.path.exists(results_path) or not os.path.exists(cleaned_path):
        print("[可视化] 数据文件不全，跳过词云")
        return

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pos_texts = [item["message"] for item in data["all"] if item["label"] == "positive"]
    neg_texts = [item["message"] for item in data["all"] if item["label"] == "negative"]

    print(f"[可视化] 生成词云：正向 {len(pos_texts)} 条，负向 {len(neg_texts)} 条")
    _build_wordcloud(pos_texts, "wordcloud_positive.png", "Greens")
    _build_wordcloud(neg_texts, "wordcloud_negative.png", "Reds")


# ============================================================
# 实体情感柱状图
# ============================================================

def draw_entity_chart(results_path="data/sentiment_results.json"):
    """
    读取 sentiment_results.json 中的 entity_sentiment，绘制实体情感对比柱状图。
    输出: output/entity_sentiment.png
    """
    if not os.path.exists(results_path):
        print("[可视化] sentiment_results.json 不存在，跳过实体图")
        return

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entity_stats = data.get("entity_sentiment", {})
    if not entity_stats:
        print("[可视化] 无 entity_sentiment 数据，跳过")
        return

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False

    # 按提及次数排序，取前12
    sorted_entities = sorted(entity_stats.items(), key=lambda x: x[1]["total"], reverse=True)[:12]
    names = [e[0] for e in sorted_entities]
    pos_vals = [e[1]["positive"] / e[1]["total"] * 100 for e in sorted_entities]
    neu_vals = [e[1]["neutral"] / e[1]["total"] * 100 for e in sorted_entities]
    neg_vals = [e[1]["negative"] / e[1]["total"] * 100 for e in sorted_entities]

    x = range(len(names))
    fig, ax = plt.subplots(figsize=(12, 5))

    bar_w = 0.55
    p1 = ax.bar(x, pos_vals, bar_w, color=PIE_COLORS[0], label="正向")
    p2 = ax.bar(x, neu_vals, bar_w, bottom=pos_vals, color=PIE_COLORS[1], label="中立")
    p3 = ax.bar(x, neg_vals, bar_w, bottom=[a + b for a, b in zip(pos_vals, neu_vals)], color=PIE_COLORS[2], label="负向")

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=30, ha="right", fontsize=11)
    ax.set_ylabel("占比 (%)", fontsize=13)
    ax.set_title("各实体评论情感分布", fontsize=16)
    ax.legend(loc="upper right", fontsize=11)
    ax.set_ylim(0, 105)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "entity_sentiment.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[可视化] 实体情感图 -> {out_path}")


if __name__ == "__main__":
    draw_pie_chart()
    draw_wordclouds()
