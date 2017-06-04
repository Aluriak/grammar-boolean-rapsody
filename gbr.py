"""
Aim of this script is to produce, for any pattern like:

    a&(b|c)&(d|e)

the resulting lists of elements:

    (a, b, d)
    (a, c, d)
    (a, b, e)
    (a, c, e)

Use a finite state machine (see generate_fsm() function) to parse the input,
 produce a syntactic tree from the lexical table, and then deduce a DAG,
 that is finally used for find the expected ouput.

The API consist only in the compile_output(1) function.
All other functions are used internally, or not used at all
 but conserved for science. (only postfix(1) function is in this last case)

The compile_output(1) function is high-level and simple. You may want to
 begin there if you want to read these code.

PEP8 is completely busted at some point, but its mainly because of
 readability of big lines.

Principles:
- lexical analysis of the input string, given the lexems (id, operators, parenthesis)
- generate the polish notation of the lexical table
- syntactic tree construction
- DAG creation from the syntactic tree
- walks in the DAG for determine the outputed elements lists

Idea is, mainly, that a DAG is simple to store (dict {node:successors}),
 and represent well the input data.
 The walks in the DAG is performed by the generate_output(1) function,
 and simply consist of a DFS with generation of the whole path since the
 root each time a leaf is hit.

The algorithm for the syntactic tree to DAG is probably not what you want to have
 in any real project. This algorithm was design and tested too quickly for being
 efficient or secure.

Limits:
- no real error handling for parenthesis
- source code can't begin with non defined start (ex: (a|b)&c is prohibited),
while the creation of the DAG doesn't handle that case.
- the DAG is probably not necessary, while the syntactic tree contains already
all necessary information, well structured.

"""
import re
from enum import Enum
from collections import ChainMap, defaultdict


# Constants
ERROR_LIMIT = 10  # at most 10 errors before compilation abortion
SILENT_SYNTACTIC_ANALYSIS = True  # continue compilation even if syntactic error
OP_AND = '&'
OP_OR  = '|'


def precedence(op1, op2):
    """True if op1 have precedence on op2.
    Here AND have an higher precedence than OR.
    """
    _, op1 = op1
    _, op2 = op2
    assert op1 in (OP_AND, OP_OR)
    assert op2 in (OP_AND, OP_OR)
    return op1 != op2 and op1 == OP_AND


class Type(Enum):
    Letter  = '[a-zA-Z0-9]'
    Op      = '[' + OP_AND + OP_OR + ']'
    Opening = '\('
    Closing = '\)'
    Other   = ''  # used as start-state
    EndOfFile = '\0'

class Command(Enum):
    Stack        = -1
    Finish       = -2

class Error(Enum):
    UnexpectedLetter  = 'unexpected letter'
    UnexpectedOp      = 'unexpected operator'
    UnexpectedOpening = 'unexpected opening parenthesis'
    UnexpectedClosing = 'unexpected closing parenthesis'
    UnexpectedChar    = 'unexpected character'


def generate_fsm():
    """Return a dict {previous type: {current type: command/error}}"""
    # default command is : error everywhere
    default_command = {Type.Letter: Error.UnexpectedLetter,
                       Type.Op: Error.UnexpectedOp,
                       Type.Opening: Error.UnexpectedOpening,
                       Type.Closing: Error.UnexpectedClosing,
                       Type.Other: Error.UnexpectedChar,
                       Type.EndOfFile: Command.Stack}
    # use ChainMap for specify only the differences with default commands
    return {
        Type.Other  : ChainMap({Type.Letter: Type.Letter, Type.Op: Type.Op, Type.Opening: Type.Opening, Type.Closing: Type.Closing, Type.EndOfFile: Command.Finish}      , default_command),
        Type.Letter : ChainMap({Type.Letter: Type.Letter   , Type.Op     : Command.Stack , Type.Closing: Command.Stack}   , default_command) ,
        Type.Op     : ChainMap({Type.Letter: Command.Stack , Type.Opening: Command.Stack , Type.EndOfFile: Command.Stack} , default_command) ,
        Type.Opening: ChainMap({Type.Letter: Command.Stack , Type.Opening: Command.Stack , Type.EndOfFile: Command.Stack} , default_command) ,
        Type.Closing: ChainMap({Type.Op    : Command.Stack , Type.Closing: Command.Stack , Type.EndOfFile: Command.Stack} , default_command) ,
    }


def type_of(character):
    """Return the Type value for given character"""
    if character == Type.EndOfFile.value:
        return Type.EndOfFile
    for type in Type:
        if re.match(type.value, character):
            return type
    return Type.Other


