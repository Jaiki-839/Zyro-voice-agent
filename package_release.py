"""
package_release.py -- Bundles portable ZIP release package for ZYRO.
"""
from __future__ import annotations

import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def package_zip() -> Path:
    dist_dir = ROOT / "dist" / "ZYRO"
    if not dist_dir.exists():
        raise FileNotFoundError(f"{dist_dir} does not exist. Run build_exe.py first.")

    out_zip = ROOT / "dist" / "ZYRO_v1.0.0_Windows_x64_Portable.zip"
    print(f"Creating portable zip: {out_zip}...")
    
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dist_dir):
            for file in files:
                p = Path(root) / file
                arcname = Path("ZYRO") / p.relative_to(dist_dir)
                zf.write(p, arcname)

    size_mb = out_zip.stat().st_size / (1024 * 1024)
    print(f"Portable release package created successfully: {out_zip} ({size_mb:.2f} MB)")
    return out_zip

if __name__ == "__main__":
    try:
        package_zip()
    except Exception as exc:
        print(f"Packaging error: {exc}")
        sys.exit(1)
