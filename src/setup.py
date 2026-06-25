import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine-tuning.
build_exe_options = {
    "packages": ["os", "sys", "PyQt5", "qrcode", "asyncio", "aiohttp", "aiortc", "ctypes", "pyperclip"],
    "excludes": [],
    "include_files": [
        ("icon.ico", "icon.ico"),
        ("main.png", "main.png"),
        ("loading.gif", "loading.gif"),
    ],
    "include_msvcr": True,
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="TransferX",
    version="1.0",
    description="P2P File Sharing Application",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "transferx.py", 
            base=base, 
            icon="icon.ico",
            target_name="TransferX.exe",
        )
    ],
)