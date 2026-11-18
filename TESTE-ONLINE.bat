@echo off
title Doce Nuvem - link publico temporario
cd /d "%~dp0"
echo Este arquivo cria um LINK PUBLICO TEMPORARIO para outras pessoas testarem pela internet.
echo O link funciona enquanto o computador e estas janelas estiverem abertos.
echo.
if exist "cloudflared.exe" goto iniciar
echo Baixando cloudflared - ferramenta gratuita da Cloudflare, so na primeira vez...
curl -L -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
if errorlevel 1 goto erro_download

:iniciar
echo Iniciando a loja em outra janela...
start "Doce Nuvem - servidor" cmd /k INICIAR.bat
echo Aguardando a loja ligar - 30 segundos...
timeout /t 30 /nobreak >nul
echo.
echo ================================================================
echo  Procure abaixo uma linha com  https://....trycloudflare.com
echo  ESSE e o link para mandar aos testadores pelo WhatsApp.
echo  Painel do lojista: o mesmo link + /admin  - admin / cupcake123
echo ================================================================
echo.
cloudflared.exe tunnel --url http://127.0.0.1:5000
echo.
echo O tunel parou. Leia a mensagem acima.
pause
exit /b

:erro_download
echo [ERRO] Nao consegui baixar o cloudflared. Verifique a internet.
pause
exit /b 1
