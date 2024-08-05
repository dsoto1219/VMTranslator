import argparse
import constants
from constants import Command, REGEXES
import os.path
import re
from textwrap import dedent
from typing import TextIO


class Parser:
    """
    Object for parsing file with vm code. See (Nisan & Schocken, 2021, p. 196)
    for motivation.
    """
    def __init__(self, input_file: TextIO) -> None:
        self.lines: list[str] = input_file.readlines()
        self.current_line_index: int = 0
        self.current_line: str = self.lines[self.current_line_index]
        self.command_type: str = ""
        # self.arg1: str = ""
        # self.arg2: str = ""
        self._parse_line()

    def _parse_line(self) -> None:
        """
        Parses current line of vm code with regex, with expected format
            command arg1 arg2
        into the tuple, (command, arg1, arg2), where arg1 and arg2 are 
        optional.
        The current line is considered valid if it can either be parsed into
        this form or if it is a comment or whitespace. If line is not valid, 
        the method raises an AttributeError.
        """
        # regex = re.compile(r'''
        #     (?:\s*({arithmetic})\s*)|
        #     (?:\s*({memory_access})\s+({segments})\s+(\d+)\s*)
        # '''.format(arithmetic=REGEXES['command']['arithmetic'], 
        #         memory_access=REGEXES['command']['memory_access'],
        #         segments=REGEXES['segment']),
        #         re.X)
        if matches := re.match(r"(\w+) ?(\w+)? ?(\d+)?(?:://.*)?", 
                               self.current_line):
            self._parsed_line = tuple(matches.groups())
        # Case for whitespace or comment
        elif re.match(r"\s*(//.*)?", self.current_line):
            self._parsed_line = (None, None, None)
        else:
            raise AttributeError(f"Line {self.current_line_index + 1} "
                                 f"({self.current_line}) could not be parsed.")
        # Always run: even if the current line is whitespace/comment, this will
        # return None.
        self._get_command_type()

    def has_more_lines(self) -> bool:
        """
        Has the index of the current line we are parsing yet to exceed the 
        index of the last line of the VM code?

        Ex: If len(self.lines) = 16, the index of the last line in self.lines
        is len(self.lines) - 1 = 15. So, if self.current_line_index = 10, we
        have not passed the last line, nor have we if 
        `self.current_line_index = 15`. But if `self.current_line_index = 16`,
        we have passed it.
        """
        return self.current_line_index < len(self.lines) 
    
    def advance(self) -> None:
        """
        Advances to next line in VM code and parses the code. Expects user to
        check if there are any lines left via the `has_more_lines` method.
        """
        self.current_line_index += 1
        self.current_line = self.lines[self.current_line_index]
        self._parse_line()
    
    def _get_command_type(self) -> Command | None:
        """
        Reads the first entry of the parsed line (does not check if it exists)
        and returns its corresponding Command enum.
        """
        match self._parsed_line[0]:
            case "add"|"sub"|"neg"|"eq"|"gt"|"lt"|"and"|"or"|"not":
                self.command_type = Command.ARITHMETIC
            case "push":
                self.command_type = Command.PUSH
            case "pop":
                self.command_type = Command.POP
            case "label":
                self.command_type = Command.LABEL
            case "goto":
                self.command_type = Command.GOTO
            case "if-goto":
                self.command_type = Command.IF
            case "function":
                self.command_type = Command.FUNCTION
            case "return":
                self.command_type = Command.RETURN
            case "call":
                self.command_type = Command.CALL
            case _:
                self.command_type = None
    
    def arg(self, index: int) -> str:
        """
        Returns the (index)th argument of the current command, i.e. arg(1) to
        return 1st argument and arg(2) to return 2nd argument. 
        Notes:
        - If the current command is arithmetic, `arg(1)` returns the command
          (i.e. if the command is `"add"`, `arg(1)` returns `"add"`).
        - If the current command is a PUSH or POP command, checks whether the
          argument is within the set of valid segments (see `constants.py`).
        - `arg(1)` does not work for RETURN type.
        - `arg(2)` works only for Command enums PUSH, POP, FUNCTION, and CALL.
        """
        match index:
            case 1 if self.command_type != Command.RETURN:
                if self.command_type == Command.ARITHMETIC:
                    return self._parsed_line[0]
                if self.command_type in {Command.PUSH, Command.POP} and \
                (segment := self._parsed_line[index]) \
                not in constants.SEGMENT_SYMBOLS:
                    raise ValueError(f"Invalid segment {segment} for "
                                     f"{self.command_type} command.")
                return self._parsed_line[index]
            # The only commands with a second argument are the following
            case 2 if self.command_type in {
                Command.PUSH,
                Command.POP,
                Command.FUNCTION,
                Command.CALL,
            }:
                return int(self._parsed_line[index])
            case _:
                raise ValueError(f"Invalid argument index ({index}), for "
                                 f"command type {self.command_type}")


