#!/usr/bin/env python3
"""Static look at a script to seed the /droopy interview. Prints JSON.

    analyze.py path/to/script.py          # Python: AST - argparse options, constants, extensions, deps
    analyze.py path/to/tool               # anything else: runs `tool --help` and parses the options

Nothing here is authoritative: the interview confirms every row with the user.
"""
from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

STDLIB_HINT = {"os", "sys", "re", "json", "io", "pathlib", "argparse", "shutil", "subprocess",
               "tempfile", "time", "math", "typing", "dataclasses", "collections", "itertools",
               "functools", "logging", "zipfile", "tarfile", "glob", "hashlib", "datetime", "csv",
               "threading", "concurrent", "struct", "base64", "urllib", "http", "string", "random"}
EXT_RE = re.compile(r"^\.[a-z0-9]{1,5}$", re.I)


def lit(node):
    try:
        return ast.literal_eval(node)
    except Exception:  # noqa: BLE001
        return ast.unparse(node) if hasattr(ast, "unparse") else "<expr>"


def analyze_python(path: Path) -> dict:
    src = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src, filename=str(path))
    info: dict = {"kind": "python", "path": str(path), "options": [], "positionals": [],
                  "constants": {}, "extensions": set(), "imports": set(), "functions": [],
                  "uses_stdin": False, "has_main_guard": False, "uses_gui": False,
                  "deletes_files": False, "writes_files": False, "prints_progress": False}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for n in names:
                top = n.split(".")[0]
                if top and top not in STDLIB_HINT:
                    info["imports"].add(top)
                if top in ("tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "gi"):
                    info["uses_gui"] = True
        elif isinstance(node, ast.FunctionDef):
            info["functions"].append({"name": node.name, "args": [a.arg for a in node.args.args],
                                      "doc": (ast.get_docstring(node) or "")[:120]})
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and EXT_RE.match(node.value):
            info["extensions"].add(node.value.lower())
        elif isinstance(node, ast.Call):
            fn = ast.unparse(node.func) if hasattr(ast, "unparse") else ""
            if fn.endswith("add_argument"):
                opt = {"flags": [lit(a) for a in node.args], }
                for kw in node.keywords:
                    opt[kw.arg] = lit(kw.value)
                (info["positionals"] if not str(opt["flags"][0]).startswith("-") else info["options"]).append(opt)
            if fn in ("input",) or "stdin" in fn:
                info["uses_stdin"] = True
            if fn.endswith((".remove", ".unlink", ".rmtree")) or fn in ("os.remove", "os.unlink", "shutil.rmtree"):
                info["deletes_files"] = True
            if fn in ("open",) and len(node.args) > 1 and isinstance(node.args[1], ast.Constant) \
                    and "w" in str(node.args[1].value):
                info["writes_files"] = True
            if fn.endswith(".save") or fn.endswith(".write_bytes") or fn.endswith(".write_text"):
                info["writes_files"] = True
            if fn == "print" and node.args and isinstance(node.args[0], ast.JoinedStr):
                txt = ast.unparse(node.args[0])
                if "%" in txt or "/" in txt:
                    info["prints_progress"] = True
        elif isinstance(node, ast.If):
            t = ast.unparse(node.test) if hasattr(ast, "unparse") else ""
            if "__name__" in t and "__main__" in t:
                info["has_main_guard"] = True
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.isupper():
                info["constants"][name] = lit(node.value)
    info["extensions"] = sorted(info["extensions"])
    info["imports"] = sorted(info["imports"])
    info["droppable"] = bool(info["positionals"]) or any(
        f["args"] and any(k in f["args"][0] for k in ("path", "file", "src", "input")) for f in info["functions"])
    return info


HELP_RE = re.compile(r"^\s*(-\w)?,?\s*(--[\w-]+)(?:[ =]([A-Z_<>\[\]|.]+))?\s{2,}(.*)$")


def analyze_wrapped(path: str) -> dict:
    exe = shutil.which(path) or path
    info = {"kind": "wrapped", "path": exe, "options": [], "help": "", "droppable": True}
    for flag in ("--help", "-h"):
        try:
            r = subprocess.run([exe, flag], capture_output=True, text=True, timeout=10, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError) as exc:
            info["error"] = str(exc)
            continue
        text = (r.stdout or "") + (r.stderr or "")
        if text.strip():
            info["help"] = text[:6000]
            for line in text.splitlines():
                m = HELP_RE.match(line)
                if m:
                    info["options"].append({"short": m.group(1), "long": m.group(2),
                                            "value": m.group(3), "help": m.group(4).strip()})
            break
    return info


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    target = sys.argv[1]
    p = Path(target)
    if p.suffix == ".py" and p.is_file():
        info = analyze_python(p)
    else:
        info = analyze_wrapped(target)
    print(json.dumps(info, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
