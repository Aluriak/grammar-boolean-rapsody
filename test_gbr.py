
import gbr


def test_basics():
    assert tuple(gbr.compile_input('aa&bb|cc')) == (('aa', 'bb'), ('aa', 'cc'))


def test_parenthesis():
    assert tuple(gbr.compile_input('(a|b)')) == (('a',), ('b',))
    assert tuple(gbr.compile_input('(a&b&c)|(a&d&c)')) == (('a', 'b', 'c'), ('a', 'd', 'c'))


def test_multiple_roots():
    assert tuple(gbr.compile_input('a|b')) == (('a',), ('b',))


def test_complex_1():
    expecteds = (
        ('a', 'b', 'd'),
        ('a', 'b', 'e'),
        ('a', 'c', 'o', 'd'),
        ('a', 'c', 'o', 'e'),
    )
    assert tuple(gbr.compile_input('a&(b|(c&o))&(d|e)')) == expecteds

def test_complex_2():
    expecteds = (
        ('a', 'jp', 'bc')
        ('a', 'jp', 'cp')
        ('b', 'jp', 'bc')
        ('b', 'jp', 'cp')
    )
    assert tuple(gbr.compile_input('(a|b)&jp&(bc|cp)')) == expecteds
