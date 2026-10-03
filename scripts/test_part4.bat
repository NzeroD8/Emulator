@echo off
REM Тест: команды этапа 4 (pwd, ls, cd, tree, uptime) на deep_vfs.
python ..\src\emulator.py --vfs-path ..\Vfs\deep_vfs.json --script ..\scripts\startup_part4.txt
