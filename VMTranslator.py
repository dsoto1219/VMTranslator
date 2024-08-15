import argparse
import constants
from constants import Command, REGEXES
import os.path
from pathlib import Path
import re
from textwrap import dedent
from typing import Optional, TextIO


class Parser:
    """
    Object for parsing file with vm code. See (Nisan & Schocken, 2021, p. 196)
    for motivation.
    """
    def __init__(self, input_file: TextIO) -> None:
        # Filename stored in case of an error, see ParserError
        self.filename = input_file.name

        self.lines: list[str] = input_file.readlines()
        self.current_line_index: int = 0
        self.current_line: str = self.lines[self.current_line_index]

        # Instead of using the suggested subroutines for these, 
        # we use class variables.
        self.command_type: Optional[Command] = None
        self._arg1: str
        self._arg2: int

        self._parse_line()
    
    @property
    def arg1(self) -> Optional[str]:
        return self._arg1
    
    @arg1.setter
    def arg1(self, value: str) -> None:
        if self.command_type == Command.RETURN:
            raise ValueError("arg1 should not be assigned if command type "
                              "is RETURN")
        self._arg1 = value

    @property
    def arg2(self) -> Optional[int]:
        """Returns the second argument of the current command."""
        if self.command_type not in {
                Command.PUSH,
                Command.POP,
                Command.FUNCTION,
                Command.CALL,
            }:
            raise ParserError(self, 
                              "arg2 should only be accessed if command type "
                              "is PUSH, POP, FUNCTION, or CALL, not "
                             f"{self.command_type}")
        return self._arg2
    
    @arg2.setter
    def arg2(self, value: int) -> None:
        if self.command_type not in {
                Command.PUSH,
                Command.POP,
                Command.FUNCTION,
                Command.CALL,
            }:
            raise ParserError(self, 
                              "arg2 should only be assigned if command type "
                              "is PUSH, POP, FUNCTION, or CALL, not "
                             f"{self.command_type}")
        self._arg2 = value

    def _parse_line(self) -> None:
        """
        Parses current line of vm code with regex, with the following possible
        valid formats:
            1. [arithmetic command]
            2. [push/pop] [segment] [index]
        And saves results into command_type, arg1, and arg2, accordingly.
        The current line is considered valid if it can either be parsed into
        this form or if it is a comment or whitespace. If line is not valid, 
        the method raises a corresponding ParserError.
        """
        self.current_line = self.current_line.rstrip()
        # Case 1: Arithmetic command (add, sub, eq, ...)
        if matches := re.fullmatch(
                pattern=r'''
                ^\s*                       # Optional whitespace
                (?P<cmd>{arithmetic_cmds}) # Valid arithmetic commands
                \s*(?://.*)?$            # Optional whitespace+comment
                '''.format(arithmetic_cmds=REGEXES['command']['arithmetic']),
                string=self.current_line,
                flags=re.X):
            self.command_type = Command.ARITHMETIC
            self.arg1 = matches.groupdict()['cmd']
            assert self.arg1 in constants.TYPE_COMMANDS['arithmetic'], \
                ("Regex error, incorrectly found arg1 to be one of the "
                "arithmetic commands.")
        # Case 2: Memory access command (push, pop)
        elif matches := re.fullmatch(
                pattern=r'''
                ^\s*                             # Optional whitespace
                (?P<cmd>{memory_access_cmds})\s+ # Valid memory access command
                (?P<segment>{valid_segments})\s+ # Valid virtual memory segment
                (?P<index>\d+)                   # Any non-negative integer
                \s*(?://.*)?$                  # Optional whitespace+comment
                '''.format(
                    memory_access_cmds=REGEXES['command']['memory_access'],
                    valid_segments=REGEXES['segment']),
                string=self.current_line,
                flags=re.X):
            mgd = matches.groupdict()
            match mgd['cmd']:
                case "push":
                    self.command_type = Command.PUSH
                case "pop":
                    self.command_type = Command.POP
                case _: # Incorrect parse
                    raise ParserError(self, f"Regex incorrectly matched "
                                      f"{mgd['cmd']} as a push/pop command "
                                       "(Error in Parser implementation).")
            self.arg1 = mgd['segment']
            try:
                self.arg2 = int(mgd['index'])
            except ValueError:
                raise ParserError(self, "Regex incorrectly matched index "
                                        "that is not a number (Error in "
                                        "Parser implementation.")
            # regex should never match this, but adding this anyway to add a 
            # first line of defense for CodeWriter
            if self.arg2 < 0:
                raise ParserError(self, "Regex incorrectly matched negative "
                                        "index (Error in Parser "
                                        "implementation)")
            
            # Segment-specific checks (Nisan & Schocken, 2021, p. 191)
            if self.arg1 == "pointer" and self.arg2 not in {0, 1}:
                raise ParserError(self, "When segment is pointer, index "
                                        "should either be 0 or 1")
            if self.arg1 == "temp" and (self.arg2 < 5 or self.arg2 > 12):
                raise ParserError(self, "temp index must be between 5 and 12, "
                                        "inclusive")
            if self.arg1 == "constant" and self.command_type == "pop":
                raise ParserError(self, "pop not defined when segment is "
                                        "constant")
            if self.arg1 == "static" and self.arg2 > 239:
                raise ParserError(self, "segment index can only be between 0 "
                                        "and 239, inclusive")
        # Last case: All whitespace or comment
        elif matches := re.fullmatch(
                pattern=r"^\s*(?://.*)?$", 
                string=self.current_line):
            self.command_type = None
            # Not part of specification: if whitespace, arg1 will return
            # full contents of current line
            self.arg1 = self.current_line
        else: # Unknown error
            raise ParserError(self, "Unforseen error.")

    def has_more_lines(self) -> bool:
        """
        Return True if the current line of code (at current_line_index) is the
        last line of code in the file, returns False otherwise.
        """
        return self.current_line_index < len(self.lines) - 1
    
    def advance(self) -> None:
        """
        Advances to next line in VM code and parses the code. Expects user to
        check if there are any lines left via the `has_more_lines` method.
        """
        self.current_line_index += 1
        self.current_line = self.lines[self.current_line_index]
        self._parse_line()


