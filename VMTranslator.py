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
        # Although we don't store the file object itself, we store its 
        # filename in case of an error (see ParserError).
        self.filename = input_file.name

        self.lines: list[str] = input_file.readlines()
        # Index of the current line. We initialize this at -1 so that when we
        # call advance, we go to the first line of code (at index 0, a.k.a. 
        # line no. 1)
        self.current_line_index: int = -1
        self.current_line: str # Stores current line as a string

        # Intialize relevant tokens to be searched for in each line. Instead 
        # of using the suggested subroutines for these, we use class variables.
        self.command_type: Optional[Command] = None
        self._arg1: str
        self._arg2: int
    
    @property
    def arg1(self) -> Optional[str]:
        """
        Returns the first argument of the current command.

        In the case of a Command.ARITHMETIC, the command itself 
        (add, sub, etc.) is returned. 

        Should not be called if the current command is Command.RETURN.
        """
        if self.command_type == Command.RETURN:
            raise ValueError("arg1 should not be assigned if command type "
                              "is RETURN")
        return self._arg1
    
    @arg1.setter
    def arg1(self, value: str) -> None:
        if self.command_type == Command.RETURN:
            raise ValueError("arg1 should not be assigned if command type "
                              "is RETURN")
        self._arg1 = value

    @property
    def arg2(self) -> Optional[int]:
        """
        Returns the second argument of the current command. Should only be
        called if the current command is PUSH, POP, FUNCTION, or CALL.
        """
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
                \s*(?://.*)?$              # Optional whitespace+comment
                '''.format(arithmetic_cmds=REGEXES['command']['arithmetic']),
                string=self.current_line,
                flags=re.X):
            self.command_type = Command.ARITHMETIC
            self.arg1 = matches.groupdict()['cmd']
            assert self.arg1 in constants.TYPE_COMMANDS['arithmetic'], \
                ("Regex error, incorrectly found arg1 to not be one of the "
                "valid arithmetic commands.")
        # Case 2: Memory access command (push, pop)
        elif matches := re.fullmatch(
                pattern=r'''
                ^\s*                             # Optional whitespace
                (?P<cmd>{memory_access_cmds})\s+ # Valid memory access command
                (?P<segment>{valid_segments})\s+ # Valid virtual memory segment
                (?P<index>\d+)                   # Any non-negative integer
                \s*(?://.*)?$                    # Optional whitespace+comment
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
        Returns True if there are more lines in the input, returns False 
        otherwise. In particular, we return false if we have reached the
        last line of the input.
        """
        return self.current_line_index < len(self.lines) - 1
    
    def advance(self) -> None:
        """
        Advances to next line in the input and parses the code. This routine
        should only be called if has_more_lines() is True. Initially, there is
        no current command.
        """
        self.current_line_index += 1
        self.current_line = self.lines[self.current_line_index]
        self._parse_line()


class ParserError(Exception):
    """
    Custom exception that takes in an instance of a parser object, and
    prints out the current file and line that is being parsed along with the
    line number. If an error message is provided, this message will be printed
    alongside this information.
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
        arithmetic-logical `command`. See Nisan & Schocken, 2021 for details.
        """
        if not self.comments_off:
            self.outfile.write(f"// {vm_command}\n")


        # If the command takes in only one argument, the implementation 
        # specifies that we pop one element off of the stack and push its 
        # result back onto the stack (Nisan & Schocken, 2021, p. 187). Thus,
        # since there is no change to the stack pointer, we simply access the
        # value directly below the stack pointer as use this as our argument.
        if vm_command in {"neg", "not"}:
            self.outfile.write(dedent('''\
                    @SP
                    A=M-1
                '''))
        # If the command takes in two arguments, the implementation specifies
        # that we pop two elements off of the stack and push their result onto
        # the stack (Nisan & Schocken, 2021, p. 187). The net effect of this is
        # decrementing the stack pointer once. Thus, with this in mind,
        # mind, we start by decrementing the stack pointer (this will be 
        # the only modification to SP), save the our first argument into the D
        # register, and decrement the A register so that the second argument is 
        # in the M register.
        else:
            self.outfile.write(dedent('''\
                    @SP
                    AM=M-1
                    D=M
                    A=A-1
                '''))
        asm_cmd: str
        match vm_command:
            ## Arithmetic Commands 
            case "add":
                asm_cmd = 'M=D+M\n'
            case "sub":
                asm_cmd = 'M=D-M\n'
            case "neg":
                asm_cmd = 'M=-M\n'
            # For comparison and logical commands, the result is -1 if the 
            # operation is true, and the result is 0 if the operation is false
            # (Nisan & Schocken, 2021, p. 189).
            ## Comparison Commands
            case "eq"|"gt"|"lt":
                asm_cmd = dedent('''\
                    @.{CMD}.{N}
                    D-M;J{CMD}
                    M=0
                    @.END_{CMD}.{N}
                    0;JMP
                    (.{CMD}.{N})
                        M=-1
                    (.END_{CMD}.{N})
                ''').format(CMD=vm_command.upper(), 
                            N=self.label_cnts[vm_command])
                self.label_cnts[vm_command] += 1
            ## Logical commands
            case "and":
                asm_cmd = 'M=D&M\n'
            case "or":
                asm_cmd = 'M=D|M\n'
            case "not":
                asm_cmd = 'M=!M\n'
        self.outfile.write(asm_cmd)
    
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
            command: str
            match command_type:
                case Command.PUSH:
                    command = "push"
                case Command.POP:
                    command = "pop"
            self.outfile.write(f"// {command} {segment} {index}\n")

        # The value for the A-instruction that we use to get the address of
        # the desired segment
        symbol: str | dict = constants.SEGMENT_SYMBOLS[segment]
        if segment == "pointer":
            try:
                symbol = symbol[index]
            except IndexError:
                raise ValueError("Indices for pointer segments can "
                                    "only be 0 or 1")
        elif segment == "static":
            symbol = f"{Path(self.outfile.name).stem}.{index}"
        
        if command_type == Command.PUSH:
            target: str # Where to store what we get after the A-instruction

            # If segment is constant, think of the A-register as storing a 
            # value, and we that value to the D-register
            if segment == "constant":
                symbol = index
                target = 'A'
            # Otherwise, think of the A-register as storing an address, and
            # store the value at that address in the D-register
            else:
                target = 'M'

            # Access address of base segment
            self.outfile.write(f"@{symbol}\n")

            if segment not in {"pointer", "constant", "static"}:
                # For segments for which the index gives us trouble: If the 
                # index is greater than 0, save the base pointer to the 
                # D-register, and get to the address by setting the A-register
                # to the index and adding the base address to it
                if index > 0:
                    self.outfile.write(dedent('''\
                            D=M
                            @{INDEX}
                            A=D+A
                        ''').format(INDEX=index))
                # For otherwise trivial segments, simply set the A-register to 
                # the address at the base pointer
                else:
                    self.outfile.write("A=M\n")
        
            # Save the value at the address to the D-register
            self.outfile.write(f"D={target}\n")

            # Access the top of the stack and set its value to the D-register,
            # then increment the stack pointer
            self.outfile.write(dedent('''\
                    @SP
                    A=M
                    M=D
                    @SP
                    M=M+1
                '''))

        elif command_type == Command.POP:
            # Pop the top value off of the stack and save it into the 
            # D-register
            self.outfile.write(dedent('''\
                    @SP
                    AM=M-1
                    D=M
                '''))
            
            # In these simple cases, we simply take the value in the 
            # D-register and store it in the desired address, without much
            # issue.
            if segment in {"pointer", "static"} or index == 0:
                self.outfile.write(dedent('''\
                        @{SYMBOL}
                        M=D
                    ''').format(SYMBOL=symbol))
            # Outside of these cases, the implementation becomes more complex.
            # You are led to believe that the implemenation requires accessing
            # a temporary variable; however, this is not necessary. Credit to
            # https://evoniuk.github.io/posts/nand.html for this alternate 
            # implementation, which makes use of clever "register-algebra"
            # to implement this without temporary variables. I made a few
            # changes to reduce the line count, but the exact same 
            # functionality should remain.
            else:
                self.outfile.write(dedent('''\
                        @{SYMBOL}
                        D=D+M
                        @{INDEX}
                        D=D+A
                        @SP
                        A=M
                        A=D-M
                        M=D-A
                    ''').format(SYMBOL=symbol, INDEX=index))

    def write_end(self) -> None:
        """Write end-of-file loop to filename.asm."""
        self.outfile.write(dedent('''\

                (END)
                    @END
                    0;JMP'''))


def main():
    argparser = argparse.ArgumentParser(
        prog='VMTranslator',
        description="Takes in .vm files as input and outputs its "
                    "corresponding HACK Assembly file, ending in .asm",
        epilog=".asm files are saved to the same directory in which the .vm "
               "file was in")
    argparser.add_argument('infile')
    argparser.add_argument('-nc', '--no-comments', action='store_true')
    args = argparser.parse_args()

    filename, ext = os.path.splitext(args.infile)
    if ext != ".vm":
        raise AttributeError(f"File {args.infile} does have a .vm extension!")

    with open(args.infile) as in_f, open(f"{filename}.asm", "w") as out_f:
        parser = Parser(in_f)
        writer = CodeWriter(out_f, args.no_comments)
        while parser.has_more_lines():
            parser.advance()
            match parser.command_type:
                case Command.ARITHMETIC:
                    writer.write_arithmetic(parser.arg1)
                case Command.PUSH|Command.POP:
                    writer.write_push_pop(
                        parser.command_type,
                        parser.arg1,
                        parser.arg2)
        writer.write_end()


if __name__ == "__main__":
    main()