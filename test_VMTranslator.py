"""Parser tests."""
import VMTranslator as vmt
from constants import Command
import pytest


basic_test = r"C:\Users\danim\OneDrive\learn-coding\nand2tetris\projects\07\MemoryAccess\BasicTest\BasicTest.vm"
pointer_test = r"C:\Users\danim\OneDrive\learn-coding\nand2tetris\projects\07\MemoryAccess\PointerTest\PointerTest.vm"
static_test = r"C:\Users\danim\OneDrive\learn-coding\nand2tetris\projects\07\MemoryAccess\StaticTest\StaticTest.vm"


def test_basic_test():
    # Local Test
    with open(basic_test) as tf:
        parser = vmt.Parser(tf)
        # At line 1
        assert parser.has_more_lines() == True
        assert parser.command_type == None

        # Advance to first line with real code
        # One test for each command type
        for _ in range(6):
            parser.advance()
        # At line 7
        assert parser.has_more_lines() == True
        assert parser.command_type == Command.PUSH
        assert parser.arg1 == "constant"
        assert parser.arg2 == 10

        parser.advance()
        # At line 8
        assert parser.has_more_lines() == True
        assert parser.command_type == Command.POP
        assert parser.arg1 == "local"
        assert parser.arg2 == 0

        for _ in range(15):
            parser.advance()
        # At line 23
        assert parser.has_more_lines() == True
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg1 == "add"
        # Test for parser error
        with pytest.raises(vmt.ParserError) as pe:
            parser.arg2 = 2
        assert str(pe.value) == ("In BasicTest.vm, line 23 (add): arg2 should "
                                 "only be assigned if command type is PUSH, "
                                 "POP, FUNCTION, or CALL, not "
                                 "Command.ARITHMETIC")
        
        parser.advance()
        parser.advance()
        # At line 25
        assert parser.has_more_lines() == True
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg1 == "sub"
        with pytest.raises(vmt.ParserError) as pe:
            parser.arg2 = 2
        assert str(pe.value) == ("In BasicTest.vm, line 25 (sub): arg2 should "
                                 "only be assigned if command type is PUSH, "
                                 "POP, FUNCTION, or CALL, not "
                                 "Command.ARITHMETIC")

        # At line 32 (should be out of range)
        with pytest.raises(IndexError):
            for _ in range(7):
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