class ParserError(Exception):
    """
    Custom exception that takes in an optional line number and filename, and
    prints this information alongside an error message if provided.
    """
    def __init__(self, parser: Parser, message: str="") -> None:
        info: str = (f"In {os.path.basename(parser.filename)}, "
                     f"line {parser.current_line_index + 1} "
                     f"({parser.current_line})")
        if message:
            info = info + f": {message}"
        super().__init__(info)


class CodeWriter:
    """
    Object for writing code to the .asm file. User is expected to open file
    outside of the class. Contains vital methods for converting VM code to
    HACK assmebly.
    """

    def __init__(self, outfile: TextIO, comments_off: bool) -> None:
        self.outfile = outfile
        # If True, prints a comment above each sequence of asm commands
        # that tells you which vm code command it is executing.
        self.comments_off = comments_off 
        # Initialize stack to start at RAM address 256 
        # (Nisan & Schocken, 2021, p. 188):
        self._SP_INIT = dedent('''\
                    @256
                    D=A
                    @SP
                    M=D
                    ''')
        self.outfile.write(self._SP_INIT)
        # This dictionary is for the `write_arithmetic`` method. Its comparison
        # commands require labels in order to work---to avoid creating multiple
        # labels of the same name, we number the labels starting from 1, and
        # increment their numbers after printing them.
        self.label_cnts: dict[str, int] = {
            "eq" : 1,
            "gt" : 1,
            "lt" : 1,
        }

    def write_arithmetic(self, vm_command: str) -> None:
        """
        Writes to the output file the assembly code that implements the given 
        arithmetic-logical `command`.

        The two-argument commands work by popping the last two elements off the
        stack, computing their result, and pushing that result to the stack.
        The one-argument commands work in the same way, only they pop the last
        element off only (Nisan & Schocken, 2021, p. 187).

        For comparison and logical commands, the result is -1 if the operation
        is true, and the result is 0 if the operation is false (source: 
        testing with `VMTranslator.bat`).
        """
        if not self.comments_off:
            self.outfile.write(f"// {vm_command}\n")
        # Start with A register one address below the top of the stack. The 
        # value at M is the first argument. We also decrement the stack 
        # pointer.
        self.outfile.write(dedent('''\
                @SP
                AM=M-1
                '''))
        # If the command takes in two arguments, save the first argument into
        # D register and decrement the A register so that the second argument
        # is in the M register. We also, again, decrement the stack pointer.
        if vm_command not in {"neg", "not"}:
            self.outfile.write(dedent('''\
                    D=M
                    AM=A-1
                    '''))
        asm_cmd: str
        match vm_command:
            # Arithmetic Commands 
            case "add":
                asm_cmd = 'M=D+M\n'
            case "sub":
                asm_cmd = 'M=D-M\n'
            case "neg":
                asm_cmd = 'M=-M\n'
            # Comparison Commands
            case "eq"|"gt"|"lt":
                asm_cmd = dedent('''\
                    @.{CMD}{N}
                    D-M;J{CMD}
                    M=0
                    @.END-{CMD}{N}
                    0;JMP
                    (.{CMD}{N})
                        M=-1
                    (.END-{CMD}{N})
                    ''').format(CMD=vm_command.upper(), 
                            n=self.label_cnts[vm_command])
                self.label_cnts[vm_command] += 1
            # Logical commands
            case "and":
                asm_cmd = 'M=D&M\n'
            case "or":
                asm_cmd = 'M=D|M\n'
            case "not":
                asm_cmd = 'M=!M\n'
        self.outfile.write(asm_cmd)
        # Increment stack pointer.
        self.outfile.write(dedent('''\
                @SP
                M=M+1
                '''))
    
    def write_push_pop(self, command_type: Command, 
                       segment: str, 
                       index: int) -> None:
        """
        Writes to the output file the assembly code that implements the given
        `push` or `pop` `command`. See (Nisan & Schocken, 2021, p. 191-192)
        for implementation details.
        """
        if command_type not in {Command.PUSH, Command.POP}:
            raise ValueError(f"Command type {command_type} invalid, must be "
                              "Command.PUSH or Command.POP (Parser error)")
        if index < 0:
            raise ValueError(f"Index {index} invalid, must be non-negative " 
                              "(Parser Error)")

        if not self.comments_off:
            self.outfile.write(f"// {command_type} {segment} {index}")

        asm_cmd: str
        match segment:
            case "local"|"argument"|"this"|"that":
                if command_type == Command.PUSH:
                    # Push item at segment index to the stack. 
                    asm_cmd = dedent('''\
                        @{SYM}
                        D=M
                        @{IND}
                        D=D+A
                        @SP
                        A=M
                        M=D
                        @SP
                        M=M+1
                    ''').format(SYM=constants.SEGMENT_SYMBOLS[segment],
                                IND=index)
                elif command_type == Command.POP:
                    # Credit to https://evoniuk.github.io/posts/nand.html for 
                    # this implementation, which makes use of clever 
                    # "register-algebra" to implement this without temp 
                    # variables. I made a few changes to reduce the count, but
                    # it should work exactly the same.
                    asm_cmd = dedent('''\
                        @SP
                        AM=M-1
                        D=M
                        @{SYM}
                        D=D+M
                        @{IND}
                        D=D+A
                        @SP
                        A=M
                        A=D-M
                        M=D-A
                    ''').format(SYM=constants.SEGMENT_SYMBOLS[segment],
                                IND=index)
            case "pointer":
                sym: str
                if index == 0:
                    # "pointer 0" correponds to "THIS" register pointer
                    sym = "THIS"
                elif index == 1:
                    # "pointer 1" correponds to "THAT" register pointer
                    sym = "THAT"
                else:
                    raise ValueError(f"Index {index} invalid, must be either "
                                      "0 or 1 (Parser error).")

                if command_type == Command.PUSH:
                    # Push value at THIS or THAT to the stack.
                    asm_cmd = dedent('''\
                        @{SYM}
                        D=M
                        @SP
                        A=M
                        M=D
                        @SP
                        M=M+1
                    ''').format(SYM=sym)
                elif command_type == Command.POP:
                    # Pop top of the stack to THIS or THAT pointer.
                    asm_cmd = dedent('''\
                        @SP
                        AM=M-1
                        D=M
                        @{SYM}
                        M=D
                    ''').format(SYM=sym)
            case "temp":
                if index > 7:
                    raise ValueError(f"Index {index} invalid, must be between "
                                      "0 and 7, inclusive.")

                if command_type == Command.PUSH:
                    # Push value at RAM[5 + i] to the stack.
                    asm_cmd = dedent('''\
                        @R5
                        D=A
                        @{IND}
                        A=D+A
                        D=M
                        @SP
                        A=M
                        M=D
                        @SP
                        M=M+1
                    ''').format(IND=index)
                elif command_type == Command.POP:
                    # Pop top of the stack to RAM[5 + index]. Uses the same
                    # trick as the Pop command in the first case.
                    asm_cmd = ('''\
                        @SP
                        AM=M-1
                        D=M
                        @R5
                        D=D+A
                        @{IND}
                        D=D+A
                        @SP
                        A=M
                        A=D-M
                        M=D-A
                    ''').format(IND=index)
            case "constant":
                if command_type == Command.PUSH:
                    # Push constant value to the stack.
                    asm_cmd = dedent('''\
                        @{CONST}
                        D=A
                        @SP
                        A=M
                        M=D
                        @SP
                        M=M+1
                    ''').format(CONST=index)
                elif command_type == Command.POP:
                    # Command isn't allowed. Source:
                    # http://nand2tetris-questions-and-answers-forum.52.s1.nabble.com/I-m-confused-in-push-pop-constent-x-td4028972.html
                    raise ValueError("Undefined behavior: cannot pop constant off of stack.")
            case "static":
                if index > 239:
                    raise ValueError(f"Index {index} invalid, must be an "
                                      "integer between 16 and 255, inclusive "
                                      "(Parser Error)")
                
                if command_type == Command.PUSH:
                    asm_cmd = '''\
                        @{FILENAME}.{IND}
                        D=M
                        @SP
                        A=M
                        M=D
                        @SP
                        M=M+1
                    '''.format(FILENAME=Path(self.outfile.name).stem,
                               IND=index)
                elif command_type == Command.POP:
                    asm_cmd = '''\
                        @SP
                        AM=M-1
                        D=M
                        @{FILENAME}.{IND}
                        M=D
                    '''.format(FILENAME=Path(self.outfile.name).stem,
                               IND=index)

        self.outfile.write(asm_cmd)


def main():
    argparser = argparse.ArgumentParser(
        prog='VMTranslator',
        description="Translates .vm files into HACK Assembly files "
                    "(ending in .asm)",
    )
    argparser.add_argument('infile')
    argparser.add_argument('-nc', '--no-comments', action='store_false')
    args = argparser.parse_args()

    filename, ext = os.path.splitext(args.infile)
    if ext != ".vm":
        raise AttributeError(f"File {args.infile} does have a .vm extension!")

    with open(args.infile) as in_f, open(f"{filename}.asm", "w") as out_f:
        parser = Parser(in_f)
        writer = CodeWriter(out_f, args.no_comments)
        while parser.has_more_lines():
            match parser.command_type:
                case Command.ARITHMETIC:
                    writer.write_arithmetic(parser.arg1)
                case Command.PUSH|Command.POP:
                    writer.write_push_pop(
                        parser.command_type,
                        parser.arg1,
                        parser.arg2
                    )
            parser.advance()


if __name__ == "__main__":
    main()