def lexical_analysis(string):
    """Generate the lexical table of given string"""
    # Pretreatment of input: add a final character
    string += Type.EndOfFile.value
    # Initiatilization
    error_count = 0
    fsm = generate_fsm()  # dict {previous:{current:type/command/error}}
    last_element_index = 0  # index in string where ends the last added item
    START_TYPE    = Type.Other  # other is start, and is unreachable
    previous_type = START_TYPE
    idx = 0
    # main loop
    while idx < len(string):
        char = string[idx]
        current_type = type_of(char)
        next_state = fsm[previous_type][current_type]
        # print('LOOP: char:', char, '; previous:', previous_type, '; current:', current_type, '; next_state:', next_state)
        if next_state in Error:
            print('ERROR:', next_state.value, 'at position', idx,
                  '(prev:', previous_type, '; curr:', current_type, ')')
            print('\t', string)
            print('\t ', ' '*idx, '^', sep='')
            previous_type = next_state
            previous_type = START_TYPE
            if error_count > ERROR_LIMIT and not SILENT_SYNTACTIC_ANALYSIS:
                exit(1)
        elif next_state in Command:
            assert last_element_index <= idx
            if next_state is Command.Stack:
                yield (previous_type, string[last_element_index:idx])
            if next_state is Command.Finish:
                idx = len(string)  # loop break
            previous_type = START_TYPE
            last_element_index = idx
        else:
            assert next_state in Type
            previous_type = next_state
            idx += 1


def well_parenthesed(lextable):
    """True iff given lexical table is well parenthesed"""
    parenthesis_count = 0
    for type, _ in lextable:
        if type is Type.Opening:
            parenthesis_count += 1
        elif type is Type.Closing:
            parenthesis_count -= 1
    return parenthesis_count == 0


def postfix(lextable):  # UNUSED
    """Return the postfix representation of the given lexical table


    Wikipedia definition:
    While there are tokens to be read:

        Read a token.
        If the token is a number, then add it to the output queue.

        If the token is an operator, o1, then:
            while there is an operator token, o2, at the top of the operator stack, and either
                    o1 is left-associative and its precedence is less than or equal to that of o2, or
                    o1 is right associative, and has precedence less than that of o2,
                then pop o2 off the operator stack, onto the output queue;
            push o1 onto the operator stack.

        If the token is a left parenthesis (i.e. "("), then push it onto the stack.
        If the token is a right parenthesis (i.e. ")"):
            Until the token at the top of the stack is a left parenthesis, pop operators off the stack onto the output queue.
            Pop the left parenthesis from the stack, but not onto the output queue.
            If the token at the top of the stack is a function token, pop it onto the output queue.
            If the stack runs out without finding a left parenthesis, then there are mismatched parentheses.

        When there are no more tokens to read:
            While there are still operator tokens in the stack:
                If the operator token on the top of the stack is a parenthesis, then there are mismatched parentheses.
                Pop the operator onto the output queue.

        Exit.


    """
    opstack = []  # stack of operators
    for token in lextable:
        # print('LOOP:', '\n\t', token, '\n\t', opstack, '\n\t', output)
        type, value = token
        if type is Type.Letter:
            yield token
        if type is Type.Op:
            # if any operator with higher precedence (left associativity) in stack
            while (len(opstack) > 0 and opstack[-1][0] is Type.Op and
                   precedence(opstack[-1], token)):
                yield opstack.pop()
            opstack.append(token)
        if type is Type.Opening:
            opstack.append(token)
        if type is Type.Closing:
            while opstack[-1][0] != Type.Opening:
                yield opstack.pop()
            opstack.pop()  # don't put opening parenthesis in the output
    while len(opstack) > 0:
        yield opstack.pop()


def prefix(lextable):
    """
    - Scan input in reversed order:
        - If token is an operand yield it
        - If token is a ) push it to stack
        - If token is an operator o1:
            - pop from stack and yield each operator o2 that have same or higher precedence than o1.
            - puth o2 to stack
        - If token is a (:
            - pop from stack and yield each operator until a ) is encountered.
            - Remove the (

    """
    opstack = []
    output  = []
    for token in reversed(lextable):
        type, value = token
        # print('LOOP:', '\n\t', token, '\n\t', opstack, '\n\t', output)
        if type is Type.Letter:
            output.append(token)
        if type is Type.Closing:
            opstack.append(token)
        if type is Type.Op:
            # if any operator with higher precedence (left associativity) in stack
            while (len(opstack) > 0 and opstack[-1][0] is Type.Op and
                   precedence(token, opstack[-1])):
                output.append(opstack.pop())
            opstack.append(token)
        if type is Type.Opening:
            while len(opstack) and opstack[-1][0] != Type.Closing:
                output.append(opstack.pop())
            opstack.pop()  # don't put opening parenthesis in the output
    while len(opstack) > 0:
        output.append(opstack.pop())
    return reversed(output)


