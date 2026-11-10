@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Calculo Numerico Interativo
where python >nul 2>nul
if errorlevel 1 (
  echo O Python nao esta instalado. Baixe em https://www.python.org/downloads/ e marque "Add python.exe to PATH" na instalacao.
  start https://www.python.org/downloads/
  pause
  exit /b
)
python -c "import streamlit" 2>nul
if errorlevel 1 (
  echo Instalando o Streamlit - so na primeira vez...
  python -m pip install -r requirements.txt
)
echo Abrindo o livro no navegador. NAO feche esta janela enquanto estiver usando o livro.
python -m streamlit run app.py
pause
