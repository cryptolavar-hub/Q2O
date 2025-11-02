

import ast
import os
import sys
from pathlib import Path
import py_compile

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "agents"
TEMPLATES_DIR = REPO_ROOT / "templates"

def check_syntax(pyfile: Path) -> bool:
    try:
        py_compile.compile(str(pyfile), doraise=True)
        return True
    except py_compile.PyCompileError as e:
        print(f"[SYNTAX ERROR] {pyfile}: {e}")
        return False

def build_parent_map(tree):
    parent = {}
    for p in ast.walk(tree):
        for ch in ast.iter_child_nodes(p):
            parent[ch] = p
    return parent

def find_render_template_issues(pyfile: Path):
    src = pyfile.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except Exception as e:
        return {"parse_error": str(e)}

    parent_map = build_parent_map(tree)
    issues = {"missing_import": False, "bad_calls": [], "templates_missing": []}

    # check import
    has_import = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "agents.template_renderer":
                for n in node.names:
                    if n.name == "render_template":
                        has_import = True
                        break
    if not has_import:
        issues["missing_import"] = True

    # locate render_template call nodes and validate parent is Assign and that assigned value is the Call
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # function may be Name or Attribute
            func = node.func
            is_rt = False
            if isinstance(func, ast.Name) and func.id == "render_template":
                is_rt = True
            elif isinstance(func, ast.Attribute) and func.attr == "render_template":
                is_rt = True
            if not is_rt:
                continue

            parent = parent_map.get(node)
            ok = False
            # allow: Assign(value=Call)
            if isinstance(parent, ast.Expr):
                # an expression stmt containing the call -> warn (shouldn't be top-level expr)
                issues["bad_calls"].append(("expr_call", getattr(node, "lineno", None)))
            if isinstance(parent, ast.Assign):
                # check that the call is the entire value
                if parent.value is node:
                    ok = True
            if not ok and not isinstance(parent, ast.Assign):
                issues["bad_calls"].append(("not_assign", getattr(node, "lineno", None)))

            # check arguments: first arg should be a string literal pointing to template path
            if node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    tpl_path = TEMPLATES_DIR / first.value
                    if not tpl_path.exists():
                        issues["templates_missing"].append(first.value)
                else:
                    # not a string literal
                    issues["templates_missing"].append(f"nonliteral_arg_at_line_{getattr(node, 'lineno', '?')}")
    return issues

def main():
    any_problem = False
    print(f"Repo root: {REPO_ROOT}")
    if not AGENTS_DIR.exists():
        print("Agents dir not found:", AGENTS_DIR)
        sys.exit(1)

    pyfiles = sorted(AGENTS_DIR.glob("*.py"))
    for p in pyfiles:
        print("\n== Checking", p.name)
        ok_syntax = check_syntax(p)
        if not ok_syntax:
            any_problem = True
            continue
        issues = find_render_template_issues(p)
        if "parse_error" in issues:
            print("Parse error:", issues["parse_error"])
            any_problem = True
            continue

        if issues["missing_import"]:
            print("  [WARN] render_template import missing.")
            any_problem = True
        if issues["bad_calls"]:
            print("  [WARN] render_template used in unsafe context at lines:", issues["bad_calls"])
            any_problem = True
        if issues["templates_missing"]:
            print("  [WARN] Referenced templates missing:", issues["templates_missing"])
            any_problem = True
        if not issues["missing_import"] and not issues["bad_calls"] and not issues["templates_missing"]:
            print("  OK")

    # List added templates and backups
    if TEMPLATES_DIR.exists():
        print("\nTemplates dir present. Sample contents:")
        for item in sorted(TEMPLATES_DIR.rglob("*"))[:20]:
            print(" -", item.relative_to(REPO_ROOT))
    bak_files = list(AGENTS_DIR.glob("*.bak"))
    if bak_files:
        print("\nBackup files (.bak) present for review:")
        for b in bak_files:
            print(" -", b.name)

    print("\nValidation complete.")
    if any_problem:
        print("Issues detected. Review warnings above. To revert a file use: mv file.py.bak file.py")
        sys.exit(2)
    else:
        print("No automatic problems detected.")
        sys.exit(0)

if __name__ == '__main__':
    main()