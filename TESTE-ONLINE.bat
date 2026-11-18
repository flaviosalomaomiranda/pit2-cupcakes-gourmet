@echo off
chcp 65001 >nul
title Doce Nuvem - link publico temporario
cd /d "%~dp0"
echo Este arquivo cria um LINK PUBLICO TEMPORARIO para outras pessoas testarem pela internet.
echo O link funciona enquanto o computador e estas janelas estiverem abertos.
echo.
if not exist "cloudflared.exe" (
  echo Baixando cloudflared (ferramenta gratuita da Cloudflare, so na primeira vez)...
  curl -L -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
  if errorlevel 1 (
    echo [ERRO] Nao consegui baixar o cloudflared. Verifique a internet.
    pause
    exit /b 1
  )
)
echo Iniciando a loja em outra janela...
start "Doce Nuvem - servidor" cmd /c INICIAR.bat
timeout /t 25 /nobreak >nul
echo.
echo ================================================================
echo  Procure abaixo uma linha com  https://....trycloudflare.com
echo  ESSE e o link para mandar aos testadores (WhatsApp).
echo  Painel do lojista: o mesmo link + /admin   (admin / cupcake123)
echo ================================================================
echo.
cloudflared.exe tunnel --url http://127.0.0.1:5000
pause
