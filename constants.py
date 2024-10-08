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


"""Set of all commands in the VM language."""
COMMANDS = {
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


"""COMMANDS commands organized as a dictionary."""
TYPE_COMMANDS: dict[str, list[str]] = {
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


"""
Conversion of segment symbols as they would appear in VM code to how they
would appear in HACK assembly. 
- If base address is contained within a symbol, a symbol is listed.
- If the symbol refers to a range of addresses, an empty string is provided
that denotes this.
"""
SEGMENT_SYMBOLS: dict = {
    "argument" : "ARG",
    "local" : "LCL",
    "static" : "", # RAM[16-255]
    "constant" : "SP",
    "this" : "THIS",
    "that" : "THAT",
    "pointer" : {0: "THIS", 1: "THAT"}, # RAM[THIS], RAM[THAT]
    "temp" : "R5",
}


"""Strings for regex checks."""
REGEXES: dict = {
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