def generate_syntree(pretable):
    """Return the syntactic tree of given prefix lexical table"""
    syntree = {}  # uid: node
    last_uid = 1
    def parent(uid): return uid // 2
    def leftson(uid): return uid * 2
    def rightson(uid): return uid * 2 + 1

    for token in pretable:
        # print('LOOP:', '\n\t', type, value, '\n\t', dag, '\n\t')
        type, _ = token
        if len(syntree) == 0:
            assert type is Type.Op
            syntree[last_uid] = token
            new_uid = last_uid
        elif syntree[last_uid][0] is Type.Op:
            new_uid = leftson(last_uid)
            syntree[new_uid] = token
        elif syntree[last_uid][0] is Type.Letter:
            curr_uid = parent(last_uid)
            while rightson(curr_uid) in syntree:
                curr_uid = parent(curr_uid)
            new_uid = rightson(curr_uid)
            syntree[new_uid] = token
        last_uid = new_uid
    return syntree


def generate_dag(syntree):
    """Return a dict {node:{sons}} describing given syntactic tree as a DAG"""
    stack = []
    dag = {}  # {token:[tokens]}
    def parent(uid): return uid // 2
    def leftson(uid): return uid * 2
    def rightson(uid): return uid * 2 + 1

    def leafs(node_value, dag=dag):
        """Return all leafs of the given node in the dag"""
        assert node_value in dag
        ret = []
        if len(dag[node_value]):
            for son in dag[node_value]:
                ret.extend(leafs(son, dag))
            return ret
        else:  # node is a leaf
            return [node_value]

    # d = {'a': ('b', 'c'), 'c':'o', 'b': {}, 'o':{}}
    # print(d)
    # print(leafs('a', dag=d))
    # exit()


    def uid_to_node_value(uid):
        return syntree[uid][1]

    def walk_on(node, dag=dag):
        if node not in syntree: return None
        token = syntree[node]
        type, value = token
        if type is Type.Letter:  # all letters must appears in the dag
            dag[value] = tuple()
        right = walk_on(rightson(node))
        left = walk_on(leftson(node))
        # print('\nLOOP:', node, left, right, value == OP_OR)

        if left and right:
            assert type is Type.Op
            if value == OP_OR:
                return tuple(left + right)
            else:
                assert value == OP_AND
                for lson in left:
                    for leaf in leafs(lson):
                        dag[leaf] = right
                return left

        return tuple([value])

    assert 1 in syntree
    walk_on(1, dag=dag)
    return {k: v for k, v in dag.items() if len(v)}  # filter out leaves


def generate_output(dag):
    """Yield all possible walks in the given dag"""
    # get root
    internal_and_leaf = frozenset(son for sons in dag.values() for son in sons)
    root = tuple(node for node in dag if node not in internal_and_leaf)
    assert len(root) == 1
    root = next(iter(root))

    # exploration in deep
    path = []
    def walk_on(cur_node, dag=dag, path=[]):
        if cur_node in dag:  # if not a leaf
            for son in dag[cur_node]:
                yield from walk_on(son, path=path+[cur_node])
        else:  # leaf case
            yield tuple(path + [cur_node])

    return tuple(walk_on(root, dag=dag, path=[]))


def compile_input(string):
    """Yields the possible combinations parsed from given string.
    See module docstring for more explanations.
    """
    # lexical + syntactic analysis
    lexical_table = tuple(lexical_analysis(string))
    # print('STRING:', string)
    # print('LEXICAL TABLE:', lexical_table)
    assert well_parenthesed(lexical_table)

    # get prefix representation
    pretable = tuple(prefix(lexical_table))
    # print('PREFIX:', pretable)

    # get postfix representation  # UNUSED
    # postable = tuple(postfix(lexical_table))
    # print('POSTFIX:', postable)

    # generate the syntactic tree representation
    syntree = generate_syntree(pretable)
    # print('SYNTACTIC TREE:', syntree)

    # generate the DAG representation
    dag = generate_dag(syntree)
    # print('DAG:', dag)

    # generate Output strings
    yield from generate_output(dag)



if __name__ == '__main__':
    string = 'a&(b|(c&o))&(d|e)'
    # string = '(a|b)&jp&(bc|cp)'  # exception : dag treatment fails with a non fixed beginning
    # string = 'jp&(bc|cp)'
    # string = 'jp&a(bc|cp)'  # error
    # string = 'a&b|c'  # operator priority
    print('OUTPUT:\n\t', '\n\t '.join(str(_) for _ in compile_input(string)))

