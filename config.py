"""
config.py —— 舆情洞察员项目全局配置
所有可调参数集中于此，禁止在其他模块中硬编码。
"""

from pathlib import Path

# 项目根目录锚点（config.py 所在目录 = sentiment_analyzer/）
BASE_DIR = Path(__file__).parent.resolve()

# ============================================================
# 爬虫配置
# ============================================================
# B站视频评论区API（支持同一话题多个视频）
# oid = 视频的数字 aid（不是 BV 号）
# 获取方法：打开B站视频 → 地址栏 /video/BVxxxxx → 把 BV 号贴到
#   https://api.bilibili.com/x/web-interface/view?bvid=BVxxxxx
#   返回的 data.aid 就是 oid，加到下面列表。
BILIBILI_OIDS = [                     # NBA季后赛 活塞4:3骑士 核心球员评价
    "116593329773534",   # 骑士4:3活塞！重返季后赛 (12272播放)
    "116595309413990",   # G7骑士活塞全场集锦 (9920播放)
    "116596383220174",   # 火箭队CC出局分析 (6228播放)
    "116595024204121",   # 裁判吹罚G7骑士vs活塞 (4018播放)
    "116587407478917",   # 5月17日骑士VS活塞预测 (8884播放)
    "116588162326374",   # 5.18NBA季后赛预测骑士vs活塞 (2687播放)
]
TARGET_COUNT = 1000                   # 总目标评论数（多视频之间平均分配）
BILIBILI_COMMENT_API = "https://api.bilibili.com/x/v2/reply/main"

# ============================================================
# 平台选择 ("bilibili" | "hupu")
# ============================================================
CRAWL_PLATFORM = "bilibili"

# 虎扑帖子ID列表
HUPU_TOPIC_IDS = [
    # "631246614",
]

# 请求头（模拟浏览器）
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
}

# ============================================================
# 时间 & 质量过滤配置
# ============================================================
COMMENT_DAYS_LIMIT = 30                # 只保留近N天的评论（热门话题时效性）
MIN_EFFECTIVE_CHARS = 4                # 清洗后有效中文至少N个字符，否则丢弃
MAX_EMOJI_RATIO = 0.5                  # 非中文占比超过此值视为表情包/无意义
TOPIC_KEYWORDS = []                    # 话题关键词（非空时用于相关性初筛；空则跳过）

# ============================================================
# 情感分析配置
# ============================================================
POSITIVE_THRESHOLD = 0.6               # >=此值为正向
NEGATIVE_THRESHOLD = 0.4               # <=此值为负向（中间为中立）

# ============================================================
# 分词 & 情感后端配置
# ============================================================
# 分词后端: "jieba" (默认) | "pkuseg" (需 Python≤3.12 + pip install pkuseg)
SEGMENTER_BACKEND = "jieba"
PKUSEG_MODEL = "web"                   # pkuseg 领域: web/news/medicine/tourism
# 情感后端: "snownlp" (默认) | "cntext" (需 pip install cntext)
SENTIMENT_BACKEND = "snownlp"
STOPWORDS_FILE = str(BASE_DIR / "data" / "stopwords.txt")
JIEBA_USER_DICT = None                 # 可选：自定义词典路径

# ============================================================
# 可视化配置
# ============================================================
FONT_PATH = "C:/Windows/Fonts/msyh.ttc"  # 中文字体（Windows 微软雅黑）
OUTPUT_DIR = str(BASE_DIR / "output")
PIE_COLORS = ["#4CAF50", "#FFC107", "#F44336"]  # 正向绿 / 中立黄 / 负向红

# ============================================================
# 数据文件路径（基于 BASE_DIR 的绝对路径，防工作目录漂移）
# ============================================================
DATA_DIR      = str(BASE_DIR / "data")
RAW_COMMENTS  = str(BASE_DIR / "data" / "raw_comments.json")
CLEANED       = str(BASE_DIR / "data" / "cleaned_comments.json")
SENTIMENT     = str(BASE_DIR / "data" / "sentiment_results.json")
WORD_FREQ     = str(BASE_DIR / "data" / "word_freq.json")
ALIAS_DICT    = str(BASE_DIR / "data" / "alias_dict.json")