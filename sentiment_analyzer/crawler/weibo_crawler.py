"""
weibo_crawler.py —— B站视频评论区爬虫
通过 Bilibili API 分页抓取评论，支持多视频同一话题汇总。
输出：data/raw_comments.json
"""

import json
import time
import os
from datetime import datetime, timedelta
import requests
from config import (
    BILIBILI_OIDS, BILIBILI_COMMENT_API, HEADERS,
    TARGET_COUNT, COMMENT_DAYS_LIMIT,
)


def _crawl_one_video(oid, per_count, cutoff_ts):
    """抓取单个视频的评论，最多 per_count 条。只保留 cutoff_ts 之后的评论。返回列表。"""
    comments = []
    page = 1
    skipped = 0
    max_pages = 50                      # 防止空转

    print(f"  [视频 oid={oid}] 开始抓取，目标 {per_count} 条，时间要求 >= {datetime.fromtimestamp(cutoff_ts):%Y-%m-%d}...")

    while len(comments) < per_count and page <= max_pages:
        params = {
            "oid": oid,
            "type": 1,
            "mode": 2,              # 2=按时间排序（稳定分页），3=按热度（易重复）
            "pn": page,
            "ps": 20,
        }
        try:
            resp = requests.get(BILIBILI_COMMENT_API, params=params, headers=HEADERS, timeout=10)
            data = resp.json()
        except Exception as e:
            print(f"    第{page}页请求失败: {e}")
            break

        if data.get("code") != 0:
            print(f"    API返回错误: {data.get('message')}")
            break

        replies = data.get("data", {}).get("replies")
        if not replies:
            print(f"    第{page}页无评论")
            break

        for item in replies:
            ctime = item.get("ctime", 0)
            # 时间过滤：只保留近 N 天的评论
            if ctime < cutoff_ts:
                skipped += 1
                continue
            comments.append({
                "rpid":    item.get("rpid"),
                "mid":     item.get("mid"),
                "message": item.get("content", {}).get("message", ""),
                "ctime":   ctime,
                "like":    item.get("like"),
                "oid":     oid,
            })

        print(f"    第{page}页 +{len(replies)}条 (跳过{skipped}条旧评), 累计 {len(comments)}/{per_count}")
        page += 1
        time.sleep(0.5)

    return comments[:per_count]


def crawl_comments(oids=None, target_count=None, out_path="data/raw_comments.json"):
    """
    抓取多个 B站视频的评论，合并去重。
    
    参数:
        oids:         aid 列表，默认从 config 读取
        target_count: 总目标评论数，默认从 config 读取，多视频之间平均分配
        out_path:     输出JSON路径
    
    返回: 合并后的评论列表
    """
    oids = oids or BILIBILI_OIDS
    target_count = target_count or TARGET_COUNT

    if not oids:
        print("[爬虫] 未配置任何视频 oid！请在 config.py 的 BILIBILI_OIDS 中添加至少一个 aid。")
        return []

    # 计算时间截止点（Unix 时间戳）
    cutoff_ts = int((datetime.now() - timedelta(days=COMMENT_DAYS_LIMIT)).timestamp())

    per_video = max(1, target_count // len(oids))
    print(f"[爬虫] 话题分析模式：{len(oids)} 个视频，总计目标 {target_count} 条，每视频约 {per_video} 条")
    print(f"[爬虫] 时间过滤：只保留 {COMMENT_DAYS_LIMIT} 天内的评论")

    all_comments = []
    seen_rpid = set()

    for idx, oid in enumerate(oids, 1):
        print(f"\n[爬虫] [{idx}/{len(oids)}] 抓取视频 oid={oid}")
        video_comments = _crawl_one_video(oid, per_video, cutoff_ts)
        # 去重（不同视频理论上 rpid 不重复，但做防御性去重）
        for c in video_comments:
            if c["rpid"] not in seen_rpid:
                seen_rpid.add(c["rpid"])
                all_comments.append(c)
        print(f"  该视频有效 {len(video_comments)} 条, 累计 {len(all_comments)}/{target_count}")

    # 写入 JSON
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_comments, f, ensure_ascii=False, indent=2)

    print(f"\n[爬虫] 完成。{len(oids)} 个视频共抓取 {len(all_comments)} 条评论 → {out_path}")
    return all_comments


if __name__ == "__main__":
    crawl_comments()
