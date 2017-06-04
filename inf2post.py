"""postfix to infix converter and boolean evaluation,
using parenthesis without special cases for parenthesis.

"""

OPERATORS = {
    # maps each operator with others it have precedence on
    '&': frozenset('|'),
    '|': frozenset(''),
    '^': frozenset('&|'),
}
# Populate with '(' and ')' precedency
for op, succs in tuple(OPERATORS.items()):
    OPERATORS[op] = succs | {'(', ')'}
OPERATORS[')'] = frozenset()
OPERATORS['('] = frozenset(OPERATORS.keys())
print(OPERATORS)

OPERATORS_FUNCTION = {
    '&': (lambda one, two: one and two),
    '|': (lambda one, two: one or two),
    '^': (lambda one, two: one ^ two),
}
INFIX_OPERATORS = frozenset('()')  # removed during infix to postfix conversion


def tokenized(source:str, operators:set) -> iter:
    """Yield tokens found in given source"""
    yield from source  # TODO: handle longer than one identifiers


def have_precedence(one, two, operators=OPERATORS) -> bool:
    """True if *one* have precedence over *two*, else False,
    or raise ValueError if operators are either not valid
    or not orderable by precedency

    """
    if one not in operators:
        raise ValueError("Operator '{}' is not in expected ones ({})"
                         "".format(one, ', '.join(operators)))
    if two not in operators:
        raise ValueError("Operator '{}' is not in expected ones ({})"
                         "".format(two, ', '.join(operators)))
    if one == two:
        return True
    if two in operators[one]:
        return False
    if one in operators[two]:
        return True
    raise ValueError("Operators '{}' and '{}' are not comparables"
                     "".format(one, two))


def infix_to_postfix(source:str, tokenizer:callable=tokenized,
                     have_precedence:callable=have_precedence,
                     operators:set=OPERATORS,
                     infix_operators:set=INFIX_OPERATORS) -> tuple:
    """source in infix form is tokenized and returned in postfix form"""
    stack = []
    for token in tokenizer(source, operators):
        if token in operators:
            while stack and have_precedence(token, stack[-1], operators):
                last = stack.pop()
                if last not in infix_operators:
                    print('YIELD:', last)
                    yield last
            stack.append(token)
        else:
            yield token
    yield from (op for op in reversed(stack) if op not in infix_operators)


def eval_postfix(tokens:iter, variables:dict,
                 operators=OPERATORS_FUNCTION) -> bool:
    """Evaluate given tokens given in postfix order,
    returning the bool result"""
    stack = []
    tokens = tuple(tokens)
    for token in tokens:
        if token in operators:
            *stack, two, one = stack
            one, two = variables.get(one, one), variables.get(two, two)
            stack.append(operators[token](two, one))
        else:  # token is operand
            stack.append(token)
    if len(stack) != 1:
        raise ValueError("Malformed input tokens. {} items are remaining in "
                         "stack: {}".format(len(stack), stack))
    return stack[0]


def grammar_boolean_rapsody(source, variables:dict):
    return eval_postfix(infix_to_postfix(source), variables=variables)


if __name__ == "__main__":
    print(grammar_boolean_rapsody('a&b|c&d', {'a': True, 'b': False, 'c': True, 'd':False}))
    print(grammar_boolean_rapsody('a&(b|c)&d', {'a': True, 'b': False, 'c': True, 'd':False}))
    print('See unit tests for more examples')
