import pytest

#from parser.parser import parse
from fast_nilakkhana import transform

@pytest.mark.parametrize(
    "string",
    [
        'hello',
        'hello world'
        '_hello',
        'foo*',
        '<a link="_foo_">bar</a>',
        '<a href="http://example.com" attr="_foo_">bar</a>',
        '<span class="_foo">bar</span><span class="bar_">foo</span>',
    ]
)
def test_no_change(string):
    assert transform(string) == string

@pytest.mark.parametrize(
    "string,expected",
    [
        ('hello world', 'hello world'),
        ('<b>hello world</b>', '<b>hello world</b>'),
        ('foo *bar* baz!', 'foo <em>bar</em> baz!'),
        ('<i class="_foo_">**bold**</i>', '<i class="_foo_"><b>bold</b></i>'),
    ]
)
def test_transform(string, expected):
    assert transform(string) == expected