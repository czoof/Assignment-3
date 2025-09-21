# YouTube-like Console Simulator

This small Python console app simulates uploading and listing videos (metadata only).

Features

# YouTube-like Simulator (GUI + CLI)

This small project is a compact simulator for uploading and managing video metadata. It provides both a graphical desktop interface (Tkinter) and a command-line interface for scripting and automation.

## Features

- Store video metadata (title, description, uploader, tags, uploaded timestamp)
- Persistent JSON storage (`videos.json`)
- Command-line interface: `upload`, `list`, `view`, `delete`, `search`, `--demo`
- Desktop GUI (Tkinter): form-based upload, search, table listing, view/delete actions

## Prerequisites

- Python 3.8 or newer (3.11 recommended)
- Tkinter (usually included with standard Python on Windows/macOS; on some Linux distributions you may need a separate package)

## Installation

1. Clone or copy the repository to your machine.
2. (Optional) Create and activate a virtual environment:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate
```

3. No external dependencies are required — the app uses Python's standard library.

## Running the application

### GUI mode (recommended for quick use)

```powershell
python .\main.py
```

This opens a window where you can:

- Enter a title, description, uploader and tags to upload a video (title is required).
- Use the search box to filter videos by title, description or tags.
- Select a video from the table and click "View" to see details or "Delete" to remove it.

### Command-line mode

Use the CLI when you want to script interactions or avoid the GUI.

Examples (PowerShell):

```powershell
# Upload a video
python .\main.py upload --title "My Video" --description "A short demo" --uploader alice --tags "demo,example"

# List videos
python .\main.py list

# View details (JSON)
python .\main.py view --id 1

# Delete
python .\main.py delete --id 1

# Search
python .\main.py search --query python

# Run scripted demo (resets `videos.json`)
python .\main.py --demo
```

## Data storage

Videos are saved to `videos.json` in the current working directory. The file contains a JSON array of video objects and is safe to back up or inspect manually.

## Project layout

- `main.py` — application entrypoint with both CLI and GUI implementations
- `README.md` — this file
- `videos.json` — created at runtime when videos are added

## Design notes

- The GUI uses Tkinter for maximum portability without extra dependencies.
- The storage is a human-readable JSON array so you can manually edit or migrate it later.

## Potential improvements

- Add editing of video metadata in the GUI
- Track simulated view count, likes, and comments
- Improve the detail view UI and validation
- Package the app into a single-file executable (PyInstaller)

## Packaging (create an executable)

This project can be packaged into a single-file executable using PyInstaller. A helper PowerShell script `build.ps1` is included to automate the common steps on Windows.

Basic steps (PowerShell):

```powershell
# Ensure execution policy allows running local scripts (run as admin if needed)
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Run the build script (it creates a venv, installs PyInstaller, then builds)
.\build.ps1

# The resulting executable will be in the `dist` folder as `YouTubeSimulator.exe`.
```

Notes:

- The `--windowed` option is used so the packaged app doesn't open a console window. Remove it if you prefer a console build.
- On other platforms (macOS/Linux) use the equivalent PyInstaller commands in a shell environment.
- Building an executable may require additional platform-specific dependencies for Tkinter.

## License

This is a small demo/assignment project. Add a license file if you intend to distribute it publicly.

## Contact / Next steps

If you'd like, I can implement any of the potential improvements above, add tests, or create an executable build.