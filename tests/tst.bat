@echo off
rem This script runs CPUEmulator.bat in all directories specified in the first argument

rem Check if the user provided a directory as an argument
if "%~1"=="" (
    echo Error: No directory provided.
    echo Usage: tst.bat path/
    pause
    exit /b
)

rem Check if the provided directory exists
if not exist "%~1" (
    echo Error: The specified directory does not exist.
    pause
    exit /b
)

rem Go to the specified directory
cd /d "%~1"

rem Loop over all files and translate them
for /r %%f in (*.tst) do @(
    rem Check if the filename contains 'VME'
    echo %%~nxf | findstr /i "VME" >nul
    rem If so, run the file
    if errorlevel 1 (
        echo Test file: %%~nxf
        CPUEmulator.bat %%f
    )
)