import pytest

from src.kt.message_builder import MessageBuilder


class TestMessageBuilder:

    test_cases = {
        "normal message": ("normal message", "normal message"),
        "link message": (
            "link message http://example.com",
            'link message <a href="http://example.com">http://example.com</a>',
        ),
        "link message with query string": (
            "link message http://example.com?foo=bar&baz=hoge",
            'link message <a href="http://example.com?foo=bar&baz=hoge">http://example.com?foo=bar&baz=hoge</a>',
        ),
        "link message with japanese query string": (
            "link message http://example.com?foo=ほげ&baz=ふが",
            'link message <a href="http://example.com?foo=ほげ&baz=ふが">http://example.com?foo=ほげ&baz=ふが</a>',
        ),
        "link message line break": (
            "link message\nhttp://example.com",
            'link message\n<a href="http://example.com">http://example.com</a>',
        ),
        "link message multi": (
            "link message http://one.example.com http://two.example.com",
            'link message <a href="http://one.example.com">http://one.example.com</a> <a href="http://two.example.com">http://two.example.com</a>',
        ),
        "link message multi line break": (
            "link message\nhttp://one.example.com\nhttp://two.example.com",
            'link message\n<a href="http://one.example.com">http://one.example.com</a>\n<a href="http://two.example.com">http://two.example.com</a>',
        ),
    }

    @pytest.mark.parametrize(
        "message,expected",
        list(test_cases.values()),
        ids=test_cases.keys(),
    )
    def test_message_build(self, message, expected):
        m = MessageBuilder(message)
        assert m.build() == expected
