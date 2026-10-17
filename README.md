# Hearth POS

A Windows desktop restaurant point-of-sale application built with PySide6 and SQLAlchemy.

## Run from source

```bat
run_pos.bat
```

The first run initializes the SQLite database and idempotently seeds the starter staff and menu data.

## Build a Windows executable

From the project root, with `.venv` activated:

```bat
scripts\build_windows.bat
```

The distributable is produced at `dist\HearthPOS\HearthPOS.exe`. The executable keeps its data directory beside the application when packaged.

## Verification

```bat
set QT_QPA_PLATFORM=offscreen
.venv\Scripts\python.exe -m pytest -q
```
