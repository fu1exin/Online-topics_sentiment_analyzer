"""
hupu_crawler.py —— 虎扑社区评论爬虫
虎扑页面为 JS 客户端渲染，两种方案:
  A) Selenium 渲染后解析 (推荐，需 chromedriver)
  B) 抓包 App API (需逆向 sign 参数)

当前实现: Selenium 方案，自动降级到 HTML 静态解析。
"""

import json
import os
import time
import re
import requests
from config import (
    HUPU_TOPIC_IDS, HEADERS, TARGET_COUNT,
    RAW_COMMENTS,
)


def _extract_from_html(html):
    """从虎扑 HTML 页面中提取评论（降级方案）"""
    comments = []
    # 虎扑页面中评论可能嵌入在特定标签中
    patterns = [
        r'<div[^>]*class="[^"]*reply-content[^"]*"[^>]*>(.*?)</div>',
        r'<p[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</p>',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        for m in matches:
            text = re.sub(r'<[^>]+>', '', m).strip()
            if len(text) > 2 and text not in comments:
                comments.append(text)
        if comments:
            break
    return comments


def crawl_hupu_comments_selenium(topic_id, per_count, out_path=RAW_COMMENTS):
    """
    使用 Selenium 爬取虎扑帖子评论。
    需要: pip install selenium + chromedriver
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        print("[虎扑] selenium 未安装，回退到静态HTML解析。pip install selenium")
        return crawl_hupu_comments_static(topic_id, per_count, out_path)

    print(f"[虎扑] Selenium 模式: topicId={topic_id}")

    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument(f"user-agent={HEADERS['User-Agent']}")

    try:
        driver = webdriver.Chrome(options=opts)
    except Exception as e:
        print(f"[虎扑] Chrome driver 启动失败: {e}")
        return crawl_hupu_comments_static(topic_id, per_count, out_path)

    all_comments = []
    page = 1

    try:
        while len(all_comments) < per_count:
            url = f"https://bbs.hupu.com/{topic_id}-{page}.html"
            driver.get(url)
            time.sleep(2)  # 等待 JS 渲染

            # 找评论元素
            replies = driver.find_elements(By.CSS_SELECTOR, ".reply-content, .post-reply")
            if not replies:
                print(f"   第{page}页无评论")
                break

            for el in replies:
                text = el.text.strip()
                if text:
                    all_comments.append({
                        "message": text,
                        "like": 0,
                        "ctime": 0,
                        "platform": "hupu",
                        "topic_id": topic_id,
                    })

            print(f"   第{page}页 +{len(replies)}条, 累计 {len(all_comments)}/{per_count}")
            page += 1
            time.sleep(1)

    finally:
        driver.quit()

    # 写出 JSON
    return _write_output(all_comments[:per_count], out_path)


def crawl_hupu_comments_static(topic_id, per_count, out_path=RAW_COMMENTS):
    """静态 HTML 解析（降级方案）"""
    print(f"[虎扑] 静态解析模式: topicId={topic_id}")

    all_comments = []
    for page in range(1, 6):
        url = f"https://bbs.hupu.com/{topic_id}-{page}.html"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
        except Exception as e:
            print(f"   第{page}页失败: {e}")
            break

        comments = _extract_from_html(resp.text)
        if not comments:
            print(f"   第{page}页无评论（可能需Selenium渲染）")
            break

        for text in comments:
            all_comments.append({
                "message": text,
                "like": 0,
                "ctime": 0,
                "platform": "hupu",
                "topic_id": topic_id,
            })

        print(f"   第{page}页 +{len(comments)}条, 累计 {len(all_comments)}/{per_count}")
        if len(all_comments) >= per_count:
            break
        time.sleep(0.5)

    return _write_output(all_comments[:per_count], out_path)


def _write_output(comments, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"[虎扑] 完成。抓取 {len(comments)} 条评论 → {out_path}")
    return comments


def crawl_comments(topic_ids=None, target_count=None, out_path=RAW_COMMENTS):
    """
    虎扑爬虫入口（兼容多平台统一接口）。
    """
    topic_ids = topic_ids or HUPU_TOPIC_IDS
    target_count = target_count or TARGET_COUNT

    if not topic_ids:
        print("[虎扑] 未配置 HUPU_TOPIC_IDS")
        return []

    per_topic = max(1, target_count // len(topic_ids))
    print(f"[虎扑] 爬取 {len(topic_ids)} 个帖子, 目标 {target_count} 条")

    all_comments = []
    for tid in topic_ids:
        print(f"\n[虎扑] 帖子 {tid}")
        comments = crawl_hupu_comments_selenium(tid, per_topic, out_path)
        all_comments.extend(comments)

    return all_comments