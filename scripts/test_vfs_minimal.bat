@echo off
REM Тест: загрузка минимального VFS и проверка vfs-info.
python ..\src\emulator.py --vfs-path ..\Vfs\minimal_vfs.json --script ..\scripts\startup_part3_full.txt
