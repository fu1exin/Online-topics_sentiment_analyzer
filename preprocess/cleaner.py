"""
cleaner.py —— 评论文本清洗 + 质量过滤
去除 emoji、URL、@提及，过滤短评、表情包、无意义内容。
输入：raw JSON列表
输出：cleaned_comments.json
"""

import re
import json
import os
from config import CLEANED, RAW_COMMENTS, MIN_EFFECTIVE_CHARS, MAX_EMOJI_RATIO, TOPIC_KEYWORDS


# 纯重复字符模式（如 "哈哈哈哈"、"66666"）
_RE_REPEAT = re.compile(r"^(.)\1{3,}$")
# 纯标点/表情符
_RE_PUNCT_ONLY = re.compile(r"^[\W_]+$")


def clean_text(text):
    """清洗单条评论文本"""
    if not text:
        return ""

    # 1. 去除 URL
    text = re.sub(r"https?://\S+", "", text)
    # 2. 去除 @提及
    text = re.sub(r"@\S+", "", text)
    # 3. 去除 HTML标签
    text = re.sub(r"<[^>]+>", "", text)
    # 4. 去除 emoji 表情（保留中文、英文、数字、常见标点）
    text = re.sub(r"[^\u4e00-\u9fff\w\s.,!?;:。，！？；：…\-\+\=（）()【】《》\"\'…\n]", "", text)
    # 5. 合并多余空白
    text = re.sub(r"\s+", " ", text).strip()

    return text


def is_low_quality(text):
    """
    判断清洗后的文本是否为低质量评论。
    返回 True 表示应丢弃。
    """
    if not text:
        return True

    # ----- 1. 纯重复字符（如 "哈哈哈哈"、"6666"、"？？？"）
    if _RE_REPEAT.match(text):
        return True

    # ----- 2. 纯标点/符号
    if _RE_PUNCT_ONLY.match(text):
        return True

    # ----- 3. 有效中文字符数不足
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    if chinese_chars < MIN_EFFECTIVE_CHARS:
        return True

    # ----- 4. 非中文占比过高（表情包、火星文）
    total_chars = len(text.replace(" ", ""))
    if total_chars > 0:
        non_cn_ratio = 1.0 - (chinese_chars / total_chars)
        if non_cn_ratio > MAX_EMOJI_RATIO:
            return True

    # ----- 5. 话题关键词过滤（仅当配置了关键词时启用）
    if TOPIC_KEYWORDS:
        if not any(kw in text for kw in TOPIC_KEYWORDS):
            return True

    return False


def clean_comments(
    raw_path=RAW_COMMENTS,
    out_path=CLEANED,
):
    """
    读取原始评论JSON，清洗后写入 cleaned_comments.json。
    返回清洗后的评论列表（只保留 message 字段）。
    """
    if not os.path.exists(raw_path):
        print(f"[清洗] 文件不存在: {raw_path}，跳过")
        return []

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_list = json.load(f)

    cleaned = []
    discarded = 0
    for item in raw_list:
        msg = clean_text(item.get("message", ""))
        if not msg:
            discarded += 1
            continue
        # 质量过滤：短评、表情包、无意义内容
        if is_low_quality(msg):
            discarded += 1
            continue
        cleaned.append({
            "rpid": item.get("rpid"),
            "mid":  item.get("mid"),
            "message": msg,
            "like": item.get("like"),
        })

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"[清洗] 完成。{len(raw_list)} → {len(cleaned)} 条有效评论 (丢弃{discarded}条) → {out_path}")

    return cleaned


if __name__ == "__main__":
    clean_comments()
