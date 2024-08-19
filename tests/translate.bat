@echo off
rem This script runs VMTranslator.py on all .vm files in the specified directory.

rem Check if the user provided a directory as an argument
if "%~1"=="" (
    echo Error: No directory provided.
    echo Usage: translator.bat path/
    pause
    exit /b
)

rem Check if the provided directory exists
if not exist "%~1" (
    echo Error: The specified directory does not exist.
    pause
    exit /b
)

rem Ensure a file named "VMTranslator.py" is in the current directory
if not exist "VMTranslator.py" (
    echo Error: VMTranslator.py not found in the current directory.
    echo Please ensure that VMTranslator.py is in the same directory as this script.
    pause
    exit /b
)
rem Save VMTranslator path to variable
set "vm_translator_path=%cd%\VMTranslator.py"

rem Go to the specified directory
cd /d "%~1"

rem Loop over all files and translate them
for /r %%f in (*.vm) do (
    echo Processing %%f
    python %vm_translator_path% %%f
)

echo All .vm files have been translated.