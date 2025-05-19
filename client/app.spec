# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files

datas = [
    (os.path.join('embedded_device', 'app_configuration'), 'app_configuration/'),
    (os.path.join('embedded_device', 'multithreading'), 'multithreading/'),
    ("embedded_device/thermal_viewer.qml", ".") 
]

binaries = []
hiddenimports = []

a = Analysis(
    ['embedded_device/app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=['embedded_device.multithreading.producer','embedded_device.multithreading.buffer'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='embedded-device-microservice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
