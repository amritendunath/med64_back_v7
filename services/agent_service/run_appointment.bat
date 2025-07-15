@echo off
chcp 65001
cd /d "%~dp0src"
python main.py --port=8000
