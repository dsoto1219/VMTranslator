from enum import Enum


# Enum: https://stackoverflow.com/a/1695250/18031673
class Command(Enum):
    ARITHMETIC = 0
    PUSH = 1
    POP = 2
    LABEL = 3
    GOTO = 4
    IF = 5
    FUNCTION = 6
    RETURN = 7
    CALL = 8


COMMANDS = {
    """Set of all commands in the VM language."""
    # Arithmetic/Logical Commands
    'add',
    'sub',
    'neg',
    'eq',
    'gt',
    'lt',
    'and',
    'or',
    'not',
    # Memory access commands
    'push',
    'pop',
    # Branching commands
    'label',
    'goto',
    'if-goto',
    # Function commands
    'function',
    'return',
    'call',
}


TYPE_COMMANDS: dict[str, list[str]] = {
    """COMMANDS commands organized as a dictionary."""
    # Arithmetic/Logical Commands
    "arithmetic" : [
        'add',
        'sub',
        'neg',
        'eq',
        'gt',
        'lt',
        'and',
        'or',
        'not',
    ],
    # Memory access commands
    "memory_access" : ['push', 'pop'],
    # Branching commands
    "branching" : ['label', 'goto', 'if-goto'],
    # Function commands
    "function" : ['function', 'return', 'call'],
}


SEGMENT_SYMBOLS: dict[str, str] = {
    """
    Conversion of segment symbols as they would appear in VM code to how they
    would appear in HACK assembly. 
    - If base address is contained within a symbol, a symbol is listed.
    - If the symbol refers to a range of addresses, an empty string is provided
    that denotes this.
    """
    "argument" : "ARG",
    "local" : "LCL",
    "static" : "", # RAM[16-255]
    "constant" : "SP",
    "this" : "THIS",
    "that" : "THAT",
    "pointer" : "", # RAM[THIS], RAM[THAT]
    "temp" : "R5",
}


REGEXES: dict = {
    """Strings for regex checks."""
    'command' : { 
        'arithmetic': 'add|sub|neg|eq|gt|lt|and|or|not',
        'memory_access': 'push|pop',
        'branching': 'label|goto|if-goto',
        'function': 'function|return|call'
    },
    'segment' : 'argument|local|static|constant|this|that|pointer|temp'
}


# # Matches number of arguments to commands
# ARGS: dict[int, list[str]] = {
#     0 : [
#         'add',
#         'sub',
#         'neg',
#         'eq',
#         'gt',
#         'lt',
#         'and',
#         'or',
#         'not',
#         'return'
#     ],
#     1 : [
#         'label',
#         'goto',
#         'if-goto',
#     ],
#     2 : [
#         'push',
#         'pop',
#         'function',
#         'call',
#     ]
# }