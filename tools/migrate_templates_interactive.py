"""
Interactive AST-based tool to extract inline triple-quoted templates from agents/*.py
into templates/<agent>/extracted_<n>.tpl and replace the inline literal with a
render_template(...) expression.

Usage:
  # dry run (shows candidates, does not modify)
  python tools/migrate_templates_interactive.py --dry-run

  # interactive apply (prompts for each candidate, writes files as confirmed)
  python tools/migrate_templates_interactive.py

Notes:
- Backups created with .bak extension for modified files.
- This implementation uses AST to avoid touching docstrings or embedded literals
  that are not simple assignment RHS string literals.
"""
from pathlib import Path
import ast
import argparse
import shutil
import textwrap
import os

KEYWORDS = [
    "terraform", "resource", "provider", "local_file", "helm", "chart", "api", "router",
    "apirouter", "fastapi", "class", "<!doctype", "server {", "http {"
]
MIN_CHARS = 200
PREVIEW_CHARS = 400


def find_string_candidates(source: str, min_chars: int = MIN_CHARS):
    """
    Parse source into AST and return a list of candidate tuples:
      (node, parent, start_lineno, start_col, end_lineno, end_col, value)
    Candidates are ast.Constant nodes with string values containing any KEYWORDS
    and length >= min_chars.
    """
    candidates = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return candidates

    # build parent map
    parent = {}
    for p in ast.walk(tree):
        for ch in ast.iter_child_nodes(p):
            parent[ch] = p

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if len(s) < min_chars:
                continue
            low = s.lower()
            if not any(kw in low for kw in KEYWORDS):
                continue
            start_lineno = getattr(node, "lineno", None)
            start_col = getattr(node, "col_offset", None)
            end_lineno = getattr(node, "end_lineno", start_lineno)
            end_col = getattr(node, "end_col_offset", None)
            candidates.append((node, parent.get(node), start_lineno, start_col, end_lineno, end_col, s))
    return candidates


def lineno_col_to_offset(source_lines, lineno, col):
    # lineno is 1-based
    if lineno is None or col is None:
        return None
    # sum lengths of previous lines
    offset = sum(len(source_lines[i]) for i in range(lineno - 1))
    return offset + col


def ensure_renderer_import_and_get_text(new_text: str):
    """
    Ensure 'from agents.template_renderer import render_template' exists.
    Insert after last import statement or module docstring, preserving newlines.
    Return modified new_text.
    """
    imp_stmt = "from agents.template_renderer import render_template"
    if imp_stmt in new_text:
        return new_text

    try:
        tree = ast.parse(new_text)
    except SyntaxError:
        # best-effort: prepend import
        return imp_stmt + "\n" + new_text

    last_import_end_line = None
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            last_import_end_line = getattr(node, "end_lineno", getattr(node, "lineno", None))

    insert_line = 0
    lines = new_text.splitlines(keepends=True)
    if last_import_end_line:
        # insert after that line
        insert_line = last_import_end_line
    else:
        # if module has docstring, insert after it
        doc = ast.get_docstring(tree)
        if doc:
            # find first Expr node with the docstring
            for node in tree.body:
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    insert_line = getattr(node, "end_lineno", getattr(node, "lineno", 0))
                    break
    # insert at start of line insert_line (0-based index)
    insert_at = 0
    if insert_line and insert_line <= len(lines):
        insert_at = sum(len(lines[i]) for i in range(insert_line))
    return new_text[:insert_at] + (imp_stmt + "\n") + new_text[insert_at:]


