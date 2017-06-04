
import functools
import itertools
import inf2post as i2p


def test_have_precedence():
    assert i2p.have_precedence('(', '&') == False
    assert i2p.have_precedence('(', '|') == False
    assert i2p.have_precedence('&', '(') == False
    assert i2p.have_precedence('|', '(') == False
    assert i2p.have_precedence('|', ')') == False
    assert i2p.have_precedence('&', ')') == False
    assert i2p.have_precedence('(', ')') == False


def test_infix_to_postfix():
    assert tuple(i2p.infix_to_postfix('a&b|c')) == ('a', 'b', '&', 'c', '|')
    assert tuple(i2p.infix_to_postfix('a|c')) == ('a', 'c', '|')

def test_infix_to_postfix_parenthesis():
    assert tuple(i2p.infix_to_postfix('(a&b)|c')) == ('a', 'b', '&', 'c', '|')
    assert tuple(i2p.infix_to_postfix('a&(b|c)')) == ('a', 'b', 'c', '|', '&')
    assert tuple(i2p.infix_to_postfix('(a|c)')) == ('a', 'c', '|')


def test_grammar_boolean_rapsody_mult_and():
    assert i2p.grammar_boolean_rapsody('a&b&c&d', {'a': True, 'b': True, 'c': True, 'd': True})

def test_grammar_boolean_rapsody_exhaust():
    func = functools.partial(i2p.grammar_boolean_rapsody, 'a&b|c&d')
    for a, b, c, d in itertools.product((True, False), repeat=4):
        assert func(dict(zip('abcd', (a, b, c, d)))) == (a and b) or (c and d)

def test_grammar_boolean_rapsody_parenthesis():
    func = functools.partial(i2p.grammar_boolean_rapsody, 'a&(b|c)&d')
    for a, b, c, d in itertools.product((True, False), repeat=4):
        assert func(dict(zip('abcd', (a, b, c, d)))) == (a and (b or c) and d)