class CodeWriter:
    """
    Object for writing code to the .asm file. User is expected to open file
    outside of the class. Contains vital methods for converting VM code to
    HACK assmebly.
    """

    def __init__(self, outfile: TextIO, comments_on: bool) -> None:
        self.outfile = outfile
        # If true, prints a comment above each sequence of asm commands
        # that tells you which vm code command it is executing.
        self.comments_on = comments_on 
        # From (Nisan & Schocken, 2021, p. 188): Initialize stack to start at 
        # RAM address 256
        self._SP_INIT = dedent('''\
                    @256
                    D=A
                    @SP
                    M=D
                    ''')
        self.outfile.write(self._SP_INIT)
        # For `write_arithmetic`` method. Some vm commands require labels in
        # order to work. To avoid creating multiple labels of the same name,
        # we number the labels starting from 1, and increment their numbers 
        # after printing them.
        self.label_cnts = {
            "eq" : 1,
            "gt" : 1,
            "lt" : 1, 
            "continue": 1
        }
        # For `write_push_pop` method.
        self._static_register = 16
        self._temp_register = 5

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
        if self.comments_on:
            self.outfile.write(f"// {vm_command}\n")
        # Start with A register one address below the top of the stack. The 
        # value at M is the first argument.
        self.outfile.write(dedent('''\
                @SP
                A=M-1
                '''))
        # If the command takes in two arguments, save the first argument into
        # D register and decrement the A register so that the second argument
        # is in the M register.
        if vm_command not in {"neg", "not"}:
            self.outfile.write(dedent('''\
                    D=M
                    A=A-1
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
            case "eq":
                asm_cmd = '''\
                @EQ.{m}
                D-M;JEQ
                M=0
                @CONTINUE.{n}
                0;JMP
                (EQ.{m})
                    M=-1
                (CONTINUE.{n})
                '''.format(m=self.label_cnts["eq"],
                                    n=self.label_cnts["continue"])
                self.label_cnts["eq"] += 1
                self.label_cnts["continue"] += 1
            case "gt":
                asm_cmd = '''\
                @GT.{m}
                D-M;JGT
                M=0
                @CONTINUE.{n}
                0;JMP
                (GT.{m})
                    M=-1
                (CONTINUE.{n})
                '''.format(m=self.label_cnts["gt"], 
                           n=self.label_cnts["continue"])
                self.label_cnts["gt"] += 1
                self.label_cnts["continue"] += 1
            case "lt":
                asm_cmd = '''\
                @LT.{m}
                D-M;JLT
                M=0
                @CONTINUE.{n}
                0;JMP
                (LT.{m})
                    M=-1
                (CONTINUE.{n})
                '''.format(m=self.label_cnts["lt"], 
                           n=self.label_cnts["continue"])
                self.label_cnts["lt"] += 1
                self.label_cnts["continue"] += 1
            # Logical commands
            case "and":
                asm_cmd = 'M=D&M\n'
            case "or":
                asm_cmd = 'M=D|M\n'
            case "not":
                asm_cmd = 'M=!M\n'
        self.outfile.write(dedent(asm_cmd))
        # Increment stack pointer, and leave A register pointing to the top of
        # the stack.
        self.outfile.write(dedent('''\
                D=A+1
                @SP
                AM=D
                '''))
    
    def write_push_pop(self, command: Command, 
                       segment: str, 
                       index: int) -> None:
        """
        Writes to the output file the assembly code that implements the given
        `push` or `pop` `command`.
        """
        if self.comments_on:
            self.outfile.write(f"// {command} {segment} {index}")

        # Some of the segments are "static", meaning they point to a specific,
        # unchanging RAM address, while others are "dynamic", meaning the 
        # addresses that they point to change over time.
        register: str
        # "Static" segments have their symbols stored in `SEGMENT_SYMBOLS`
        if seg_symbol := constants.SEGMENT_SYMBOLS[segment]:
            register = seg_symbol
        # "Dynamic" segments have no symbol stored, and have to be handled
        # as follows
        else:
            match segment:
                case "static":
                    register = f"R{self._static_register}"
                    self._static_register += 1
                case "temp":
                    register = f"R{self._temp_register}"
                    self._temp_register += 1
                case "pointer":
                    if index in {0, 1}:
                        register = f"R{3 + index}"
                    else:
                        raise ValueError("pointer can only be 0 or 1")
        match command:
            case Command.PUSH:
                self.outfile.write(dedent('''\
                        @{i}
                        D=A
                        @{seg}
                        A=M
                        M=D
                        @{seg}
                        M=M+1
                        ''').format(seg = register,
                                    i = index))
            case Command.POP:
                self.outfile.write(dedent('''\
                        @{i}
                        D=A
                        @{seg}
                        A=M
                        M=D
                        @{seg}
                        M=M+1
                        ''').format(seg = register,
                                    i = index))


def main():
    argparser = argparse.ArgumentParser(
        prog='VMTranslator',
        description="Translates .vm files into HACK Assembly files (ending in .asm)",
    )
    argparser.add_argument('infile')
    argparser.add_argument('-c', '--comments-on', action='store_true')
    args = argparser.parse_args()

    filename, ext = os.path.splitext(args.infile)
    if ext != ".vm":
        raise AttributeError(f"File {args.infile} does have a .vm extension!")

    with open(args.file) as in_f, open(f"{filename}.asm") as out_f:
        parser = Parser(in_f)
        writer = CodeWriter(out_f, args.c)
        while parser.has_more_lines():
            match parser.command_type:
                case Command.ARITHMETIC:
                    writer.write_arithmetic(parser.arg(1))
            parser.advance()


if __name__ == "__main__":
    main()