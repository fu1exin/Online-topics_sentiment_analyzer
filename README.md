# 舆情洞察员 — 评论情感分析流水线

从 B站（或虎扑）爬取评论区，经清洗、别名归一化、分词、情感分析后输出图表。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置爬虫目标（可选）
#    编辑 config.py，修改 BILIBILI_OIDS 列表

# 3. 运行全流水线
python main.py
```

输出文件位于 `output/` 目录：
- `pie_chart.png` — 原始 / ECDF 加权情感分布饼图
- `entity_sentiment.png` — 各实体情感对比柱状图
- `wordcloud_positive.png` — 正向评论词云
- `wordcloud_negative.png` — 负向评论词云

## 项目结构

```
sentiment_analyzer/
├── config.py                ← 全局配置（爬虫目标、后端切换、路径）
├── main.py                  ← 7 步流水线入口
├── crawler/
│   ├── weibo_crawler.py     ← B站 API 爬虫
│   └── hupu_crawler.py      ← 虎扑爬虫（Selenium / 静态降级）
├── preprocess/
│   ├── cleaner.py           ← 文本清洗 + 质量过滤
│   ├── alias_resolver.py    ← 四层别名归一化引擎
│   └── segmenter.py         ← 分词 + 词频统计
├── sentiment/
│   └── analyzer.py          ← 情感打分 + ECDF 加权 + 实体级情感
├── visualize/
│   └── pie_chart.py         ← 饼图 / 柱状图 / 词云
├── data/                    ← 数据文件（已 .gitignore，不提交）
│   ├── alias_dict.json      ← 别名词典（知识库）
│   ├── stopwords.txt        ← 停用词表
│   └── ... (运行时生成)
├── tests/                   ← pytest 单元测试
│   ├── test_cleaner.py
│   └── test_alias_resolver.py
└── output/                  ← 图表输出（已 .gitignore）
```

## 配置切换

在 `config.py` 中可切换：

- **分词后端**：`jieba`（默认）/ `pkuseg`（需 Python ≤3.12）
- **情感后端**：`snownlp`（默认）/ `cntext`（需 Python ≤3.12）
- **平台**：`bilibili`（默认）/ `hupu`

## 流水线 7 步

| 步 | 阶段 | 输入 → 输出 | 说明 |
|----|------|-------------|------|
| 1 | 爬虫 | → raw_comments.json | B站 API / 虎扑渲染 |
| 2 | 清洗 | raw → cleaned_comments.json | 去 emoji、URL、低质评论 |
| 3 | 归一化 | cleaned → 别名替换 | 四层别名引擎（L0-L4） |
| 4 | 分词 | → word_freq.json | jieba / pkuseg |
| 5 | 情感 | → 整体情感统计 | SnowNLP / cntext |
| 6 | 实体 | → 逐实体情感 | 上下文窗口独立打分 |
| 7 | 可视化 | → 4 张 PNG | 饼图 + 词云 + 实体柱状图 |

## 依赖

- Python ≥ 3.9
- 见 `requirements.txt`

## 隐私说明

`data/*.json` 文件包含爬取的真实用户评论（含 B站用户 mid），已通过 `.gitignore` 排除在版本控制之外。请勿手动将其提交到公开仓库。
