"""
[COLLEGE AI CLEANUP]
=====================
This script organizes the folder into a professional structure.
Moves all documentation, scripts, and logs into dedicated folders.
"""
import os
import shutil
from pathlib import Path

BASE = Path(os.getcwd())

# Define Folder Structure
FOLDERS = {
    "docs": [
        "*.md", "*.txt", "ARCHITECTURE.txt", "ROADMAP.md", "README.md",
        "This file will be moved too? No, keep README in root."
    ],
    "scripts": [
        "*.bat", "*.ps1", "*.py"
    ],
    "config": [],
    "logs": []
}

# EXEMPTIONS (Files to keep in ROOT)
KEEP_IN_ROOT = [
    "START_COLLEGE_AI.bat",
    "README.md",
    "server.py",
    "setup_college.py",
    "download_portable_ollama.py",
    "organize_neat.py",
    "requirements.txt"
]

def organize():
    # 1. Create 'docs' folder
    docs_dir = BASE / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # 2. Create 'scripts_archive' for old scripts
    scripts_archive = BASE / "archive"
    scripts_archive.mkdir(exist_ok=True)

    # 3. Move Markdown/Text files to docs (except README)
    print("Organizing Documentation...")
    for ext in ["*.md", "*.txt"]:
        for f in BASE.glob(ext):
            if f.name not in KEEP_IN_ROOT:
                try:
                    shutil.move(str(f), str(docs_dir / f.name))
                    print(f"Moved {f.name} -> docs/")
                except Exception as e:
                    print(f"Skipped {f.name}: {e}")

    # 4. Move Old Scripts to archive
    print("Archiving Old Scripts...")
    for ext in ["*.bat", "*.ps1", "*.py"]:
        for f in BASE.glob(ext):
            if f.name not in KEEP_IN_ROOT:
                try:
                    shutil.move(str(f), str(scripts_archive / f.name))
                    print(f"Moved {f.name} -> archive/")
                except Exception as e:
                    print(f"Skipped {f.name}: {e}")

    # 5. Remove Empty Folders
    for d in BASE.iterdir():
        if d.is_dir():
            try:
                d.rmdir() # Only works if empty
                print(f"Removed empty folder: {d.name}")
            except:
                pass

    print("\n[ORGANIZATION COMPLETE]")
    print("Your folder is now clean. Documents are in 'docs', old scripts in 'archive'.")

if __name__ == "__main__":
    organize()
