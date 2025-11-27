"""
Automatically move research files to their correct project folders.
"""

import shutil
from pathlib import Path
import re
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TENANT_PROJECTS_ROOT = PROJECT_ROOT / "Tenant_Projects"
ROOT_RESEARCH = PROJECT_ROOT / "research"


def get_project_execution_times():
    """Get execution times for each project from their research folders."""
    projects = {}
    
    if not TENANT_PROJECTS_ROOT.exists():
        return projects
    
    for project_folder in TENANT_PROJECTS_ROOT.iterdir():
        if not project_folder.is_dir():
            continue
        
        project_id = project_folder.name
        research_folder = project_folder / "research"
        
        if not research_folder.exists():
            continue
        
        timestamps = []
        for file in research_folder.glob("*.json"):
            match = re.search(r'(\d{8}_\d{6})', file.name)
            if match:
                try:
                    dt = datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
                    timestamps.append(dt)
                except ValueError:
                    pass
        
        if timestamps:
            projects[project_id] = sorted(timestamps)
    
    return projects


def match_research_file_to_project(file_path):
    """Try to match a research file to a project."""
    match = re.search(r'(\d{8}_\d{6})', file_path.name)
    if not match:
        return None
    
    try:
        file_timestamp = datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
    except ValueError:
        return None
    
    project_times = get_project_execution_times()
    
    best_match = None
    best_diff = None
    
    for project_id, timestamps in project_times.items():
        for ts in timestamps:
            diff = abs((file_timestamp - ts).total_seconds())
            if diff < 3600:  # Within 1 hour
                if best_diff is None or diff < best_diff:
                    best_match = project_id
                    best_diff = diff
    
    return best_match


def main():
    """Move research files to their correct project folders."""
    if not ROOT_RESEARCH.exists():
        print("No root/research/ folder found.")
        return
    
    research_files = list(ROOT_RESEARCH.glob("*.json"))
    research_files.extend(ROOT_RESEARCH.glob("*.md"))
    
    moved = 0
    skipped = 0
    errors = 0
    
    print(f"Moving {len(research_files)} research files...")
    print()
    
    for file_path in research_files:
        project_id = match_research_file_to_project(file_path)
        if not project_id:
            skipped += 1
            continue
        
        project_folder = TENANT_PROJECTS_ROOT / project_id / "research"
        project_folder.mkdir(parents=True, exist_ok=True)
        
        target_path = project_folder / file_path.name
        
        try:
            if target_path.exists():
                # Backup existing file
                backup_path = target_path.with_suffix(target_path.suffix + '.backup')
                shutil.move(str(target_path), str(backup_path))
                print(f"[BACKUP] {file_path.name} -> existing file backed up")
            
            shutil.move(str(file_path), str(target_path))
            print(f"[OK] Moved: {file_path.name} -> {project_id}")
            moved += 1
        except Exception as e:
            print(f"[ERROR] Failed to move {file_path.name}: {e}")
            errors += 1
    
    print()
    print("=" * 80)
    print("MOVEMENT STATISTICS:")
    print(f"  Moved: {moved}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print("=" * 80)


if __name__ == '__main__':
    main()

