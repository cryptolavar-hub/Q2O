"""
Generate side-by-side comparison of GitHub vs Local file system.
"""

import subprocess
from pathlib import Path
from typing import Set, List, Tuple
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_git_tracked_root_items() -> Set[str]:
    """Get root-level items tracked in git."""
    try:
        result = subprocess.run(
            ['git', 'ls-tree', '-r', '--name-only', 'HEAD'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        
        root_items = set()
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('/')
            if parts:
                root_item = parts[0]
                # Exclude Tenant_Projects and addon_portal from root comparison
                if root_item not in ['Tenant_Projects', 'addon_portal']:
                    root_items.add(root_item)
        
        return root_items
    except Exception as e:
        print(f"Error: {e}")
        return set()


def get_local_root_items() -> Set[str]:
    """Get all root-level items in local file system."""
    items = set()
    for item in PROJECT_ROOT.iterdir():
        # Include all items, even hidden ones
        items.add(item.name)
    return items


def is_git_ignored(item: str) -> bool:
    """Check if item is git-ignored."""
    try:
        result = subprocess.run(
            ['git', 'check-ignore', '-q', item],
            cwd=PROJECT_ROOT,
            capture_output=True,
            check=False
        )
        return result.returncode == 0
    except:
        # Fallback: check common ignored patterns from .gitignore
        # Read .gitignore to check patterns
        gitignore_path = PROJECT_ROOT / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                gitignore_content = f.read()
                # Check if item matches any pattern
                for line in gitignore_content.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # Simple pattern matching
                    if line == item or line.endswith('/') and item.startswith(line[:-1]):
                        return True
                    if line.startswith('*') and item.endswith(line[1:]):
                        return True
        
        # Additional common patterns
        if item in ['Tenant_Projects', 'addon_portal', '.git', '.llm_cache']:
            return True
        
        return False


def get_item_type(item: str) -> str:
    """Get item type (FILE or DIR)."""
    item_path = PROJECT_ROOT / item
    if item_path.is_dir():
        return "DIR"
    elif item_path.is_file():
        return "FILE"
    else:
        return "UNKNOWN"


def main():
    """Generate side-by-side comparison."""
    git_items = get_git_tracked_root_items()
    local_items = get_local_root_items()
    
    # Combine and sort
    all_items = sorted(git_items | local_items)
    
    # Build comparison data
    comparison: List[Tuple[str, str, str, str]] = []
    
    for item in all_items:
        in_git = item in git_items
        in_local = item in local_items
        ignored = is_git_ignored(item)
        
        git_status = "YES" if in_git else "NO"
        local_status = "YES" if in_local else "NO"
        
        if in_local:
            item_type = get_item_type(item)
        else:
            item_type = "?"
        
        notes = ""
        if ignored:
            notes = "IGNORED"
        elif in_local and not in_git:
            # Tenant_Projects is the container folder for all projects (correctly not in git)
            if item == 'Tenant_Projects':
                notes = "PROJECT CONTAINER (correctly not in git)"
            elif item == 'addon_portal':
                notes = "PLATFORM FOLDER (should be tracked in git)"
            elif item == 'k8s':
                notes = "PROJECT GENERATED (should be in Tenant_Projects/{project_id}/)"
            else:
                notes = "NOT TRACKED"
        elif in_git and not in_local:
            notes = "MISSING LOCALLY"
        
        comparison.append((item, git_status, local_status, item_type, notes))
    
    # Generate markdown table
    lines = [
        "# GitHub vs Local File System - Root Folder Comparison",
        "",
        "**Generated:** " + str(Path(__file__).stat().st_mtime),
        "",
        "## Side-by-Side Comparison",
        "",
        "| Item Name | In GitHub | In Local | Type | Notes |",
        "|-----------|-----------|----------|------|-------|"
    ]
    
    for item, git_status, local_status, item_type, notes in comparison:
        # Format item name (escape pipes)
        item_display = item.replace('|', '\\|')
        lines.append(f"| `{item_display}` | {git_status} | {local_status} | {item_type} | {notes} |")
    
    lines.extend([
        "",
        "## Summary",
        "",
        f"- **Total items in GitHub:** {len(git_items)}",
        f"- **Total items in local:** {len(local_items)}",
        f"- **In both:** {sum(1 for _, g, l, _, _ in comparison if g == 'YES' and l == 'YES')}",
        f"- **GitHub only (missing locally):** {sum(1 for _, g, l, _, _ in comparison if g == 'YES' and l == 'NO')}",
        f"- **Local only (not tracked):** {sum(1 for _, g, l, _, n in comparison if g == 'NO' and l == 'YES' and 'IGNORED' not in n)}",
        f"- **Local ignored:** {sum(1 for _, g, l, _, n in comparison if 'IGNORED' in n)}",
        "",
        "## Notes",
        "",
        "- **IGNORED**: Item is in .gitignore (intentionally excluded from git)",
        "- **NOT TRACKED**: Item exists locally but is not in git (may need to be added or ignored)",
        "- **MISSING LOCALLY**: Item is in git but doesn't exist locally (may need to be restored)",
        ""
    ])
    
    report = "\n".join(lines)
    print(report)
    
    # Save to file
    output_file = PROJECT_ROOT / "docs" / "GITHUB_VS_LOCAL_COMPARISON.md"
    output_file.write_text(report, encoding='utf-8')
    print(f"\n\nReport saved to: {output_file}")


if __name__ == '__main__':
    main()

