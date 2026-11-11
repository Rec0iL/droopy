#!/usr/bin/env python3
"""Render the /droopy template into a droplet folder.

    scaffold.py --manifest droopy.json --out DIR            # fresh droplet
    scaffold.py --manifest DIR/droopy.json --out DIR --update   # refresh scaffold, keep hand edits

Fresh: copies the template, fills __PLACEHOLDERS__, strips `droopy:feature X` blocks that
are not enabled, renames the package, compiles the shader (if qsb-qt6 exists) and writes
droopy.json into the folder.

Update: same rendering, but (1) files in PROTECTED are never overwritten and (2) the bodies
of `droopy:<region> begin/end` regions (options, header, palette, glyphs) are carried over
from the existing files, so hand-written option rows and palettes survive.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "template"

FEATURE_RE = re.compile(r"^\s*(?:#|//)\s*droopy:feature\s+(\w+)\s+(begin|end)\s*$")
REGION_RE = re.compile(r"^(\s*)(?:#|//)\s*droopy:(options|header|palette|glyphs)\s+(begin|end)\b.*$")

# relative to the droplet folder; {pkg} is the package dir
PROTECTED = ["{pkg}/core.py", "shaders/bg.frag", "shaders/bg.frag.qsb", "README.md",
             "packaging/{app_id}.svg", "tests/test_core.py", "droopy.json"]

DEFAULT_FEATURES = {"history": True, "delete": False, "retry": True, "previews": True,
                    "mascot": "pixel"}


def die(msg: str) -> None:
    print(f"scaffold: {msg}", file=sys.stderr)
    sys.exit(1)


def feature_set(m: dict) -> set[str]:
    f = {**DEFAULT_FEATURES, **m.get("features", {})}
    on = {k for k in ("history", "delete", "retry", "previews") if f.get(k)}
    mascot = f.get("mascot", "pixel")
    if mascot in ("pixel", "kaomoji", "glyph"):
        on.add(f"mascot_{mascot}")
    if mascot != "kaomoji":
        on.add("status_chip")
    return on


def strip_features(text: str, enabled: set[str]) -> str:
    out, skip_depth, stack = [], 0, []
    for line in text.splitlines(keepends=True):
        m = FEATURE_RE.match(line)
        if m:
            name, kind = m.group(1), m.group(2)
            if kind == "begin":
                stack.append(name)
                if name not in enabled:
                    skip_depth += 1
            else:
                if stack and stack[-1] == name:
                    stack.pop()
                if name not in enabled and skip_depth:
                    skip_depth -= 1
            continue  # marker lines never reach the output
        if skip_depth == 0:
            out.append(line)
    if stack:
        print(f"scaffold: warning - unbalanced feature markers: {stack}", file=sys.stderr)
    return "".join(out)


def extract_regions(text: str) -> dict[str, str]:
    regions, cur, buf = {}, None, []
    for line in text.splitlines(keepends=True):
        m = REGION_RE.match(line)
        if m:
            if m.group(3) == "begin":
                cur, buf = m.group(2), []
            elif cur == m.group(2):
                regions[cur] = "".join(buf)
                cur = None
            continue
        if cur is not None:
            buf.append(line)
    return regions


def inject_regions(text: str, regions: dict[str, str]) -> str:
    out, cur = [], None
    for line in text.splitlines(keepends=True):
        m = REGION_RE.match(line)
        if m:
            name, kind = m.group(2), m.group(3)
            if kind == "begin":
                out.append(line)
                if name in regions:
                    out.append(regions[name])
                    cur = name
                continue
            if cur == name:
                cur = None
            out.append(line)
            continue
        if cur is None:
            out.append(line)
    return "".join(out)


def placeholders(m: dict, background: str) -> dict[str, str]:
    d = m.get("drop", {})
    deps = m.get("py_deps", [])
    checks = ""
    for c in m.get("tool_checks", []):
        checks += f'command -v {c["cmd"]} >/dev/null || warn "{c["cmd"]} not found - {c.get("hint", "install it")}"\n'
    opt = json.dumps(m.get("option_defaults", {}), indent=4, ensure_ascii=False)
    opt = opt.replace(": true", ": True").replace(": false", ": False").replace(": null", ": None")
    return {
        "__APP_NAME__": m["app_name"],
        "__APP_ID__": m["app_id"],
        "__APP_COMMENT__": m.get("comment", f"{m['app_name']} droplet"),
        "__GENERIC_NAME__": m.get("generic_name", m["app_name"]),
        "__CATEGORIES__": m.get("categories", "Utility;"),
        "__KEYWORDS__": m.get("keywords", ""),
        "__MIMETYPES__": m.get("mimetypes", ""),
        "__PY_DEPS__": " ".join(deps),
        "__PY_REQUIREMENTS__": "\n".join(m.get("py_requirements", [])),
        "__TOOL_CHECKS__": checks,
        "__SUPPORTED__": json.dumps(m.get("supported", [])),
        "__ACCEPT_DIRS__": "True" if m.get("accept_dirs") else "False",
        "__OPTION_DEFAULTS__": opt,
        "__NOTHING_MSG__": d.get("nothing_msg", "Nothing to do here - no supported files found"),
        "__DROP_TITLE__": d.get("title", "Drop files here"),
        "__DROP_HOVER__": d.get("hover", "Release to start"),
        "__DROP_HINT__": d.get("hint", "Files or whole folders"),
        "__DROP_GLYPH__": d.get("glyph", "▣"),
        "__FILE_DIALOG_TITLE__": d.get("file_dialog_title", "Choose files"),
        "__FILE_FILTER__": d.get("file_filter", "All files (*)"),
        "__WORKING_LABEL__": d.get("working_label", "WORKING"),
        "__DONE_TITLE__": d.get("done_title", "Finished!"),
        "__BACKGROUND_COMPONENT__": "Background" if background == "shader" else "BackgroundSoft",
        "__README_BODY__": m.get("readme_body", "").rstrip(),
    }


def render(text: str, ph: dict[str, str], enabled: set[str]) -> str:
    text = strip_features(text, enabled)
    for k, v in ph.items():
        text = text.replace(k, v)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--no-compile", action="store_true", help="skip qsb-qt6 even if present")
    args = ap.parse_args()

    m = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    for key in ("app_name", "app_id"):
        if not m.get(key):
            die(f"manifest needs '{key}'")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", m["app_id"]):
        die("app_id must be lower-case letters/digits/underscore (it becomes the Python package)")
    out = Path(args.out).resolve()
    pkg = m["app_id"]
    enabled = feature_set(m)

    background = m.get("look", {}).get("background", "shader")
    qsb = shutil.which("qsb-qt6") or shutil.which("qsb")
    if background == "shader" and not qsb and not args.no_compile:
        print("scaffold: qsb-qt6 not found - using the QML-only BackgroundSoft fallback", file=sys.stderr)
        background = "soft"
        m.setdefault("look", {})["background"] = "soft"
    ph = placeholders(m, background)

    if out.exists() and not args.update and any(out.iterdir()):
        die(f"{out} exists and is not empty (use --update to refresh a droplet)")
    protected = {p.format(pkg=pkg, app_id=pkg) for p in PROTECTED}

    written, kept = [], []
    for src in sorted(TEMPLATE.rglob("*")):
        if src.is_dir() or "__pycache__" in src.parts:
            continue
        rel = src.relative_to(TEMPLATE)
        if rel.parts[0] == "app":
            rel = Path(pkg, *rel.parts[1:])
        if rel.parts[0] == "shaders" and len(rel.parts) > 1 and rel.parts[1] == "examples":
            continue  # inspiration only, not shipped
        if rel.as_posix() == "packaging/example_icon.svg":
            rel = Path("packaging", f"{pkg}.svg")
        dst = out / rel
        if args.update and rel.as_posix() in protected and dst.exists():
            kept.append(rel.as_posix())
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in (".py", ".qml", ".sh", ".md", ".txt", ".frag", ".svg", "") or src.name == "qmldir":
            text = render(src.read_text(encoding="utf-8"), ph, enabled)
            if args.update and dst.exists():
                old_regions = extract_regions(dst.read_text(encoding="utf-8"))
                if old_regions:
                    text = inject_regions(text, old_regions)
            dst.write_text(text, encoding="utf-8")
            if src.stat().st_mode & 0o111:
                dst.chmod(0o755)
        else:
            shutil.copy2(src, dst)
        written.append(rel.as_posix())

    # unused background variant and dialogs are removed to keep the tree clean
    if background == "shader":
        (out / "qml" / "BackgroundSoft.qml").unlink(missing_ok=True)
    else:
        (out / "qml" / "Background.qml").unlink(missing_ok=True)
        (out / "shaders" / "bg.frag").unlink(missing_ok=True)
        shutil.rmtree(out / "shaders", ignore_errors=True)
    if "history" not in enabled:
        (out / "qml" / "HistoryDialog.qml").unlink(missing_ok=True)
    if "delete" not in enabled:
        (out / "qml" / "DeleteDialog.qml").unlink(missing_ok=True)
    if "mascot_pixel" not in enabled:
        (out / "qml" / "PixelIcon.qml").unlink(missing_ok=True)

    compiled = False
    if background == "shader" and qsb and not args.no_compile:
        frag = out / "shaders" / "bg.frag"
        r = subprocess.run([qsb, "--glsl", "100 es,120,150", "--hlsl", "50", "--msl", "12",
                            "-o", str(frag.with_suffix(".frag.qsb")), str(frag)], capture_output=True, text=True)
        compiled = r.returncode == 0
        if not compiled:
            print("scaffold: shader compile failed:\n" + r.stderr, file=sys.stderr)

    m["generated"] = time.strftime("%Y-%m-%d %H:%M")
    m["droopy_version"] = 1
    (out / "droopy.json").write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"scaffold: {'updated' if args.update else 'created'} {out}")
    print(f"  files written: {len(written)}  kept: {len(kept)}  features: {sorted(enabled)}  "
          f"background: {background}{' (compiled)' if compiled else ''}")
    if kept:
        print("  kept (hand-written): " + ", ".join(kept))
    return 0


if __name__ == "__main__":
    sys.exit(main())
