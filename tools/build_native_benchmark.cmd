@echo off
setlocal
set "VCVARS=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if not exist "%VCVARS%" (
  echo MSVC vcvars64.bat was not found. 1>&2
  exit /b 1
)
call "%VCVARS%" >nul
if errorlevel 1 exit /b %errorlevel%
if not exist "benchmarks\results" mkdir "benchmarks\results"
cl /nologo /O2 /GL /W4 /Fe:benchmarks\results\numeric_loop_native.exe benchmarks\runtime\numeric_loop_native.c /link /LTCG
