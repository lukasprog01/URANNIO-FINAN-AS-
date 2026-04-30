@echo off
title URANNIO Financas — Build v1.0
color 0A

echo.
echo  ============================================
echo   URANNIO Financas — Sistema de Build v1.0
echo  ============================================
echo.

REM ── Verificar PyInstaller ──────────────────────────────────────────────────
echo [1/4] Verificando dependencias...
python -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo  ERRO: Falha ao instalar PyInstaller.
    pause & exit /b 1
)
echo        OK

REM ── Limpar builds anteriores ───────────────────────────────────────────────
echo [2/4] Limpando builds anteriores...
if exist dist\URANNIO.exe       del /f /q dist\URANNIO.exe
if exist dist\URANNIO_Setup_v1.0.exe del /f /q dist\URANNIO_Setup_v1.0.exe
echo        OK

REM ── Build do app principal ─────────────────────────────────────────────────
echo [3/4] Compilando URANNIO.exe...
echo        (pode levar alguns minutos)
echo.
python -m PyInstaller urannio.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo  ERRO ao compilar URANNIO.exe
    pause & exit /b 1
)
echo.
echo        URANNIO.exe gerado com sucesso!
echo.

REM ── Build do instalador ────────────────────────────────────────────────────
echo [4/4] Compilando instalador URANNIO_Setup_v1.0.exe...
echo        (pode levar alguns minutos)
echo.
python -m PyInstaller installer.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo  ERRO ao compilar o instalador
    pause & exit /b 1
)
echo.

REM ── Resultado ──────────────────────────────────────────────────────────────
echo  ============================================
echo   BUILD CONCLUIDO COM SUCESSO!
echo  ============================================
echo.
echo   Arquivo gerado:
echo   dist\URANNIO_Setup_v1.0.exe
echo.
echo   Distribua este unico arquivo para os usuarios.
echo  ============================================
echo.
pause
