# -*- mode: python ; coding: utf-8 -*-
# PyInstaller : pyinstaller packaging/gscolorname.spec --noconfirm
import os, sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
IS_WIN = sys.platform.startswith("win")

datas = [
    (os.path.join(ROOT, "data", "colornames.json"), "data"),
    (os.path.join(ROOT, "data", "LICENSE-color-name-list.txt"), "data"),
    (os.path.join(ROOT, "assets", "gscolorname.png"), "assets"),
    (os.path.join(ROOT, "assets", "gscolorname-512.png"), "assets"),
    (os.path.join(ROOT, "assets", "banner.jpg"), "assets"),
]
hidden = ["jeepney", "jeepney.io.blocking"] if not IS_WIN else []

# modules Qt inutiles (réduit fortement la taille)
excludes = [
    "tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets", "PySide6.Qt3DCore", "PySide6.Qt3DRender",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtBluetooth",
    "PySide6.QtPositioning", "PySide6.QtLocation", "PySide6.QtSensors", "PySide6.QtSerialPort",
    "PySide6.QtWebSockets", "PySide6.QtWebChannel", "PySide6.QtDesigner", "PySide6.QtHelp",
    "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets", "PySide6.QtNetwork", "PySide6.QtXml",
]

a = Analysis(
    [os.path.join(ROOT, "gscolorname.py")],
    pathex=[ROOT],
    datas=datas,
    hiddenimports=hidden,
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="gscolorname",
    console=False,
    icon=os.path.join(ROOT, "assets", "gscolorname.ico") if IS_WIN else None,
    version=os.path.join(SPECPATH, "windows", "version_info.txt") if IS_WIN else None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=not IS_WIN, upx=False, name="gscolorname")
