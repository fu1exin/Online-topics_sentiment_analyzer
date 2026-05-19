"""
alias_resolver.py —— 四层别名归一化体系

层级:
  L1 规则召回   — 别名词典精确/大小写匹配
  L2 语义消歧   — 多候选词时，按上下文词共现选择最佳规范名
  L3 启发发现   — 高频未知词与已知词的共现模式发现候选别名
  L4 自动迭代   — 发现的别名写入词典 _auto_discovery，下次自动生效

使用:
  resolver = AliasResolver("data/alias_dict.json")
  text = resolver.resolve("小驴今天状态太好了")
  # -> "donk今天状态太好了"
"""

import json
import os
import re
from collections import Counter
from config import STOPWORDS_FILE


def _levenshtein(a, b):
    """计算两个字符串的编辑距离（Levenshtein）"""
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    dp = [[0] * (m + 1) for _ in range(2)]
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        dp[i % 2][0] = i
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i % 2][j] = min(
                dp[(i - 1) % 2][j] + 1,
                dp[i % 2][j - 1] + 1,
                dp[(i - 1) % 2][j - 1] + cost,
            )
    return dp[n % 2][m]


class AliasResolver:
    """四层别名归一化引擎"""

    def __init__(self, dict_path="data/alias_dict.json"):
        self.dict_path = dict_path
        self.entries = {}           # {entry_key: {canonical, aliases, context_words, source}}
        self.alias_map = {}         # {alias_lower: entry_key}  快速查找
        self.new_discoveries = []   # 本轮新发现
        self._load()

    # ==================== L1: 规则召回 ====================

    def _load(self):
        """加载别名词典，构建大小写不敏感映射表"""
        if not os.path.exists(self.dict_path):
            print(f"[别名] 词典不存在: {self.dict_path}")
            return

        with open(self.dict_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for key, val in data.items():
            if key.startswith("_"):
                continue
            self.entries[key] = {
                "canonical": val["canonical"],
                "aliases": val["aliases"],
                "context_words": val.get("context_words", []),
                "source": val.get("source", "manual"),
            }
            # 所有别名 → 条目 key 的映射
            canonical = val["canonical"]
            for alias in val["aliases"]:
                self.alias_map[alias.lower()] = key
            # 规范名本身也映射
            self.alias_map[canonical.lower()] = key

    def _find_candidates(self, word):
        """找某个词可能对应的所有条目（支持多候选）"""
        candidates = []
        word_lower = word.lower()
        # 直接匹配
        if word_lower in self.alias_map:
            candidates.append(self.alias_map[word_lower])
        # 子串匹配（如 "donk!!" → "donk"）
        for alias_lower, key in self.alias_map.items():
            if alias_lower in word_lower and len(alias_lower) >= 3:
                if key not in candidates:
                    candidates.append(key)
        return candidates

    def resolve(self, text):
        """
        L1 + L2: 将文本中的别名替换为规范名。
        单候选直接替换，多候选用上下文词共现消歧。
        """
        if not self.alias_map:
            return text

        # 策略: 用别名映射表中的每一个 alias 作为候选项逐个替换
        # 为避免短别名误伤（如 "TS" 可能出现在 "PTS" 中），用词边界 + 大小写不敏感

        # 构建替换映射: {(start, end): canonical}
        replacements = []

        # 按别名长度降序排列，优先匹配长别名（避免 "小驴" 没被匹配前被 "驴" 误匹配）
        sorted_aliases = sorted(
            [(alias, self.alias_map[alias]) for alias in self.alias_map],
            key=lambda x: len(x[0]), reverse=True
        )

        for alias, entry_key in sorted_aliases:
            canonical = self.entries[entry_key]["canonical"]
            # 使用正则进行词边界匹配（中文无边界，用子串扫描）
            pattern = re.escape(alias)
            for m in re.finditer(pattern, text, re.IGNORECASE):
                start, end = m.start(), m.end()
                # 检查是否已被更长的匹配覆盖
                if not any(s <= start < e for s, e, _ in replacements):
                    # L2: 多候选消歧
                    candidates = self._find_candidates(text[start:end])
                    if len(candidates) > 1:
                        canonical = self._disambiguate(text, candidates, start)
                    else:
                        canonical = self.entries[entry_key]["canonical"]
                    replacements.append((start, end, canonical))

        # 按位置倒序替换，避免偏移问题
        replacements.sort(key=lambda x: x[0], reverse=True)
        result = text
        for start, end, canonical in replacements:
            result = result[:start] + canonical + result[end:]

        return result

    # ==================== L2: 语义消歧 ====================

    def _disambiguate(self, text, candidates, position):
        """
        多候选消歧：计算每个候选的上下文词在文本中的共现得分。
        得分最高者胜出；平局返回第一个。
        """
        # 取前后各 30 个字符作为上下文窗口
        ctx_start = max(0, position - 30)
        ctx_end = min(len(text), position + 30)
        context = text[ctx_start:ctx_end]

        best_key = candidates[0]
        best_score = -1
        for key in candidates:
            score = 0
            for ctx_word in self.entries[key].get("context_words", []):
                if ctx_word.lower() in context.lower():
                    score += 1
            if score > best_score:
                best_score = score
                best_key = key

        return self.entries[best_key]["canonical"]

    # ==================== L0: 冷启动自举 ====================

    def auto_bootstrap(self, cleaned_texts, min_freq=3, max_entities=15):
        """
        L0 冷启动：对全新话题自动发现实体并聚类别名。
        
        策略:
          1. TF-IDF + jieba 提取高频关键词作为候选实体
          2. 按编辑距离 + 上下文相似度聚类
          3. 每簇最高频词作为规范名，其余为别名
          4. 写入 self.entries，使 resolve() 即时生效
        
        返回: 发现的实体数
        """
        if len(cleaned_texts) < 10:
            return 0

        import jieba
        import jieba.analyse

        corpus = "\n".join(cleaned_texts)

        # 1. TF-IDF 提取关键词作为候选实体
        tags = jieba.analyse.extract_tags(corpus, topK=80, withWeight=True)

        # 2. 过滤：至少 min_freq 次出现 + 命名实体特征
        candidates = []
        for word, weight in tags:
            if len(word) < 2 or len(word) > 8:
                continue
            if word.isdigit():
                continue
            count = corpus.count(word)
            if count < min_freq:
                continue
            # 英文候选：必须首字母大写或全大写（命名实体特征）
            if word.isascii() and not (word[0].isupper() or word.isupper()):
                continue
            candidates.append({"word": word, "freq": count, "weight": round(weight, 2)})

        if not candidates:
            return 0

        # 3. 聚类：按简单字符串相似度
        def similarity(a, b):
            al, bl = a.lower(), b.lower()
            if al == bl:
                return 1.0
            if al in bl or bl in al:
                return 0.85
            max_len = max(len(al), len(bl))
            if max_len == 0:
                return 0.0
            dist = _levenshtein(al, bl)
            return 1.0 - dist / max_len

        clusters = []  # [{words: [candidate, ...]}]

        for cand in candidates:
            best_cluster = None
            best_sim = 0.4  # 阈值
            for ci, cluster in enumerate(clusters):
                for existing in cluster["words"]:
                    sim = similarity(cand["word"], existing["word"])
                    if sim > best_sim:
                        best_sim = sim
                        best_cluster = ci
            if best_cluster is not None:
                clusters[best_cluster]["words"].append(cand)
            else:
                if len(clusters) < max_entities:
                    clusters.append({"words": [cand]})

        # 4. 每簇选最高频为规范名
        discovered = 0
        for cluster in clusters:
            if len(cluster["words"]) < 2:
                continue  # 单成员的簇不需要归一化
            sorted_words = sorted(cluster["words"], key=lambda x: x["freq"], reverse=True)
            canonical = sorted_words[0]["word"]
            aliases = [w["word"] for w in sorted_words[1:]]
            context = self._extract_context(canonical, cleaned_texts)
            key = f"auto_{canonical}"
            self.entries[key] = {
                "canonical": canonical,
                "aliases": aliases,
                "context_words": context,
                "source": "auto_bootstrap",
            }
            for alias in aliases:
                self.alias_map[alias.lower()] = key
            self.alias_map[canonical.lower()] = key
            discovered += 1

        if discovered > 0:
            print(f"[别名] L0自举: 发现 {discovered} 组别名簇 (共 {sum(len(c['words']) for c in clusters)} 个实体词)")

        return discovered

    def _extract_context(self, word, texts, top_n=5):
        """提取与 word 共现的高频上下文词"""
        import jieba
        co_words = Counter()
        for text in texts:
            if word not in text:
                continue
            words = [w for w in jieba.lcut(text) if len(w) > 1 and w != word]
            co_words.update(words)
        return [w for w, _ in co_words.most_common(top_n)]

    # ==================== L3: 启发式发现 ====================

    def discover(self, cleaned_texts, top_n=10):
        """
        从清洗后文本中启发式发现潜在新别名。
        策略:
          a) 高频双字词中，不在现有词表中 → 候选
          b) 在已知实体附近频繁共现的未知词 → 高置信候选
          c) "叫X" / "就是X" / "又称X" 模式 → 中等置信候选
        """
        if len(cleaned_texts) < 10:
            return []

        # 收集所有高频词（简单按2-3字分词片段）
        import jieba
        all_words = []
        for text in cleaned_texts:
            for w in jieba.lcut(text):
                w = w.strip()
                if 2 <= len(w) <= 6 and re.search(r'[\u4e00-\u9fff]', w):
                    all_words.append(w)

        word_freq = Counter(all_words)

        # 排除已有别名词表中的词
        known = set(a.lower() for a in self.alias_map)
        candidates = []

        discovery_text = "\n".join(cleaned_texts)

        for word, freq in word_freq.most_common(200):
            if word.lower() in known:
                continue
            if len(word) < 2:
                continue

            # 策略b: 检查是否与已知实体共现
            co_occur = {}
            for entry_key, entry in self.entries.items():
                canonical = entry["canonical"]
                # 在评论中搜索 word 和 canonical 同时出现
                count = discovery_text.count(word)
                if count < 3:
                    continue
                # 简化: 统计共现场景
                for ctx_word in entry.get("context_words", []):
                    # 如果 word 和 ctx_word 在同一个上下文中出现
                    pass

            # 策略c: 检查解释模式
            expl_patterns = [
                rf'{re.escape(word)}[是为即]',      # "小驴是" "洞仔即"
                rf'叫{re.escape(word)}',            # "叫小驴"
                rf'{re.escape(word)}[（(]\w+[）)]', # "小驴(donk)"
            ]
            pattern_score = 0
            for pat in expl_patterns:
                if re.search(pat, discovery_text):
                    pattern_score += 2

            total_score = freq * 0.1 + pattern_score
            if total_score >= 0.5:
                candidates.append({
                    "word": word,
                    "freq": freq,
                    "score": round(total_score, 2),
                })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_n]

    # ==================== L4: 自动迭代 ====================

    def auto_save_discoveries(self, candidates, min_score=2.0):
        """
        将高置信候选别名写入词典的 _auto_discovery 字段。
        """
        if not candidates:
            return 0

        saved = 0
        with open(self.dict_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        existing_auto = {d["word"] for d in data.get("_auto_discovery", [])}

        for c in candidates:
            if c["score"] >= min_score and c["word"] not in existing_auto:
                data["_auto_discovery"].append({
                    "word": c["word"],
                    "freq": c["freq"],
                    "score": c["score"],
                })
                saved += 1

        with open(self.dict_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if saved > 0:
            print(f"[别名] 自动保存 {saved} 个新候选别名 -> {self.dict_path}")
        return saved

    # ==================== 工具 ====================

    def get_stats(self):
        """返回统计信息"""
        manual = sum(1 for e in self.entries.values() if e["source"] == "manual")
        total_aliases = sum(len(e["aliases"]) for e in self.entries.values())
        return {
            "entities": len(self.entries),
            "manual_entities": manual,
            "total_aliases": total_aliases,
            "alias_map_size": len(self.alias_map),
        }


# ============================================================
# 便捷函数：集成到流水线
# ============================================================

def resolve_comments(
    cleaned_path="data/cleaned_comments.json",
    out_path=None,
    dict_path="data/alias_dict.json",
    auto_save=True,
):
    """
    对已清洗的评论执行别名归一化。
    返回: (resolved_texts_list, resolver, discovery_candidates)
    """
    if out_path is None:
        out_path = cleaned_path

    if not os.path.exists(cleaned_path):
        print(f"[别名] 文件不存在: {cleaned_path}")
        return [], None, []

    with open(cleaned_path, "r", encoding="utf-8") as f:
        comments = json.load(f)

    resolver = AliasResolver(dict_path)
    stats = resolver.get_stats()

    # L0 冷启动：词典为空时自动从数据中发现实体
    if stats["entities"] == 0:
        print("[别名] 词典为空，启动 L0 自举...")
        texts = [c["message"] for c in comments]
        found = resolver.auto_bootstrap(texts)
        if found == 0:
            print("[别名] 未发现可聚类的别名簇，跳过归一化")
            return texts, resolver, []

    replaced_count = 0
    for c in comments:
        original = c["message"]
        resolved = resolver.resolve(original)
        if resolved != original:
            replaced_count += 1
        c["message"] = resolved

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

    texts = [c["message"] for c in comments]
    discoveries = resolver.discover(texts)

    saved = 0
    if auto_save and discoveries:
        saved = resolver.auto_save_discoveries(discoveries)

    print(f"[别名] 完成。{stats['entities']} 实体, {stats['total_aliases']} 别名 -> {replaced_count} 条替换")
    if discoveries:
        top = discoveries[:5]
        print(f"  发现候选: {', '.join(d['word']+f'({d['score']:.1f})' for d in top)}")
    if saved:
        print(f"  自动保存 {saved} 个候选")

    return texts, resolver, discoveries
