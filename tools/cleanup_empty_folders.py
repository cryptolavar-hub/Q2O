"""
Clean up empty folders from root directory.
"""

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

folders_to_check = [
    'src',
    '.coverage_reports'
]

for folder_name in folders_to_check:
    folder_path = PROJECT_ROOT / folder_name
    if folder_path.exists():
        if folder_path.is_dir():
            # Check if folder is empty
            try:
                if not any(folder_path.iterdir()):
                    shutil.rmtree(folder_path)
                    print(f"[OK] Deleted empty folder: {folder_name}")
                else:
                    print(f"[WARNING] Folder {folder_name} is not empty, keeping it")
            except Exception as e:
                print(f"[ERROR] Failed to delete {folder_name}: {e}")
        else:
            print(f"[WARNING] {folder_name} exists but is not a directory")
    else:
        print(f"[INFO] {folder_name} does not exist")

print("\nCleanup complete!")

