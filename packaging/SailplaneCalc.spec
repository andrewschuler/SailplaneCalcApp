# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for SailplaneCalc. Build with (from the repo root):

    pyinstaller packaging/SailplaneCalc.spec

Produces a windowed, onedir build: dist/SailplaneCalc/ on Windows and Linux, and a real
double-clickable dist/SailplaneCalc.app bundle on macOS.

Paths below are built from SPECPATH (the absolute directory containing this file, provided by
PyInstaller) rather than relative strings, so the build works identically whether invoked from
the repo root (`pyinstaller packaging/SailplaneCalc.spec`, what CI does) or from inside
packaging/ (`pyinstaller SailplaneCalc.spec`).
"""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
ENTRY_POINT = os.path.join(REPO_ROOT, "run_app.py")

a = Analysis(
    [ENTRY_POINT],
    pathex=[REPO_ROOT],
    binaries=[],
    # No `datas` entries needed: the app has zero external runtime assets (no fonts, images,
    # or data files loaded at runtime -- all UI content is inline Python, see docs/Manual.html).
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SailplaneCalc",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # windowed: no console window on launch
    icon=os.path.join(REPO_ROOT, "assets", "icon.ico"),  # ignored (harmlessly) on Linux
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SailplaneCalc",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="SailplaneCalc.app",
        icon=os.path.join(REPO_ROOT, "assets", "icon.icns"),
        bundle_identifier=None,
    )
