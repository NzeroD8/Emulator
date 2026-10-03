@echo off
REM Тест: команды этапа 5 на глубокой VFS.
python ..\src\emulator.py --vfs-path ..\Vfs\deep_vfs.json --script ..\scripts\startup_part5.txt
