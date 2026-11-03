# -*- mode: python ; coding: utf-8 -*-
# PyInstaller : pyinstaller packaging/gscolorname.spec --noconfirm
import os, sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"
sys.path.insert(0, ROOT)
from version import __version__ as VERSION  # noqa: E402

datas = [
    (os.path.join(ROOT, "data", "colornames.json"), "data"),
    (os.path.join(ROOT, "data", "LICENSE-color-name-list.txt"), "data"),
    (os.path.join(ROOT, "assets", "gscolorname.png"), "assets"),
    (os.path.join(ROOT, "assets", "gscolorname-512.png"), "assets"),
    (os.path.join(ROOT, "assets", "banner.jpg"), "assets"),
]
if IS_MAC:
    hidden = ["AppKit", "Foundation", "objc"]
elif IS_WIN:
    hidden = []
else:
    hidden = ["jeepney", "jeepney.io.blocking"]

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
    icon=(os.path.join(ROOT, "assets", "gscolorname.ico") if IS_WIN
          else os.path.join(ROOT, "assets", "gscolorname.icns") if IS_MAC else None),
    version=os.path.join(SPECPATH, "windows", "version_info.txt") if IS_WIN else None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=not (IS_WIN or IS_MAC), upx=False, name="gscolorname")

if IS_MAC:
    app = BUNDLE(
        coll,
        name="gsColorName.app",
        icon=os.path.join(ROOT, "assets", "gscolorname.icns"),
        bundle_identifier="ca.gsavard.gscolorname",
        version=VERSION,
        info_plist={
            "CFBundleName": "gsColorName",
            "CFBundleDisplayName": "gsColorName",
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "CFBundleDevelopmentRegion": "fr",
            "LSApplicationCategoryType": "public.app-category.graphics-design",
            "LSMinimumSystemVersion": "11.0",
            "NSHighResolutionCapable": True,
            "NSRequiresAquaSystemAppearance": False,
            "NSHumanReadableCopyright": "© 2026 gsavard — MIT",
        },
    )
