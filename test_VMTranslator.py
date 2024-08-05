import VMTranslator as vmt
from constants import Command
import pytest


basic_test = r"C:\Users\danim\OneDrive\learn-coding\nand2tetris\projects\07\MemoryAccess\BasicTest\BasicTest.vm"

# Parser tests
def test_parser():
    with open(basic_test) as tf:
        parser = vmt.Parser(tf)
        assert parser.has_more_lines() == True
        assert parser.command_type == None

        # Advance to first line with real code
        # One test for each command type
        for _ in range(6):
            parser.advance()
        assert parser.has_more_lines() == True
        assert parser.command_type == Command.PUSH
        assert parser.arg(1) == "constant"
        assert parser.arg(2) == 10

        parser.advance()
        assert parser.has_more_lines() == True
        assert parser.command_type == Command.POP
        assert parser.arg(1) == "local"
        assert parser.arg(2) == 0

        for _ in range(15):
            parser.advance()
        assert parser.has_more_lines() == True
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg(1) == "add"
        with pytest.raises(ValueError):
            parser.arg(2)
        
        parser.advance()
        parser.advance()
        assert parser.has_more_lines() == True
        assert parser.command_type == Command.ARITHMETIC
        assert parser.arg(1) == "sub"
        with pytest.raises(ValueError):
            parser.arg(2)

        with pytest.raises(IndexError):
            for _ in range(7):
                parser.advance()