"""test_alias_resolver.py — 别名归一化引擎单元测试"""

import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from preprocess.alias_resolver import AliasResolver, _levenshtein
from config import ALIAS_DICT


class TestLevenshtein:
    def test_empty(self):
        assert _levenshtein("", "abc") == 3
        assert _levenshtein("abc", "") == 3

    def test_identical(self):
        assert _levenshtein("donk", "donk") == 0

    def test_substitution(self):
        assert _levenshtein("donk", "dong") == 1

    def test_insertion(self):
        assert _levenshtein("donk", "donks") == 1


class TestAliasResolver:
    def test_init_nonexistent_dict(self):
        """词典不存在时不应抛出异常"""
        resolver = AliasResolver("/tmp/_nonexistent_dict_.json")
        assert resolver.entries == {}

    def test_resolve_no_alias(self):
        """文本中没有别名时应原样返回"""
        resolver = AliasResolver(ALIAS_DICT)
        text = "今天打得不错"
        assert resolver.resolve(text) == text

    def test_bootstrap_empty_corpus(self):
        """空语料自举应返回0"""
        resolver = AliasResolver(ALIAS_DICT)
        assert resolver.auto_bootstrap([], min_freq=3) == 0
