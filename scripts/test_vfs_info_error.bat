@echo off
REM Тест: обработка ошибки при вызове vfs-info без указания --vfs-path.
python ..\src\emulator.py --script ..\scripts\startup_vfs_info_error.txt
