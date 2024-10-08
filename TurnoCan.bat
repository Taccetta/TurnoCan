@echo off
title TurnoCan Open
cd /d %~dp0
call .venv\Scripts\activate
start /wait python main.py
exit