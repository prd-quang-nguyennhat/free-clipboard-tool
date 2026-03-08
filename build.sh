#!/bin/bash

# 1. Install PyInstaller if you don't have it
echo "Checking for PyInstaller..."
pip install pyinstaller

# 2. Define script name (change this if your file is named differently)
SCRIPT_NAME="main.py"
APP_NAME="ClipboardPro"

echo "Building $APP_NAME..."

# 3. Run PyInstaller
# --noconsole: Prevents a terminal window from popping up
# --onefile: Bundles everything into one executable
# --windowed: Standard for macOS GUI apps
# --clean: Cleans cache before building
pyinstaller --noconsole --onefile --windowed \
    --name "$APP_NAME" \
    --clean \
    "$SCRIPT_NAME"

echo "------------------------------------------------"
echo "Build Complete!"
echo "Your app is located in: ./dist/$APP_NAME.app"
echo "You can now move it to your Applications folder."
echo "------------------------------------------------"