"""
Compare GitHub repository contents with local file system root folder.
"""

import subprocess
from pathlib import Path
from typing import Set, Dict, List
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_git_tracked_files() -> Set[str]:
    """Get all files/folders tracked in git (root level only)."""
    try:
        result = subprocess.run(
            ['git', 'ls-tree', '-r', '--name-only', 'HEAD'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        
        tracked = set()
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            # Get root-level items only (first component)
            parts = line.split('/')
            if parts:
                root_item = parts[0]
                # Exclude Tenant_Projects and addon_portal (they're tracked but we want root comparison)
                if root_item not in ['Tenant_Projects', 'addon_portal']:
                    tracked.add(root_item)
        
        return tracked
    except Exception as e:
        print(f"Error getting git tracked files: {e}")
        return set()


def get_local_root_items() -> Set[str]:
    """Get all files/folders in local root directory."""
    root_items = set()
    
    for item in PROJECT_ROOT.iterdir():
        # Skip hidden items that start with . (except .git, .github)
        if item.name.startswith('.') and item.name not in ['.git', '.github']:
            continue
        root_items.add(item.name)
    
    return root_items


def get_git_ignored_items() -> Set[str]:
    """Get items that are git-ignored."""
    try:
        result = subprocess.run(
            ['git', 'status', '--ignored', '--porcelain'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        
        ignored = set()
        for line in result.stdout.strip().split('\n'):
            if line.startswith('!!'):
                # Format: !! path/to/item
                item_path = line[3:].strip()
                # Get root-level item
                parts = item_path.split('/')
                if parts:
                    ignored.add(parts[0])
        
        return ignored
    except Exception as e:
        print(f"Error getting git ignored items: {e}")
        return set()


def categorize_item(item: str, git_tracked: Set[str], local_items: Set[str], git_ignored: Set[str]) -> str:
    """Categorize an item."""
    in_git = item in git_tracked
    in_local = item in local_items
    is_ignored = item in git_ignored
    
    if in_git and in_local:
        return "IN_BOTH"
    elif in_git and not in_local:
        return "GIT_ONLY"
    elif not in_git and in_local:
        if is_ignored:
            return "LOCAL_IGNORED"
        else:
            return "LOCAL_ONLY"
    else:
        return "NEITHER"


def main():
    """Generate comparison report."""
    print("Analyzing GitHub vs Local file system...")
    print()
    
    git_tracked = get_git_tracked_files()
    local_items = get_local_root_items()
    git_ignored = get_git_ignored_items()
    
    # Combine all items
    all_items = git_tracked | local_items
    
    # Categorize
    categories: Dict[str, List[str]] = {
        "IN_BOTH": [],
        "GIT_ONLY": [],
        "LOCAL_ONLY": [],
        "LOCAL_IGNORED": [],
    }
    
    for item in sorted(all_items):
        category = categorize_item(item, git_tracked, local_items, git_ignored)
        if category in categories:
            categories[category].append(item)
    
    # Generate report
    report_lines = [
        "=" * 100,
        "GITHUB vs LOCAL FILE SYSTEM - ROOT FOLDER COMPARISON",
        "=" * 100,
        "",
        f"Generated: {Path(__file__).stat().st_mtime}",
        "",
        "LEGEND:",
        "  IN_BOTH       - Item exists in both GitHub and local (tracked, synced)",
        "  GIT_ONLY      - Item exists in GitHub but not in local (missing locally)",
        "  LOCAL_ONLY    - Item exists locally but not in GitHub (untracked, may need .gitignore)",
        "  LOCAL_IGNORED - Item exists locally but is git-ignored (intentionally excluded)",
        "",
        "=" * 100,
        "",
    ]
    
    # IN_BOTH section
    if categories["IN_BOTH"]:
        report_lines.append(f"IN BOTH (GitHub + Local) - {len(categories['IN_BOTH'])} items:")
        report_lines.append("-" * 100)
        for item in categories["IN_BOTH"]:
            item_path = PROJECT_ROOT / item
            item_type = "DIR" if item_path.is_dir() else "FILE"
            report_lines.append(f"  [{item_type:4}] {item}")
        report_lines.append("")
    
    # GIT_ONLY section
    if categories["GIT_ONLY"]:
        report_lines.append(f"GIT ONLY (In GitHub, missing locally) - {len(categories['GIT_ONLY'])} items:")
        report_lines.append("-" * 100)
        for item in categories["GIT_ONLY"]:
            report_lines.append(f"  [MISS] {item}")
        report_lines.append("")
    
    # LOCAL_ONLY section
    if categories["LOCAL_ONLY"]:
        report_lines.append(f"LOCAL ONLY (Not in GitHub, not ignored) - {len(categories['LOCAL_ONLY'])} items:")
        report_lines.append("-" * 100)
        for item in categories["LOCAL_ONLY"]:
            item_path = PROJECT_ROOT / item
            item_type = "DIR" if item_path.is_dir() else "FILE"
            report_lines.append(f"  [{item_type:4}] {item} - NOT TRACKED")
        report_lines.append("")
    
    # LOCAL_IGNORED section
    if categories["LOCAL_IGNORED"]:
        report_lines.append(f"LOCAL IGNORED (In .gitignore) - {len(categories['LOCAL_IGNORED'])} items:")
        report_lines.append("-" * 100)
        for item in categories["LOCAL_IGNORED"]:
            item_path = PROJECT_ROOT / item
            item_type = "DIR" if item_path.is_dir() else "FILE"
            report_lines.append(f"  [{item_type:4}] {item} - IGNORED")
        report_lines.append("")
    
    # Summary
    report_lines.extend([
        "=" * 100,
        "SUMMARY",
        "=" * 100,
        f"Total items in GitHub: {len(git_tracked)}",
        f"Total items in local: {len(local_items)}",
        f"In both: {len(categories['IN_BOTH'])}",
        f"GitHub only: {len(categories['GIT_ONLY'])}",
        f"Local only (untracked): {len(categories['LOCAL_ONLY'])}",
        f"Local ignored: {len(categories['LOCAL_IGNORED'])}",
        "=" * 100,
    ])
    
    report = "\n".join(report_lines)
    print(report)
    
    # Save to file
    output_file = PROJECT_ROOT / "docs" / "GITHUB_VS_LOCAL_COMPARISON.md"
    output_file.write_text(report, encoding='utf-8')
    print(f"\nReport saved to: {output_file}")


if __name__ == '__main__':
    main()

