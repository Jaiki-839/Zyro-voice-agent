"""
zyro_app.pyw -- Windows Windowed (No Console) Entry Point for ZYRO.
Executing this script with pythonw.exe or double-clicking on Windows
runs ZYRO directly with zero command prompt or terminal window.
"""
import os
import sys

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import main

if __name__ == "__main__":
    main()
