"""
installer/build_installer_exe.py -- Compiles the graphical installer into a single-file
Windows Setup Executable: dist/ZYRO_Setup_v1.0.0.exe
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def build_setup_exe() -> None:
    print("==================================================")
    print(" Compiling Standalone Windows Installer (.exe)   ")
    print("==================================================")
    
    installer_script = ROOT / "installer" / "setup_zyro.py"
    icon_path = ROOT / "assets" / "zyro.ico"
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--noconsole",
        f"--icon={str(icon_path)}",
        "--name=ZYRO_Setup_v1.0.0",
        f"--add-data={str(ROOT / 'assets')};assets",
        f"--add-data={str(ROOT / 'dist' / 'ZYRO_v1.0.0_Windows_x64_Portable.zip')};dist",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build" / "installer"),
        "--specpath", str(ROOT / "build" / "installer"),
        str(installer_script),
        "--noconfirm",
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(ROOT))
    if res.returncode == 0:
        exe_path = ROOT / "dist" / "ZYRO_Setup_v1.0.0.exe"
        if exe_path.exists():
            mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"SUCCESS: Single-File Setup Executable created:")
            print(f" -> {exe_path} ({mb:.2f} MB)")
    else:
        print("Installer compilation failed.")

if __name__ == "__main__":
    build_setup_exe()
