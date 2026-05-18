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
    读取情感分析结果，绘制情感分布饼图。
    输出: output/pie_chart.png
    """
    if not os.path.exists(results_path):
        print("[可视化] sentiment_results.json 不存在，跳过饼图")
        return

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = data["stats"]
    labels = ["正向", "中立", "负向"]
    sizes = [stats["positive"], stats["neutral"], stats["negative"]]

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=PIE_COLORS,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.6,
    )
    for t in autotexts:
        t.set_fontsize(14)
    for t in texts:
        t.set_fontsize(14)

    ax.set_title(f"评论情感分布 (共{data['total']}条)", fontsize=16, pad=20)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "pie_chart.png")
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[可视化] 饼图 → {out_path}")


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


if __name__ == "__main__":
    draw_pie_chart()
    draw_wordclouds()
