# ClipboardPro

A powerful clipboard manager built with PyQt6 that tracks your clipboard history and provides easy access to previously copied content.

## Features

- 📋 **Clipboard History**: Automatically tracks and stores your clipboard history
- 🖼️ **Image Support**: Handles both text and image clipboard content
- 🔍 **Search**: Quickly find items in your clipboard history
- 🖥️ **System Tray**: Runs in the background with system tray integration
- 💾 **Persistent Storage**: Saves clipboard history across sessions
- 🎨 **Clean UI**: Modern and intuitive user interface

## Requirements

- Python 3.7+
- PyQt6
- macOS (primary target platform)

## Installation

### Quick Setup (Recommended)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd free-clipboard-tool
   ```

2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   This will:
   - Create a virtual environment (`.venv`)
   - Install Python dependencies (PyQt6)
   - Set up the project for development

### Manual Installation

If you prefer to set up manually:

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install PyQt6
   ```

## Starting the Application

### Development Mode

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

2. Run the application:
   ```bash
   python main.py
   ```

The application will start and appear in your system tray. Click the tray icon to access your clipboard history.

## Building the Application

### Create Standalone Executable

To build a standalone executable that can run without Python installed:

1. Make sure you're in the activated virtual environment:
   ```bash
   source .venv/bin/activate
   ```

2. Run the build script:
   ```bash
   chmod +x build.sh
   ./build.sh
   ```

   This will:
   - Install PyInstaller if needed
   - Create a single executable file using PyInstaller
   - Generate the app in the `dist/` directory

3. The built application will be available at:
   ```
   dist/ClipboardPro
   ```

### Manual Build (Alternative)

You can also build manually using the PyInstaller spec file:

```bash
pyinstaller ClipboardPro.spec
```

## Project Structure

```
free-clipboard-tool/
├── main.py           # Main application entry point
├── build.sh          # Build script for creating executable
├── setup.sh          # Setup script for development environment
├── ClipboardPro.spec # PyInstaller specification file
├── .venv/            # Virtual environment (created by setup)
├── build/            # Build artifacts (generated)
├── dist/             # Distribution files (generated)
└── .images/          # Temporary image storage (generated)
```

## Usage

1. **Starting**: Launch the application and it will run in your system tray
2. **Accessing History**: Click the tray icon to view your clipboard history
3. **Selecting Items**: Click on any item in the history to copy it back to your clipboard
4. **Search**: Use the search field to quickly find specific clipboard content
5. **Images**: The app automatically handles both text and image clipboard content

## Development

- The application uses PyQt6 for the GUI framework
- Clipboard monitoring runs automatically in the background
- Images are temporarily stored in `.images/` directory
- Maximum history is limited to 50 items for performance

## Troubleshooting

- **Permission Issues**: Make sure the app has accessibility permissions on macOS
- **Virtual Environment**: Always activate the virtual environment before running or building
- **Dependencies**: If you encounter import errors, reinstall dependencies with `pip install PyQt6`
