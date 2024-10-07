@echo off
title Ejecución de main.py
cd /d %~dp0
call .venv\Scripts\activate
start /wait python main.py
exit