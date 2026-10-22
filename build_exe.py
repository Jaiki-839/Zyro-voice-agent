"""
build_exe.py -- Automated build script for ZYRO Desktop Executable.
Runs PyInstaller using zyro.spec, generates necessary assets, and validates output.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def check_environment() -> None:
    print("[1/4] Checking build environment...")
    # Verify icon exists or generate it
    ico_path = ROOT / "assets" / "zyro.ico"
    if not ico_path.exists():
        print(" -> Generating assets/zyro.ico...")
        from assets.generate_icon import main as gen_icons
        gen_icons()
    else:
        print(" -> Icon assets verified.")

def run_pyinstaller() -> bool:
    print("[2/4] Running PyInstaller build (zyro.spec)...")
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "zyro.spec"]
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print("PyInstaller build failed!")
        return False
    print(" -> PyInstaller completed successfully.")
    return True

def bundle_extra_assets() -> None:
    print("[3/4] Bundling auxiliary distribution files...")
    dist_zyro = ROOT / "dist" / "ZYRO"
    if not dist_zyro.exists():
        print(f"Error: {dist_zyro} does not exist!")
        return

    # Copy .env.example, README.md, docs if present
    for fname in [".env.example", "README.md", "ZYRO_MASTER_PROMPT.md", "launch_zyro.bat", "run_silent.vbs"]:
        src = ROOT / fname
        if src.exists():
            shutil.copy2(src, dist_zyro / fname)
            print(f" -> Copied {fname} to dist/ZYRO/")

    # Copy docs folder if present
    docs_src = ROOT / "docs"
    if docs_src.exists():
        docs_dst = dist_zyro / "docs"
        if docs_dst.exists():
            shutil.rmtree(docs_dst)
        shutil.copytree(docs_src, docs_dst)
        print(" -> Copied documentation suite to dist/ZYRO/docs/")

def verify_output() -> bool:
    print("[4/4] Verifying generated executable...")
    exe_path = ROOT / "dist" / "ZYRO" / "ZYRO.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"SUCCESS: Standalone executable created at:")
        print(f"  {exe_path} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"FAILED: Expected {exe_path} not found.")
        return False

def main() -> int:
    print("==================================================")
    print("      ZYRO Desktop Executable Builder (x64)       ")
    print("==================================================")
    try:
        check_environment()
        if not run_pyinstaller():
            return 1
        bundle_extra_assets()
        if not verify_output():
            return 1
        print("==================================================")
        print("Build Complete! You can now run dist\\ZYRO\\ZYRO.exe")
        print("==================================================")
        return 0
    except Exception as exc:
        print(f"Build failed with exception: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
