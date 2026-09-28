@echo off
REM Тест: загрузка VFS с несколькими файлами на одном уровне,
REM включая файл с бинарными данными.
python ..\src\emulator.py --vfs-path ..\Vfs\multi_file_vfs.json --script ..\scripts\startup_part3_full.txt
