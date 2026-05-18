"""
segmenter.py —— 中文分词 + 停用词过滤 + 词频统计
使用 jieba 分词，加载停用词表，输出高频词列表。
"""

import os
import json
import jieba
from collections import Counter
from config import STOPWORDS_FILE, JIEBA_USER_DICT


def load_stopwords(path=STOPWORDS_FILE):
    """加载停用词表，返回 set"""
    stopwords = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stopwords.add(line.strip())
    else:
        print(f"[分词] 停用词表不存在: {path}，使用空集")
    return stopwords


def segment_and_count(
    texts,
    stopwords=None,
    top_n=50,
):
    """
    对文本列表分词，去停用词，返回词频 Counter。
    
    参数:
        texts:     字符串列表
        stopwords: 停用词集合，默认从文件加载
        top_n:     返回前N个高频词
    返回:
        (counter, top_words_list)
    """
    if stopwords is None:
        stopwords = load_stopwords()

    # 可选：加载自定义词典
    if JIEBA_USER_DICT:
        jieba.load_userdict(JIEBA_USER_DICT)

    all_words = []
    for text in texts:
        # jieba 精确模式分词
        words = jieba.lcut(text)
        # 过滤：单字、纯数字、停用词
        words = [
            w for w in words
            if len(w) > 1
            and not w.isdigit()
            and w not in stopwords
        ]
        all_words.extend(words)

    counter = Counter(all_words)
    top_list = counter.most_common(top_n)

    return counter, top_list


def segment_comments(
    cleaned_path="data/cleaned_comments.json",
    out_path="data/word_freq.json",
):
    """
    读取清洗后的评论，分词统计，输出高频词JSON。
    """
    if not os.path.exists(cleaned_path):
        print(f"[分词] 文件不存在: {cleaned_path}")
        return None, []

    with open(cleaned_path, "r", encoding="utf-8") as f:
        comments = json.load(f)

    texts = [item["message"] for item in comments]
    stopwords = load_stopwords()
    counter, top_list = segment_and_count(texts, stopwords)

    # 写出词频文件
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    freq_data = [{"word": w, "count": c} for w, c in top_list]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(freq_data, f, ensure_ascii=False, indent=2)

    print(f"[分词] 完成。总词数 {sum(counter.values())}, 不重复词 {len(counter)}")
    print(f"  TOP 10: {top_list[:10]}")

    return counter, top_list


if __name__ == "__main__":
    segment_comments()
