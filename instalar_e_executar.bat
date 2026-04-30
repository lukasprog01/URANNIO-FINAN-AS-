@echo off
title Controle Financeiro - Instalação e Execução
color 0A

echo ==========================================
echo   CONTROLE FINANCEIRO - Configuração
echo ==========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não encontrado!
    echo Baixe em: https://www.python.org/downloads/
    echo Marque a opção "Add Python to PATH" ao instalar.
    pause
    exit /b 1
)

echo [OK] Python encontrado
python --version

echo.
echo Instalando dependências...
echo.

python -m pip install --upgrade pip
python -m pip install PyQt6 matplotlib

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar dependências.
    echo Tente executar como Administrador.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   Iniciando Controle Financeiro...
echo ==========================================
echo.

python main.py

pause
