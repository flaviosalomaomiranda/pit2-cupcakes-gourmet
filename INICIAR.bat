@echo off
title Doce Nuvem Cupcakes - servidor
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 goto sem_python

if exist ".venv\Scripts\python.exe" goto instalar
echo Criando ambiente virtual - so na primeira vez...
python -m venv .venv
if errorlevel 1 goto erro_venv

:instalar
echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 goto erro_pip

echo.
echo ============================================================
echo  Loja:    http://127.0.0.1:5000
echo  Painel:  http://127.0.0.1:5000/admin   - admin / cupcake123
echo  Para encerrar: feche esta janela.
echo ============================================================
start "" http://127.0.0.1:5000
set HOST=0.0.0.0
".venv\Scripts\python.exe" run.py
echo.
echo O servidor parou. Leia a mensagem acima.
pause
exit /b

:sem_python
echo [ERRO] Python nao encontrado.
echo Instale em https://www.python.org/downloads/ marcando "Add python.exe to PATH" e rode de novo.
pause
exit /b 1

:erro_venv
echo [ERRO] Nao foi possivel criar o ambiente virtual.
pause
exit /b 1

:erro_pip
echo [ERRO] Falha ao instalar dependencias. Verifique a internet.
pause
exit /b 1
