# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Collect all necessary data for PyQt5
datas = [
    ('D:\\TransferX\\icon.ico', '.'),
    ('D:\\TransferX\\main.png', '.'),
    ('D:\\TransferX\\loading.gif', '.'),
    ('D:\\TransferX\\qrcode.png', '.')
]
binaries = []
hiddenimports = []

# Collect all for PyQt5
tmp_ret = collect_all('PyQt5')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Add other specific imports
hiddenimports += [
    'pyperclip',
    'qrcode',
    'aiohttp',
    'aiortc',
    'asyncio',
    'ctypes',
    'aiohttp.client',
    'aiohttp.client_reqrep',
    'aiohttp.helpers',
    'aiortc.sdp',
    'aiortc.rtcpeerconnection'
]

# Collect all submodules for problematic packages
hiddenimports += collect_submodules('aiohttp')
hiddenimports += collect_submodules('aiortc')

a = Analysis(
    ['transferx.py'],
    pathex=['D:\\TransferX'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TransferX',
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
    icon='D:\\TransferX\\icon.ico'
)