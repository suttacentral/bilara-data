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
def test_basic_transform(string, expected):
    assert transform(string) == expected

@pytest.mark.parametrize(
    "string,expected",
    [
        ('A [hyperlink](https://example.com)', "A <a href='https://example.com'>hyperlink</a>"),
        ('Best dhamma site = [](https://suttacentral.net)', "Best dhamma site = <a href='https://suttacentral.net'>https://suttacentral.net</a>"),
    ]
)
def test_hyperlink_transform(string, expected):
    assert transform(string) == expected
    
@pytest.mark.parametrize(
    "string,expected",
    [
        ('comment-en-brahmali', 'Text reference: [pli-tv-bu-vb-pj3]()', "Text reference: <a href='/pli-tv-bu-vb-pj3/en/brahmali'>Pli-Tv-Bu-Vb-Pj3</a>"),
        ('comment-en-sujato', '[Murder](pli-tv-bu-vb-pj3) is bad.', "<a href='/pli-tv-bu-vb-pj3/en/brahmali'>Murder</a> is bad."),
        ('comment-en-sujato', 'Uppercasing [sn1.1]()', "<a href='/sn1.1/en/sujato'>SN 1.1</a>"),
        ('comment-en-sujato', 'Colons hashed [sn1.1:1.7]()', "<a href='/sn1.1/en/sujato#1.7'>SN 1.1:1.7</a>"),
    ]
)
def test_reference_transform(string, expected):
    assert transform(string) == expected
    