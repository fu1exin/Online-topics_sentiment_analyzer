"""
main.py —— 舆情洞察员项目入口
按数据流依次执行：爬虫 → 清洗 → 分词 → 情感 → 可视化
"""

import os
import sys

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.weibo_crawler import crawl_comments
from preprocess.cleaner import clean_comments
from preprocess.segmenter import segment_comments
from sentiment.analyzer import analyze_comments
from visualize.pie_chart import draw_pie_chart, draw_wordclouds


def main():
    print("=" * 60)
    print("  舆情洞察员 —— 评论情感分析流水线")
    print("=" * 60)

    # 1. 爬虫
    print("\n[1/5] 爬取评论...")
    comments = crawl_comments()
    if not comments:
        print("\n[!] 未抓到任何评论。请修改 config.py 中 BILIBILI_OIDS 列表，填入至少一个视频的 aid。")
        print("    获取方法：打开B站视频 -> 地址栏 BV 号 ->")
        print("    https://api.bilibili.com/x/web-interface/view?bvid=BVxxxxx -> data.aid")
        return

    # 2. 清洗
    print("\n[2/5] 清洗文本...")
    clean_comments()

    # 3. 分词 + 词频
    print("\n[3/5] 分词统计...")
    segment_comments()

    # 4. 情感分析
    print("\n[4/5] 情感分析...")
    analyze_comments()  # 返回 (results, stats, weighted_stats)

    # 5. 可视化
    print("\n[5/5] 生成图表...")
    draw_pie_chart()
    draw_wordclouds()

    print("\n" + "=" * 60)
    print("  全流程完成！请查看 output/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()
