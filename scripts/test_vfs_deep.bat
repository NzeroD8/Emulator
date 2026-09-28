@echo off
REM Тест: загрузка VFS с глубокой вложенностью.
python ..\src\emulator.py --vfs-path ..\Vfs\deep_vfs.json --script ..\scripts\startup_part3_full.txt
