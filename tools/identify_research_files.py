"""
Identify Research Files by Project

Helps identify which project research files in root/research/ belong to
by matching timestamps and content patterns.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TENANT_PROJECTS_ROOT = PROJECT_ROOT / "Tenant_Projects"
ROOT_RESEARCH = PROJECT_ROOT / "research"


def get_project_execution_times() -> Dict[str, List[datetime]]:
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
        
        # Get timestamps from research files in project folder
        timestamps = []
        for file in research_folder.glob("*.json"):
            # Extract timestamp from filename (format: name_YYYYMMDD_HHMMSS.json)
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


def match_research_file_to_project(file_path: Path) -> Optional[str]:
    """Try to match a research file to a project."""
    # Extract timestamp from filename
    match = re.search(r'(\d{8}_\d{6})', file_path.name)
    if not match:
        return None
    
    try:
        file_timestamp = datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
    except ValueError:
        return None
    
    # Get project execution times
    project_times = get_project_execution_times()
    
    # Find project with closest timestamp (within 1 hour)
    best_match = None
    best_diff = None
    
    for project_id, timestamps in project_times.items():
        for ts in timestamps:
            diff = abs((file_timestamp - ts).total_seconds())
            # Match if within 1 hour (3600 seconds)
            if diff < 3600:
                if best_diff is None or diff < best_diff:
                    best_match = project_id
                    best_diff = diff
    
    return best_match


def analyze_research_files():
    """Analyze research files and suggest project matches."""
    if not ROOT_RESEARCH.exists():
        print("No root/research/ folder found.")
        return
    
    research_files = list(ROOT_RESEARCH.glob("*.json"))
    research_files.extend(ROOT_RESEARCH.glob("*.md"))
    
    matches: Dict[str, List[Path]] = {}
    unmatched: List[Path] = []
    
    print(f"Analyzing {len(research_files)} research files...")
    print()
    
    for file_path in research_files:
        project_id = match_research_file_to_project(file_path)
        if project_id:
            if project_id not in matches:
                matches[project_id] = []
            matches[project_id].append(file_path)
        else:
            unmatched.append(file_path)
    
    # Report matches
    if matches:
        print("=" * 80)
        print("FILES MATCHED TO PROJECTS:")
        print("=" * 80)
        for project_id, files in sorted(matches.items()):
            print(f"\nProject: {project_id}")
            print(f"  Files: {len(files)}")
            for file_path in sorted(files)[:10]:
                print(f"    - {file_path.name}")
            if len(files) > 10:
                print(f"    ... and {len(files) - 10} more")
    
    # Report unmatched
    if unmatched:
        print("\n" + "=" * 80)
        print(f"FILES NOT MATCHED ({len(unmatched)} files):")
        print("=" * 80)
        print("\nThese files could not be automatically matched to a project.")
        print("They may be:")
        print("  - From projects that no longer exist")
        print("  - From test runs")
        print("  - System research files")
        print("\nConsider:")
        print("  - Reviewing file timestamps manually")
        print("  - Checking file content for project identifiers")
        print("  - Moving to a 'orphaned_research' folder if not needed")
        print()
        for file_path in sorted(unmatched)[:20]:
            print(f"  - {file_path.name}")
        if len(unmatched) > 20:
            print(f"  ... and {len(unmatched) - 20} more")
    
    # Generate move commands
    if matches:
        print("\n" + "=" * 80)
        print("SUGGESTED MOVE COMMANDS:")
        print("=" * 80)
        print("\n# Run these commands to move matched files:")
        print()
        for project_id, files in sorted(matches.items()):
            project_folder = TENANT_PROJECTS_ROOT / project_id / "research"
            print(f"# Project: {project_id}")
            for file_path in sorted(files):
                target = project_folder / file_path.name
                print(f'move "{file_path}" "{target}"')
            print()


if __name__ == '__main__':
    analyze_research_files()

