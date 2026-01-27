@echo off
setlocal enabledelayedexpansion
title Snapshot do Projeto

echo.
echo ==== INICIANDO SNAPSHOT ====
echo.

REM ====== DESTINO DOS SNAPSHOTS ======
set "DESTINO=C:\Users\Fabiano\Documents\Snapshots PINHALJUNIOR"

echo Pasta atual (projeto): "%CD%"
echo Destino snapshots:     "%DESTINO%"
echo.

REM ====== CRIA A PASTA DESTINO SE NAO EXISTIR ======
if not exist "%DESTINO%\" (
  echo Criando pasta: "%DESTINO%"
  mkdir "%DESTINO%" 2>nul
)

if not exist "%DESTINO%\" (
  echo ❌ ERRO: nao consegui criar/acessar "%DESTINO%".
  goto FIM
)

REM ====== NOME DO PROJETO (nome da pasta atual) ======
for %%I in ("%CD%") do set "PROJETO=%%~nxI"

REM ====== DATA/HORA ======
for /f %%A in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HHmm"') do set "DATAHORA=%%A"

REM ====== ARQUIVO ZIP ======
set "ZIP=%DESTINO%\%PROJETO%_%DATAHORA%.zip"

echo.
echo ================================
echo  Projeto: %PROJETO%
echo  Origem:  %CD%
echo  Zip:     %ZIP%
echo ================================
echo.

REM ====== CRIA O ZIP ======
powershell -NoProfile -ExecutionPolicy Bypass ^
  "Compress-Archive -Path '%CD%\*' -DestinationPath '%ZIP%' -Force" 2>&1

echo.
if exist "%ZIP%" (
  echo ✅ Snapshot criado com sucesso!
) else (
  echo ❌ Falhou ao criar o snapshot.
)

:FIM
echo.
echo ==== FIM ====
echo.
pause
endlocal
