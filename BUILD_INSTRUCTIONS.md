# Building Windows .exe Installer for TuriX-CUA

This guide explains how to build a Windows executable and installer for TuriX-CUA.

## Prerequisites (on Windows)

1. **Python 3.10 or higher** - Download from https://python.org
2. **Git** (optional, if you want to clone the repo)

## Step 1: Install Dependencies

Open Command Prompt or PowerShell as Administrator and run:

```powershell
# Navigate to your project directory
cd path\to\turix-cua

# Install Python dependencies
pip install -r requirements_windows.txt

# Install PyInstaller
pip install pyinstaller
```

## Step 2: Build the Executable

Run the build script:

```powershell
python build_exe.py
```

This will create:
- `dist/TuriX-CUA/TuriX-CUA.exe` - The main executable
- All required dependencies bundled in the same folder

## Step 3: Test the Executable

Before creating an installer, test the executable:

```powershell
cd dist\TuriX-CUA
.\TuriX-CUA.exe --help
```

Make sure it runs without errors.

## Step 4A: Distribute as Portable App (Simple)

The easiest distribution method is to zip the entire folder:

```powershell
# In the dist directory
Compress-Archive -Path TuriX-CUA -DestinationPath TuriX-CUA-Portable.zip
```

Users can:
1. Extract the zip file
2. Run `TuriX-CUA.exe`
3. Configure `config_windows_openrouter.json` with their API key

## Step 4B: Create Professional Installer (Recommended)

For a proper Windows installer (.exe setup file):

### Option 1: Using Inno Setup (Free)

1. **Download Inno Setup**: https://jrsoftware.org/isdl.php
2. **Install Inno Setup**
3. **Compile the installer**:
   ```powershell
   # Using command line compiler
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```
   
   Or open `installer.iss` in the Inno Setup Compiler GUI and click "Build > Compile"

4. **Find your installer**: `installer_output/TuriX-CUA-Setup.exe`

### Option 2: Using NSIS (Alternative)

1. Download NSIS: https://nsis.sourceforge.io/Download
2. Create an NSIS script (example provided below)
3. Compile with `makensis.exe your_script.nsi`

## Configuration

Users need to configure the application before first use:

1. **Set API Key** (choose one method):
   - Edit `config_windows_openrouter.json` and add your OpenRouter API key
   - Or set environment variable: `set OPENROUTER_API_KEY=your_key_here`

2. **Default Configuration**: The app comes pre-configured for:
   - Provider: OpenRouter
   - Model: Hermes (via OpenRouter)
   - Hotkey: Ctrl+Shift+2

## Troubleshooting

### Build Fails with Import Errors

Make sure all dependencies are installed:
```powershell
pip install -r requirements_windows.txt
pip install pyinstaller
```

### Executable Crashes on Startup

Try running with console output to see errors:
```powershell
# Rebuild with console window
python build_exe.py --console
```

Or edit `build_exe.py` and change `'--windowed'` to remove it temporarily.

### Missing DLL Errors

Some antivirus software may quarantine files. Add an exception or rebuild with:
```powershell
# Add UPX compression exclusion
pyinstaller --upx-exclude "*.dll" ...
```

## Distribution Checklist

- [ ] Test executable on a clean Windows machine (no Python installed)
- [ ] Verify config file is included and editable
- [ ] Test with a valid OpenRouter API key
- [ ] Check that hotkey (Ctrl+Shift+2) works
- [ ] Scan installer with antivirus before distribution
- [ ] Include README with usage instructions

## File Structure After Build

```
dist/
└── TuriX-CUA/
    ├── TuriX-CUA.exe          # Main executable
    ├── config_windows_openrouter.json
    ├── python312.dll          # Python runtime
    ├── pyautogui*.pyd         # Dependencies
    ├── comtypes*.pyd
    └── ... (other bundled files)

installer_output/              # After running Inno Setup
└── TuriX-CUA-Setup.exe        # Professional installer
```

## Notes

- The bundled executable is ~50-100MB (includes Python runtime)
- First launch may take a few seconds
- Antivirus may flag the exe (false positive) - you may need to sign it
- For production, consider code-signing your executable

## Advanced: One-File Executable

To create a single .exe file instead of a folder:

Edit `build_exe.py` and change:
```python
'--onedir',  # Change this line to:
'--onefile',
```

Note: One-file mode is slower to start but easier to distribute.
