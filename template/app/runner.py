"""Helpers for droplets that wrap an external command instead of importing Python.

    rc, tail = run_command(["tool", "--flag", str(src)], progress=cb, cancel=ev)

Progress is guessed from stdout/stderr lines: "42%", "42.5 %", "3/10", "[3 of 10]",
"frame=  120" with a known total, etc. Pass `total_re` / `current_re` to override.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
from collections import deque
from pathlib import Path
from typing import Callable, Sequence

Progress = Callable[[float, str], None]

_PERCENT = re.compile(r"(\d{1,3}(?:[.,]\d+)?)\s*%")
_OF = re.compile(r"\b(\d+)\s*(?:/|of|von)\s*(\d+)\b")


class CommandError(Exception):
    pass


def find_tool(*names: str) -> str | None:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def guess_progress(line: str) -> float | None:
    m = _PERCENT.search(line)
    if m:
        return min(1.0, float(m.group(1).replace(",", ".")) / 100.0)
    m = _OF.search(line)
    if m:
        cur, tot = int(m.group(1)), int(m.group(2))
        if tot > 0 and cur <= tot:
            return cur / tot
    return None


def run_command(cmd: Sequence[str], *, cwd: str | Path | None = None, env: dict | None = None,
                progress: Progress | None = None, cancel: threading.Event | None = None,
                line_re: re.Pattern | None = None, tail_lines: int = 30,
                timeout: float | None = None) -> tuple[int, str]:
    """Run `cmd`, stream its output for progress, return (returncode, last lines).

    `line_re` with a group named `pct` (0..100) or `cur`/`tot` overrides the heuristics.
    Raises CommandError if the command cannot be started; the caller decides what a
    non-zero return code means.
    """
    try:
        proc = subprocess.Popen(
            list(cmd), cwd=str(cwd) if cwd else None, env={**os.environ, **(env or {})},
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
            bufsize=1, start_new_session=True,
        )
    except OSError as exc:
        raise CommandError(f"Cannot start {cmd[0]}: {exc.strerror or exc}") from exc

    tail: deque[str] = deque(maxlen=tail_lines)
    last = -1.0
    assert proc.stdout is not None
    try:
        for raw in proc.stdout:
            line = raw.rstrip("\r\n")
            # progress bars often rewrite one line with \r - keep the last chunk
            if "\r" in raw:
                line = raw.split("\r")[-1].strip()
            if line:
                tail.append(line)
            if cancel is not None and cancel.is_set():
                proc.kill()
                raise_cancel()
            frac = None
            if line_re is not None:
                m = line_re.search(line)
                if m:
                    gd = m.groupdict()
                    if gd.get("pct"):
                        frac = min(1.0, float(gd["pct"]) / 100.0)
                    elif gd.get("cur") and gd.get("tot") and int(gd["tot"]) > 0:
                        frac = int(gd["cur"]) / int(gd["tot"])
            else:
                frac = guess_progress(line)
            if progress is not None and frac is not None and frac > last:
                last = frac
                progress(frac, line[:80])
        proc.wait(timeout=timeout)
    finally:
        if proc.poll() is None:
            proc.kill()
    return proc.returncode, "\n".join(tail)


def raise_cancel() -> None:
    from .core import Cancelled
    raise Cancelled()
