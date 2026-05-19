"""
segmenter.py —— 中文分词 + 停用词过滤 + 词频统计
使用 jieba 分词，加载停用词表，输出高频词列表。
"""

import os
import json
from collections import Counter
from config import STOPWORDS_FILE, JIEBA_USER_DICT, SEGMENTER_BACKEND, PKUSEG_MODEL

# 延迟加载分词器
_segger = None


def _get_segger():
    """获取当前分词后端实例"""
    global _segger
    if _segger is not None:
        return _segger

    if SEGMENTER_BACKEND == "pkuseg":
        try:
            import pkuseg
            _segger = pkuseg.pkuseg(model_name=PKUSEG_MODEL)
            print(f"[分词] 使用 pkuseg ({PKUSEG_MODEL})")
        except ImportError:
            print("[分词] pkuseg 未安装，回退到 jieba")
            import jieba
            _segger = jieba
    else:
        import jieba
        _segger = jieba
        print("[分词] 使用 jieba")

    return _segger


def _cut_words(text):
    """对单条文本分词，自动选择后端"""
    seg = _get_segger()
    if SEGMENTER_BACKEND == "pkuseg" and hasattr(seg, "cut"):
        return seg.cut(text)
    else:
        import jieba
        return jieba.lcut(text)


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

    # 可选：加载自定义词典（仅 jieba 后端有效）
    if JIEBA_USER_DICT and SEGMENTER_BACKEND == "jieba":
        import jieba
        jieba.load_userdict(JIEBA_USER_DICT)

    all_words = []
    for text in texts:
        words = _cut_words(text)
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