def extract_and_prompt(file_path: Path, templates_dir: Path, dry_run: bool, min_chars: int) -> bool:
    text = file_path.read_text(encoding="utf-8")
    source_lines = text.splitlines(keepends=True)
    candidates = find_string_candidates(text, min_chars=min_chars)
    if not candidates:
        return False

    new_text = text
    # We will perform replacements from end to start to keep offsets valid
    processed_any = False
    # sort candidates by start position descending
    def get_start_offset(cand):
        _, _, sl, sc, _, _, _ = cand
        off = lineno_col_to_offset(source_lines, sl, sc)
        return off if off is not None else -1

    candidates_sorted = sorted(candidates, key=get_start_offset, reverse=True)
    idx_counter = 0

    for node, parent_node, sl, sc, el, ec, value in candidates_sorted:
        start_off = lineno_col_to_offset(source_lines, sl, sc)
        end_off = lineno_col_to_offset(source_lines, el, ec)
        if start_off is None or end_off is None:
            continue

        # Skip module docstring: parent is ast.Expr and its parent is ast.Module
        if isinstance(parent_node, ast.Expr):
            # likely docstring or standalone literal; skip
            continue

        # Only allow simple assignments where the string literal is the entire value (safe replacement)
        # i.e., parent_node is ast.Assign and node is the value (or nested Constant exactly)
        allow = False
        if isinstance(parent_node, ast.Assign):
            if parent_node.value is node:
                allow = True
        # also allow keyword arg value in simple call? skip for safety
        if not allow:
            continue

        # Present preview and prompt
        preview = value.strip()
        if len(preview) > PREVIEW_CHARS:
            preview_short = preview[:PREVIEW_CHARS].rstrip() + "\n\n...[truncated]..."
        else:
            preview_short = preview

        print(f"\nFile: {file_path}")
        print("Candidate template (preview):\n")
        print(textwrap.indent(preview_short, "    "))
        while True:
            ans = input("\nAction? [y=extract / n=skip / v=view full / q=quit]: ").strip().lower()
            if ans == "v":
                print("\nFULL CONTENT:\n")
                print(textwrap.indent(preview, "    "))
                continue
            if ans == "q":
                print("Quitting interactive migration.")
                return processed_any
            if ans in ("y", "n"):
                break
            print("Please answer y, n, v, or q.")

        if ans == "n":
            continue

        # proceed to extract
        agent_name = file_path.stem
        tpl_dir = templates_dir / agent_name
        tpl_dir.mkdir(parents=True, exist_ok=True)
        tpl_name = f"extracted_template_{idx_counter}.tpl"
        tpl_path = tpl_dir / tpl_name
        idx_counter += 1

        if not dry_run:
            # write the raw string content from the AST node (node.value)
            tpl_path.write_text(value.lstrip("\n"), encoding="utf-8")
            print(f"  -> wrote template: {tpl_path}")
        else:
            print(f"  -> [dry-run] would write template: {tpl_path}")

        # build replacement expression to insert as RHS of assignment
        replacement_expr = f"render_template('{agent_name}/{tpl_name}', {{}})"
        # replace the substring in new_text between start_off and end_off
        new_text = new_text[:start_off] + replacement_expr + new_text[end_off:]
        # ensure renderer import present (only modify when not dry-run)
        if not dry_run:
            new_text = ensure_renderer_import_and_get_text(new_text)

        processed_any = True

    if processed_any and not dry_run:
        backup = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copyfile(file_path, backup)
        file_path.write_text(new_text, encoding="utf-8")
        print(f"File updated: {file_path} (backup: {backup})")
    elif processed_any and dry_run:
        print(f"[dry-run] {file_path} would be modified (no file written).")

    return processed_any


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agents-dir", default="agents", help="Directory containing agents Python files")
    parser.add_argument("--templates-dir", default="templates", help="Directory to write templates into")
    parser.add_argument("--min-chars", type=int, default=MIN_CHARS)
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; prompt only")
    args = parser.parse_args()

    agents_dir = Path(args.agents_dir)
    templates_dir = Path(args.templates_dir)
    changed = []

    for py in sorted(agents_dir.glob("*.py")):
        print(f"\nScanning {py}")
        try:
            ok = extract_and_prompt(py, templates_dir, args.dry_run, args.min_chars)
            if ok:
                changed.append(str(py))
        except Exception as e:
            print(f"ERROR scanning {py}: {e}")

    print("\nDone. Files changed:" if changed else "\nNo template candidates extracted.")
    for c in changed:
        print(" -", c)
    if args.dry_run:
        print("\nDry-run mode: no files modified. Re-run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()