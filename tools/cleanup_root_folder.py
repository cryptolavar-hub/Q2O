"""
Root Folder Cleanup Script

Identifies project-generated files in the root folder and moves them to their
correct Tenant_Projects/{project_id}/ folders.

This script helps clean up files that were incorrectly saved to the root folder
due to the backup agents workspace_path bug (now fixed).
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TENANT_PROJECTS_ROOT = PROJECT_ROOT / "Tenant_Projects"

# System folders/files that should stay in root
SYSTEM_FOLDERS = {
    'addon_portal',
    'agents',
    'api',  # Note: This might have project files mixed in
    'config',
    'docs',
    'demos',
    'infra',
    'k8s',
    'logs',
    'mobile',
    'research',  # Note: This might have project files mixed in
    'shared',
    'src',  # Note: This might have project files mixed in
    'templates',
    'tests',  # Note: This might have project files mixed in
    'test_workspace',
    'tools',
    'utils',
    'web',
    'zbin',
    '.github',
    '.git',
    '__pycache__',
    'node_modules',
    'venv',
    '.venv',
}

# System files that should stay in root
SYSTEM_FILES = {
    'main.py',
    'README.md',
    'requirements.txt',
    'config_example.json',
    'config.json',
    'test_config.json',
    'test_agent_system.py',
    'test_agents.py',
    'test_database_connection.py',
    'test_duckduckgo_search.py',
    'test_python313_full_compatibility.py',
    'test_research_agent_llm.py',
    'test_researcher.json',
    'test_small.json',
    'test_task_tracking.py',
    'quick_test.py',
    'check_database_schema.py',
    'check_databases.py',
    'check_tenant_sessions_schema.py',
    'create_database.py',
    'fix_db_dsn.py',
    'update_db_dsn_to_q2o.py',
    'update_password_in_env.py',
    'env.example',
    'env.llm.example.txt',
    '.env',
    '.gitignore',
    'learned_templates.db',
    'q2o_licensing.db',
    '.llm_cost_state.json',
}


def get_project_folders() -> Dict[str, Path]:
    """Get all project folders from Tenant_Projects."""
    projects = {}
    if TENANT_PROJECTS_ROOT.exists():
        for folder in TENANT_PROJECTS_ROOT.iterdir():
            if folder.is_dir() and not folder.name.startswith('.'):
                projects[folder.name] = folder
    return projects


def analyze_file(file_path: Path) -> Optional[str]:
    """
    Analyze a file to determine which project it belongs to.
    
    Returns:
        project_id if file belongs to a project, None if it's a system file
    """
    # Skip system files
    if file_path.name in SYSTEM_FILES:
        return None
    
    # Skip files in system folders
    if file_path.parent.name in SYSTEM_FOLDERS:
        # But check if it's a project file that ended up in a system folder
        # (e.g., research files in root/research/)
        if file_path.parent.name in ['research', 'tests', 'api', 'src']:
            # These folders might have project files mixed in
            # We'll analyze them separately
            pass
        else:
            return None
    
    # Check file content for project identifiers
    project_id = None
    
    # Strategy 1: Check if file path contains project-like patterns
    # Look for files that match project naming patterns
    file_name = file_path.name.lower()
    
    # Strategy 2: Check file content for project references
    if file_path.suffix in ['.py', '.json', '.md', '.tsx', '.ts', '.js']:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(5000)  # Read first 5KB
                
                # Look for project IDs in content
                # Common patterns: project_id, project-id, projectId
                patterns = [
                    r'project[_-]?id["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'projectId["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'project_id["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        potential_id = match.group(1)
                        # Check if this matches a known project folder
                        projects = get_project_folders()
                        if potential_id in projects:
                            return potential_id
        except Exception:
            pass
    
    # Strategy 3: Check filename patterns
    # Files that look like they're from a specific project
    # (e.g., test_*, api/app/*, src/*)
    if file_path.parent.name in ['research', 'tests', 'api', 'src']:
        # These might be project files - we'll need to match by timestamp or content
        # For now, we'll flag them for manual review
        return "NEEDS_REVIEW"
    
    return None


def find_project_files_in_root() -> List[Tuple[Path, Optional[str], str]]:
    """
    Find files in root that look like they belong to projects.
    
    Returns:
        List of (file_path, project_id, reason) tuples
    """
    root = PROJECT_ROOT
    project_files = []
    projects = get_project_folders()
    
    # Check root-level files
    for item in root.iterdir():
        if item.is_file():
            # Skip system files
            if item.name in SYSTEM_FILES:
                continue
            
            # Check if it's a project file
            project_id = analyze_file(item)
            if project_id:
                reason = "Root-level file that appears to be project-generated"
                project_files.append((item, project_id, reason))
    
    # Check problematic folders (research, tests, api, src)
    problematic_folders = ['research', 'tests', 'api', 'src']
    
    for folder_name in problematic_folders:
        folder_path = root / folder_name
        if not folder_path.exists() or not folder_path.is_dir():
            continue
        
        # Skip if it's a system folder (like agents/api/)
        if folder_path.parent.name in SYSTEM_FOLDERS and folder_path.parent.name != root.name:
            continue
        
        # Check files in this folder
        for file_path in folder_path.rglob('*'):
            if file_path.is_file():
                # Skip hidden files and common system files
                if file_path.name.startswith('.') or file_path.name in ['__init__.py', '__pycache__']:
                    continue
                
                # Try to match file to a project
                project_id = None
                
                # Check if file exists in any project folder
                for proj_id, proj_folder in projects.items():
                    relative_path = file_path.relative_to(root)
                    potential_target = proj_folder / relative_path
                    
                    # If file exists in project folder, this root file is a duplicate
                    if potential_target.exists():
                        project_id = proj_id
                        reason = f"Duplicate file - exists in {proj_id}"
                        break
                    
                    # Check if similar file exists (same name, different location)
                    if file_path.name in [f.name for f in proj_folder.rglob(file_path.name)]:
                        project_id = proj_id
                        reason = f"Similar file exists in {proj_id}"
                        break
                
                if project_id:
                    project_files.append((file_path, project_id, reason))
                elif project_id is None and folder_name in problematic_folders:
                    # Flag for review
                    project_files.append((file_path, "NEEDS_REVIEW", f"File in {folder_name}/ that may belong to a project"))
    
    return project_files


def generate_report(project_files: List[Tuple[Path, Optional[str], str]], dry_run: bool = True) -> str:
    """Generate a cleanup report."""
    report_lines = [
        "=" * 80,
        "ROOT FOLDER CLEANUP REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Mode: {'DRY RUN' if dry_run else 'LIVE'}",
        "=" * 80,
        "",
    ]
    
    if not project_files:
        report_lines.append("✓ No project files found in root folder.")
        report_lines.append("Root folder appears clean.")
        return "\n".join(report_lines)
    
    # Group by project
    by_project: Dict[str, List[Tuple[Path, str]]] = {}
    needs_review: List[Tuple[Path, str]] = []
    
    for file_path, project_id, reason in project_files:
        if project_id == "NEEDS_REVIEW":
            needs_review.append((file_path, reason))
        else:
            if project_id not in by_project:
                by_project[project_id] = []
            by_project[project_id].append((file_path, reason))
    
    # Report by project
    if by_project:
        report_lines.append(f"FILES TO MOVE ({len(sum(by_project.values(), []))} files):")
        report_lines.append("")
        
        for project_id, files in sorted(by_project.items()):
            report_lines.append(f"  Project: {project_id}")
            report_lines.append(f"  Files: {len(files)}")
            for file_path, reason in files[:10]:  # Show first 10
                rel_path = file_path.relative_to(PROJECT_ROOT)
                report_lines.append(f"    - {rel_path}")
                report_lines.append(f"      Reason: {reason}")
            if len(files) > 10:
                report_lines.append(f"    ... and {len(files) - 10} more files")
            report_lines.append("")
    
    # Report files needing review
    if needs_review:
        report_lines.append(f"FILES NEEDING MANUAL REVIEW ({len(needs_review)} files):")
        report_lines.append("")
        for file_path, reason in needs_review[:20]:  # Show first 20
            rel_path = file_path.relative_to(PROJECT_ROOT)
            report_lines.append(f"  - {rel_path}")
            report_lines.append(f"    Reason: {reason}")
        if len(needs_review) > 20:
            report_lines.append(f"  ... and {len(needs_review) - 20} more files")
        report_lines.append("")
    
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)


def move_files(project_files: List[Tuple[Path, Optional[str], str]], dry_run: bool = True) -> Dict[str, int]:
    """
    Move files to their correct project folders.
    
    Returns:
        Dictionary with move statistics
    """
    stats = {
        'moved': 0,
        'skipped': 0,
        'errors': 0,
        'needs_review': 0
    }
    
    projects = get_project_folders()
    
    for file_path, project_id, reason in project_files:
        if project_id == "NEEDS_REVIEW":
            stats['needs_review'] += 1
            continue
        
        if project_id not in projects:
            stats['skipped'] += 1
            print(f"[WARNING] Skipping {file_path.name}: Project {project_id} not found")
            continue
        
        project_folder = projects[project_id]
        
        # Determine target path
        # Try to preserve relative structure
        if file_path.parent.name in ['research', 'tests', 'api', 'src']:
            # Preserve folder structure
            relative_path = file_path.relative_to(PROJECT_ROOT)
            target_path = project_folder / relative_path
        else:
            # Root-level file - put in appropriate folder based on type
            if file_path.suffix == '.py':
                # Python file - check if it's a test
                if 'test' in file_path.name.lower():
                    target_path = project_folder / 'tests' / file_path.name
                else:
                    target_path = project_folder / 'src' / file_path.name
            elif file_path.suffix in ['.json', '.md']:
                # Check if it's research
                if 'research' in file_path.name.lower() or file_path.parent.name == 'research':
                    target_path = project_folder / 'research' / file_path.name
                else:
                    target_path = project_folder / file_path.name
            else:
                target_path = project_folder / file_path.name
        
        # Create target directory if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        if dry_run:
            print(f"[DRY RUN] Would move: {file_path.name}")
            print(f"          From: {file_path.relative_to(PROJECT_ROOT)}")
            print(f"          To:   {target_path.relative_to(PROJECT_ROOT)}")
            stats['moved'] += 1
        else:
            try:
                # Check if target already exists
                if target_path.exists():
                    # Compare file sizes/dates to decide
                    if file_path.stat().st_mtime > target_path.stat().st_mtime:
                        # Root file is newer - backup old and move
                        backup_path = target_path.with_suffix(target_path.suffix + '.backup')
                        shutil.move(str(target_path), str(backup_path))
                        print(f"[WARNING] Backed up existing: {backup_path.name}")
                    
                    shutil.move(str(file_path), str(target_path))
                    print(f"[OK] Moved (replaced): {file_path.name}")
                else:
                    shutil.move(str(file_path), str(target_path))
                    print(f"[OK] Moved: {file_path.name}")
                stats['moved'] += 1
            except Exception as e:
                print(f"[ERROR] Error moving {file_path.name}: {e}")
                stats['errors'] += 1
    
    return stats


def main():
    """Main cleanup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up project files from root folder')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Dry run mode (default: True)')
    parser.add_argument('--execute', action='store_true',
                        help='Actually move files (overrides --dry-run)')
    parser.add_argument('--report-only', action='store_true',
                        help='Only generate report, do not move files')
    parser.add_argument('--output', type=str,
                        help='Save report to file')
    
    args = parser.parse_args()
    
    dry_run = not args.execute if args.execute else args.dry_run
    
    print("Scanning root folder for project files...")
    project_files = find_project_files_in_root()
    
    print(f"Found {len(project_files)} potential project files")
    
    # Generate report
    report = generate_report(project_files, dry_run=dry_run)
    print("\n" + report)
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nReport saved to: {args.output}")
    
    # Move files if not report-only
    if not args.report_only and project_files:
        if dry_run:
            print("\n" + "=" * 80)
            print("DRY RUN MODE - No files were moved")
            print("Run with --execute to actually move files")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("MOVING FILES...")
            print("=" * 80)
            stats = move_files(project_files, dry_run=False)
            print("\n" + "=" * 80)
            print("MOVEMENT STATISTICS:")
            print(f"  Moved: {stats['moved']}")
            print(f"  Skipped: {stats['skipped']}")
            print(f"  Errors: {stats['errors']}")
            print(f"  Needs Review: {stats['needs_review']}")
            print("=" * 80)


if __name__ == '__main__':
    main()

