"""
[C: DRIVE CLEANUP CHECK]
========================
Checks for and removes any AI Assistant related files from C: drive.
Targeting Ollama default installations and caches.
"""
import os
import shutil
from pathlib import Path

def check_and_clean():
    user_profile = Path(os.environ['USERPROFILE'])
    local_appdata = Path(os.environ['LOCALAPPDATA'])
    
    # List of paths to check
    targets = [
        # Ollama Installation
        local_appdata / "Programs" / "Ollama",
        # Ollama Models & Config
        user_profile / ".ollama",
        # Pip Cache (If you want to be strictly clean, though this is shared)
        # local_appdata / "pip" / "Cache"  <-- unsafe to delete generally, but user asked?
        # Let's stick to Ollama first as that's the main concern.
        
        # HuggingFace Cache (often default location)
        user_profile / ".cache" / "huggingface"
    ]

    print(f"Checking C: Drive locations for AI files...\n")
    
    found_any = False
    
    for target in targets:
        if target.exists():
            found_any = True
            size_mb = 0
            try:
                size_mb = sum(f.stat().st_size for f in target.rglob('*') if f.is_file()) / (1024*1024)
            except:
                pass
            
            print(f"[FOUND] {target} ({size_mb:.2f} MB)")
            
            try:
                print(f"   -> Deleting...")
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    os.remove(target)
                print("   -> [DELETED]")
            except Exception as e:
                print(f"   -> [ERROR] Could not delete: {e}")
        else:
            print(f"[CLEAN] {target} not found.")

    if not found_any:
        print("\n[SUCCESS] C: Drive is clean. No AI files found in default locations.")
    else:
        print("\n[DONE] Cleanup finished.")

if __name__ == "__main__":
    check_and_clean()
