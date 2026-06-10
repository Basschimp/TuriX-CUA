"""
Build script for creating Windows .exe installer for TuriX-CUA
Run this script on your Windows machine after installing dependencies.

Usage:
    1. Install Python 3.10+ on Windows
    2. pip install -r requirements_windows.txt
    3. python build_exe.py
    4. Find the installer in dist/ folder
"""

import os
import sys
import shutil
from pathlib import Path

def build_exe():
    print("=" * 60)
    print("Building TuriX-CUA Windows Executable")
    print("=" * 60)
    
    # Check if running on Windows
    if os.name != 'nt':
        print("WARNING: This script should be run on Windows!")
        print("Proceeding anyway, but the output may not work correctly.")
    
    # Import PyInstaller
    try:
        import PyInstaller.__main__
    except ImportError:
        print("PyInstaller not found. Installing...")
        os.system("pip install pyinstaller")
        import PyInstaller.__main__
    
    # Get the project root directory
    project_root = Path(__file__).parent.absolute()
    main_script = project_root / "examples" / "main_win.py"
    
    if not main_script.exists():
        print(f"ERROR: Main script not found at {main_script}")
        return False
    
    # Create output directories
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    print(f"\nBuilding executable from: {main_script}")
    print(f"Output directory: {dist_dir}\n")
    
    # PyInstaller arguments
    args = [
        str(main_script),
        '--name=TuriX-CUA',
        '--onedir',  # Creates a folder with exe and dependencies (more reliable)
        '--windowed',  # No console window
        '--icon=NONE',  # Add your own icon.ico if desired
        '--add-data', f"{project_root}/src/controller;src/controller",
        '--add-data', f"{project_root}/src/windows;src/windows",
        '--add-data', f"{project_root}/examples/config_windows_openrouter.json;.",
        '--hidden-import=pyautogui',
        '--hidden-import=pillow',
        '--hidden-import=comtypes',
        '--hidden-import=ctypes',
        '--clean',
        '--noconfirm',
        f'--distpath={dist_dir}',
        f'--workpath={build_dir}',
    ]
    
    print("Running PyInstaller with options:")
    for arg in args:
        print(f"  {arg}")
    print()
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    # Check if build was successful
    exe_path = dist_dir / "TuriX-CUA" / "TuriX-CUA.exe"
    if exe_path.exists():
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print("=" * 60)
        print(f"\nExecutable location: {exe_path}")
        print(f"\nTo distribute, you can:")
        print(f"  1. Zip the entire 'TuriX-CUA' folder from dist/")
        print(f"  2. Use Inno Setup or NSIS to create a proper installer")
        print(f"\nThe application requires:")
        print(f"  - OpenRouter API key (set in config or environment)")
        print(f"  - Python runtime is NOT required (bundled in exe)")
        print("=" * 60)
        return True
    else:
        print("\nERROR: Build failed! Check the logs above.")
        return False

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)
