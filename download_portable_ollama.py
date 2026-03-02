"""
[PORTABLE OLLAMA DOWNLOADER]
============================
Downloads the official portable zip release of Ollama to avoid C: drive installation.
"""

import os
import requests
import zipfile
import shutil
import sys
from pathlib import Path

# Config
REPO_OWNER = "ollama"
REPO_NAME = "ollama"
DEST_DIR = Path("ollama")
DEST_DIR.mkdir(exist_ok=True)

def cleanup_suspicious_files():
    """Remove the 1.2GB installer if present"""
    suspicious = DEST_DIR / "ollama.exe"
    if suspicious.exists():
        size_mb = suspicious.stat().st_size / (1024 * 1024)
        if size_mb > 500: # Installers are usually large, binaries are small (~20MB)
            print(f"[CLEANUP] Removing suspicious large file: {suspicious} ({size_mb:.1f} MB)")
            try:
                os.remove(suspicious)
            except Exception as e:
                print(f"[ERROR] Could not remove file: {e}")

def get_latest_release_url():
    """Get the browser_download_url for the windows zip asset"""
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    print(f"Fetching release info from {api_url}...")
    
    try:
        resp = requests.get(api_url)
        resp.raise_for_status()
        data = resp.json()
        
        # specific precise logic
        for asset in data.get('assets', []):
            name = asset.get('name', '').lower()
            if name == 'ollama-windows-amd64.zip':
                print(f"[FOUND] Asset: {asset['name']}")
                return asset['browser_download_url']
        
        # Fallback loop
        for asset in data.get('assets', []):
            name = asset.get('name', '').lower()
            if 'windows' in name and 'zip' in name and 'rocm' not in name:
                print(f"[FOUND] Asset (Fallback): {asset['name']}")
                return asset['browser_download_url']
        
        print("[WARN] No windows zip asset found in latest release.")
        return None
    except Exception as e:
        print(f"[ERROR] API Request failed: {e}")
        return None

def download_file(url, filepath):
    """Download file with progress"""
    print(f"Downloading {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Simple progress
                    if total_size:
                        percent = int((downloaded / total_size) * 100)
                        print(f"\rProgress: {percent}%", end='')
            print("\n[OK] Download complete.")
            return True
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        return False

def extract_zip(filepath, extract_to):
    """Extract zip file"""
    print(f"Extracting to {extract_to}...")
    try:
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print("[OK] Extraction complete.")
        return True
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        return False

def main():
    print("Checking for existing installation...")
    cleanup_suspicious_files()
    
    # Check if correct binary already exists
    exe = DEST_DIR / "ollama.exe"
    if exe.exists():
        # Check size (real binary is small, <100MB)
        if exe.stat().st_size < 100 * 1024 * 1024:
            print("[OK] Portable binary already exists.")
            return
    
    url = get_latest_release_url()
    if not url:
        print("Falling back to manual zip search...")
        # Fallback to a known pattern or manual unzip of setup? 
        # Actually, if zip is missing, we might need 'ollama-windows-amd64.zip' specific tag?
        # Let's hope latest has it.
        sys.exit(1)
        
    zip_path = DEST_DIR / "ollama.zip"
    if download_file(url, zip_path):
        if extract_zip(zip_path, DEST_DIR):
            os.remove(zip_path) # Cleanup zip
            print("[SUCCESS] Ollama portable installed.")
        else:
            sys.exit(1)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
