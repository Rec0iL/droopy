#!/usr/bin/env python3
"""Run a generated droplet for verification: offscreen smoke test and/or a screenshot.

    droplet_check.py DIR --smoke FILE...                 # offscreen: queue files, print job results
    droplet_check.py DIR --shot out.png [FILE...]        # real display: grab the window after 3.5 s
    droplet_check.py DIR --shot out.png --theme dark     # force a theme for the grab
    droplet_check.py DIR --shot out.png --offscreen      # grab without a window (shader will NOT render)

Exit code 1 if the window failed to load or QML printed errors.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

RUNNER = r'''
import sys, json
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
import importlib
cfg = json.loads(sys.argv[1]); files = sys.argv[2:]
A = importlib.import_module(cfg["pkg"] + ".app")
orig = QGuiApplication.exec
state = {}
B = importlib.import_module(cfg["pkg"] + ".backend").Backend
class Spy(B):
    def __init__(self):
        super().__init__(); state["be"] = self
A.Backend = Spy
def fake_exec(self=None):
    app = QGuiApplication.instance()
    def finish():
        be = state.get("be")
        if cfg.get("shot"):
            w = app.allWindows()[0]
            img = w.grabWindow()
            print("SHOT", img.save(cfg["shot"]), img.width(), img.height())
        if be is not None:
            print("JOBS", be.jobCount, "mascot", be.mascotState)
            for r in be.model.rows:
                print("  ", r["status"].ljust(8), r["name"], "|", r["message"], "|", r["output"])
        app.quit()
    QTimer.singleShot(int(cfg.get("wait", 3500)), finish)
    return orig()
QGuiApplication.exec = staticmethod(fake_exec)
sys.exit(A.run(["main.py"] + files))
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--smoke", nargs="*", metavar="FILE")
    ap.add_argument("--shot")
    ap.add_argument("--theme", choices=["auto", "light", "dark"], default="auto")
    ap.add_argument("--offscreen", action="store_true")
    ap.add_argument("--wait", type=int, default=3500, help="ms before grabbing / reporting")
    ap.add_argument("files", nargs="*")
    args = ap.parse_intermixed_args()

    app_dir = Path(args.dir).resolve()
    manifest = app_dir / "droopy.json"
    if not manifest.exists():
        print("no droopy.json in", app_dir, file=sys.stderr)
        return 1
    pkg = json.loads(manifest.read_text())["app_id"]
    files = list(args.files) + list(args.smoke or [])

    env = {**os.environ, "PYTHONPATH": str(app_dir)}
    with tempfile.TemporaryDirectory() as cfg_home:
        env["XDG_CONFIG_HOME"] = cfg_home  # never touch the user's real settings
        if args.theme != "auto":
            d = Path(cfg_home) / json.loads(manifest.read_text())["app_name"]
            d.mkdir(parents=True)
            (d / "settings.json").write_text(json.dumps({"theme": args.theme}))
        if args.smoke is not None or args.offscreen:
            env["QT_QPA_PLATFORM"] = "offscreen"
            env.setdefault("QSG_RHI_BACKEND", "opengl")
        cfg = {"pkg": pkg, "shot": args.shot, "wait": args.wait}
        r = subprocess.run([sys.executable, "-c", RUNNER, json.dumps(cfg)] + [str(Path(f).resolve()) for f in files],
                           cwd=app_dir, env=env, capture_output=True, text=True, timeout=60)
    err = "\n".join(l for l in r.stderr.splitlines() if "font.db" not in l)
    print(r.stdout.rstrip())
    if err.strip():
        print("--- stderr ---\n" + err, file=sys.stderr)
    qml_errors = [l for l in err.splitlines() if ".qml" in l and ("error" in l.lower() or "TypeError" in l)]
    if r.returncode != 0 or qml_errors:
        print(f"droplet_check: FAILED (rc={r.returncode}, qml errors={len(qml_errors)})", file=sys.stderr)
        return 1
    print("droplet_check: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
