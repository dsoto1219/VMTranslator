"""Parser tests."""
import VMTranslator as vmt
from constants import Command
import pytest


# tests for other segments, whitespace/comments, and end-of-line error
basic_test = r"C:\Users\danim\OneDrive\learn-coding\nand2tetris\projects\07\MemoryAccess\BasicTest\BasicTest.vm"
# tests for pointer segments
pointer_test = r"C:\Users\danim\OneDrive\learn-coding\nand2tetris\projects\07\MemoryAccess\PointerTest\PointerTest.vm"
# tests for static segments
static_test = r"C:\Users\danim\OneDrive\learn-coding\nand2tetris\projects\07\MemoryAccess\StaticTest\StaticTest.vm"
# tests for comparison commands
stack_test = r"C:\Users\danim\OneDrive\learn-coding\nand2tetris\projects\07\StackArithmetic\StackTest\StackTest.vm"


def test_basic_test():
    # Local Test
    with open(basic_test) as tf:
        parser = vmt.Parser(tf)
        # Line 1, "// This file is part of www.nand2tetris.org"
        assert parser.has_more_lines() == True
        assert parser.command_type == None

        # Line 5, "" (empty)
        for _ in range(4):
            parser.advance()

        # Advance to first line with real code
        # One test for each command type and segment combination
        for _ in range(2):
            parser.advance()
        # Line 7, "push constant 10"
        assert parser.has_more_lines() == True
        assert parser.command_type == Command.PUSH
        assert parser.arg1 == "constant"
        assert parser.arg2 == 10

        parser.advance()
        # Line 8, "pop local 0"
        assert parser.has_more_lines() == True
        assert parser.command_type == Command.POP
        assert parser.arg1 == "local"
        assert parser.arg2 == 0

        for _ in range(3):
            parser.advance()
        # Line 11, "pop argument 2"
        assert parser.has_more_lines() == True
        assert parser.command_type == Command.POP
        assert parser.arg1 == "argument"
        assert parser.arg2 == 2

        for _ in range(10):
            parser.advance()
        # Line 21, "push local 0"
        assert parser.command_type == Command.PUSH
        assert parser.arg1 == "local"
        assert parser.arg2 == 0

        for _ in range(3):
            parser.advance()
        # Line 24, "push argument 1"
        assert parser.command_type == Command.PUSH
        assert parser.arg1 == "argument"
        assert parser.arg2 == 1

        parser.current_line_index = 32
        assert parser.has_more_lines() == False
        with pytest.raises(IndexError):
            parser.advance()


def test_pointer_test():
    with open(pointer_test) as tf:
        parser = vmt.Parser(tf)
        for _ in range(8):
            parser.advance()
        # Goto line 9, "pop pointer 0"
        assert parser.command_type == Command.POP
        assert parser.arg1 == "pointer"
        assert parser.arg2 == 0

        parser.advance()
        parser.advance()
        # Line 11, "pop pointer 1"
        assert parser.command_type == Command.POP
        assert parser.arg1 == "pointer"
        assert parser.arg2 == 1

        parser.advance()
        parser.advance()
        # Line 13, "pop this 2"
        assert parser.command_type == Command.POP
        assert parser.arg1 == "this"
        assert parser.arg2 == 2

        parser.advance()
        parser.advance()
        # Line 15, "pop that 6"
        assert parser.command_type == Command.POP
        assert parser.arg1 == "that"
        assert parser.arg2 == 6

        for _ in range(4):
            parser.advance()
        # Line 19, "pop that 6"
        assert parser.command_type == Command.PUSH
        assert parser.arg1 == "this"
        assert parser.arg2 == 2

        parser.advance()
        parser.advance()
        # Line 21, "pop that 6"
        assert parser.command_type == Command.PUSH
        assert parser.arg1 == "that"
        assert parser.arg2 == 6


def test_static_test():
    with open(static_test) as tf:
        parser = vmt.Parser(tf)
        for _ in range(9):
            parser.advance()
        # Line 10, "pop static 8"
        assert parser.command_type == Command.POP
        assert parser.arg1 == "static"
        assert parser.arg2 == 8

        for _ in range(3):
            parser.advance()
        # Line 12, "push static 3"
        assert parser.command_type == Command.PUSH
        assert parser.arg1 == "static"
        assert parser.arg2 == 3


def test_stack_test():
    with open(stack_test) as tf:
        parser = vmt.Parser(tf)
        for _ in range(9):
            parser.advance()
        # Line 10, "eq"
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg1 == "eq"
        # Make sure getting arg2 raises error
        with pytest.raises(vmt.ParserError) as pe:
            parser.arg2
        assert str(pe.value) == ("In StackTest.vm, line 10 (eq): arg2 should "
                                 "only be accessed if command type is PUSH, "
                                 "POP, FUNCTION, or CALL, not "
                                 "Command.ARITHMETIC")

        for _ in range(9):
            parser.advance()
        # Line 19, "lt"
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg1 == "lt"
        # Make sure assignment raises error
        with pytest.raises(vmt.ParserError) as pe:
            parser.arg2 = 2
        assert str(pe.value) == ("In StackTest.vm, line 19 (lt): arg2 should "
                                 "only be assigned if command type is PUSH, "
                                 "POP, FUNCTION, or CALL, not "
                                 "Command.ARITHMETIC")

        for _ in range(9):
            parser.advance()
        # Line 28, "lt"
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg1 == "gt"

        for _ in range(10):
            parser.advance()
        # Line 38, "add"
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg1 == "add"

        for _ in range(2):
            parser.advance()
        # Line 40, "sub"
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg1 == "sub"

        parser.advance()
        # Line 41, "neg"
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg1 == "neg"

        parser.advance()
        # Line 42, "and"
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg1 == "and"


        parser.advance()
        parser.advance()
        # Line 44, "or"
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg1 == "or"

        parser.advance()
        # Line 45, "not"
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg1 == "not"