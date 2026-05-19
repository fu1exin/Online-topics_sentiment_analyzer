# 舆情洞察员 —— 工具与仓库清单

## 当前使用的工具

| 工具 | 版本 | 用途 | 来源 |
|------|------|------|------|
| Python | 3.13.13 | 运行环境 | https://python.org |
| requests | >=2.28 | HTTP 爬虫 | https://github.com/psf/requests |
| jieba | >=0.42 | 中文分词 | https://github.com/fxsjy/jieba |
| SnowNLP | >=0.12 | 中文情感分析 | https://github.com/isnowfy/snownlp |
| matplotlib | >=3.5 | 可视化 | https://github.com/matplotlib/matplotlib |
| wordcloud | >=1.9 | 词云 | https://github.com/amueller/word_cloud |
| Bilibili API | - | 评论数据源 | https://api.bilibili.com |

## 使用的 GitHub 仓库

### 核心依赖

| 仓库 | Stars | 用途 |
|------|-------|------|
| [fxsjy/jieba](https://github.com/fxsjy/jieba) | 33k+ | 结巴中文分词 |
| [isnowfy/snownlp](https://github.com/isnowfy/snownlp) | 6.5k+ | 中文自然语言处理 |
| [psf/requests](https://github.com/psf/requests) | 52k+ | HTTP 客户端 |
| [matplotlib/matplotlib](https://github.com/matplotlib/matplotlib) | 20k+ | Python 绘图库 |
| [amueller/word_cloud](https://github.com/amueller/word_cloud) | 10k+ | Python 词云生成 |

### 推荐升级

| 仓库 | Stars | 用途 | 状态 |
|------|-------|------|------|
| [lancopku/pkuseg-python](https://github.com/lancopku/pkuseg-python) | 6.7k | 北大分词器，多领域模型 | Python<=3.12 |
| [hiDaDeng/cntext](https://github.com/hiDaDeng/cntext) | 453 | 社科文本分析，内置情感词典 | Python<=3.12 |
| [fighting41love/funNLP](https://github.com/fighting41love/funNLP) | 80k+ | 中文NLP资源大全（词典/语料） | 资源库，直接取用 |
| [dongrixinyu/JioNLP](https://github.com/dongrixinyu/JioNLP) | 3.8k | 中文NLP预处理工具箱 | 可选集成 |
| [dongrixinyu/jiojio](https://github.com/dongrixinyu/jiojio) | 50 | 轻量中文分词 | 轻量替代 |
| [Cyberbolt/Cemotion](https://github.com/Cyberbolt/Cemotion) | 222 | BERT 中文情感分析 | 需 GPU |
| [hontsev/ChineseNER](https://github.com/hontsev/ChineseNER) | 38 | 中文命名实体识别 | 可选集成 |

## 项目结构

```
sentiment_analyzer/
├── config.py                <- 全局配置（含后端切换）
├── main.py                  <- 7步流水线入口
├── TOOLS.md                 <- 本文档
├── requirements.txt
├── crawler/
│   └── weibo_crawler.py     <- B站 API 爬虫
├── preprocess/
│   ├── cleaner.py           <- 文本清洗 + 质量过滤
│   ├── alias_resolver.py    <- L0-L4 别名归一化引擎
│   └── segmenter.py         <- 分词 + 词频统计（可切换 pkuseg）
├── sentiment/
│   └── analyzer.py          <- 情感分析 + ECDF权重 + 实体级情感
├── visualize/
│   └── pie_chart.py         <- 饼图/柱状图/词云
├── data/
│   ├── alias_dict.json      <- 别名词典（持久化知识库）
│   ├── stopwords.txt        <- 停用词表
│   ├── raw_comments.json    <- 爬虫输出
│   ├── cleaned_comments.json<- 清洗后
│   ├── word_freq.json       <- 词频统计
│   └── sentiment_results.json <- 情感分析结果
└── output/
    ├── pie_chart.png         <- 原始 vs ECDF 加权饼图
    ├── entity_sentiment.png  <- 实体情感对比柱状图
    ├── wordcloud_positive.png<- 正向词云
    └── wordcloud_negative.png<- 负向词云
```

## 流水线 7 步

```
[1/7] 爬虫    -> raw_comments.json       (Bilibili API)
[2/7] 清洗    -> cleaned_comments.json   (正则 + 质量过滤)
[3/7] 归一化  -> (别名替换)              (L0-L4 别名引擎)
[4/7] 分词    -> word_freq.json          (jieba / pkuseg)
[5/7] 情感    -> (整体情感)              (SnowNLP / cntext)
[6/7] 实体    -> entity_sentiment        (逐人物情感)
[7/7] 可视化  -> 4 张图 output/
```

## 配置切换

```python
# config.py

# 分词后端
SEGMENTER_BACKEND = "jieba"     # 默认，无需额外安装
# SEGMENTER_BACKEND = "pkuseg"  # pip install numpy pkuseg (Python<=3.12)

# 情感后端
SENTIMENT_BACKEND = "snownlp"   # 默认，无需额外安装
# SENTIMENT_BACKEND = "cntext"  # pip install cntext (Python<=3.12)
```

## 算法与方法

| 组件 | 算法 | 说明 |
|------|------|------|
| 分词 | jieba / pkuseg | 中文分词 + 停用词过滤 |
| 情感 | SnowNLP | 朴素贝叶斯情感分类 |
| 加权 | ECDF | 经验累积分布函数（分位数权重） |
| 消歧 | 共现得分 | 上下文窗口词共现匹配 |
| 聚类 | Levenshtein | 编辑距离别名聚合 |
| 实体发现 | TF-IDF | jieba.analyse 关键词提取 |

## 数据源

| 平台 | API | 说明 |
|------|-----|------|
| Bilibili | api.bilibili.com/x/v2/reply/main | 视频评论（无需登录） |
| Bilibili | api.bilibili.com/x/web-interface/search/type | 视频搜索 |

## 限制说明

- **pkuseg / cntext** 当前不兼容 Python 3.13，需 Python ≤3.12 环境
- 如需在 Python 3.13 使用，建议创建 conda 环境：
  ```
  conda create -n nlp312 python=3.12
  conda activate nlp312
  pip install -r requirements.txt pkuseg cntext
  ```
- 切换后端后修改 config.py 对应选项即可
