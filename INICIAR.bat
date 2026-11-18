@echo off
chcp 65001 >nul
title Doce Nuvem Cupcakes - servidor
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python nao encontrado. Instale em https://www.python.org/downloads/ marcando "Add python.exe to PATH".
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual (so na primeira vez)...
  python -m venv .venv
)
echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo [ERRO] Falha ao instalar dependencias. Verifique a internet.
  pause
  exit /b 1
)
echo.
echo ============================================================
echo  Loja:    http://127.0.0.1:5000
echo  Painel:  http://127.0.0.1:5000/admin   (admin / cupcake123)
echo  Celular na mesma rede Wi-Fi: http://SEU-IP:5000  (veja o IP com o comando ipconfig)
echo  Para encerrar: feche esta janela.
echo ============================================================
start "" http://127.0.0.1:5000
set HOST=0.0.0.0
".venv\Scripts\python.exe" run.py
pause
