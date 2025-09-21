<#
Simple build helper to create a single-file executable using PyInstaller.

Usage (PowerShell):
.\build.ps1

#>
param()

Set-StrictMode -Version Latest

Write-Host "Creating virtual environment .venv (if missing)..."
if (-not (Test-Path -Path .venv)) {
    python -m venv .venv
}

Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate

Write-Host "Installing PyInstaller..."
pip install --upgrade pip
pip install pyinstaller

Write-Host "Building single-file executable (windowed)..."
pyinstaller --onefile --windowed --name YouTubeSimulator main.py

Write-Host "Build complete. Output in 'dist' folder."
Write-Host "If you need a console-focused build, remove the --windowed flag."
