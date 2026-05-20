"""test_cleaner.py — 文本清洗模块单元测试"""

import sys, os

# 确保项目根在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from preprocess.cleaner import clean_text, is_low_quality


class TestCleanText:
    def test_remove_url(self):
        assert "链接" in clean_text("链接 https://b23.tv/abc")

    def test_remove_at_mention(self):
        text = clean_text("@user 你好")
        assert "@user" not in text

    def test_remove_html(self):
        text = clean_text("<p>内容</p>")
        assert "<p>" not in text

    def test_remove_emoji(self):
        text = clean_text("哈哈😂😂😂")
        assert "😂" not in text

    def test_merge_space(self):
        text = clean_text("A    B")
        assert text == "A B"

    def test_empty_input(self):
        assert clean_text("") == ""
        assert clean_text(None) == ""


class TestIsLowQuality:
    def test_pure_repeat(self):
        assert is_low_quality("哈哈哈哈")

    def test_pure_punctuation(self):
        assert is_low_quality("？？？")

    def test_short_chinese(self):
        assert is_low_quality("嗯")

    def test_valid_long(self):
        assert not is_low_quality("今天骑士队赢球了，哈登表现不错。")

    def test_empty(self):
        assert is_low_quality("")
        assert is_low_quality("  ")
