"""__APP_NAME__ core: the actual work, with no Qt in it.

/droopy fills this module in from the original script. Contract used by the GUI:

    SUPPORTED        set of lower-case extensions the droplet accepts ({".exe", ...});
                     an empty set means "any file".
    ACCEPT_DIRS      True if a dropped folder is itself one job (e.g. an image folder),
                     False if folders should be searched for SUPPORTED files instead.
    OPTION_DEFAULTS  app-specific settings exposed in the UI ({"quality": 80, ...}).
                     Keys are camelCase; they are merged into settings.DEFAULTS and
                     passed to process() as `opts`.
    expand_inputs()  dropped paths -> list of job paths.
    process()        one job. Reports progress 0..1, checks `cancel`, returns Result.
    main()           optional CLI so the script still works from a terminal.
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

SUPPORTED: set[str] = set(__SUPPORTED__)
ACCEPT_DIRS: bool = __ACCEPT_DIRS__
OPTION_DEFAULTS: dict = __OPTION_DEFAULTS__

Progress = Callable[[float, str], None]


class CoreError(Exception):
    """A job failed for a reason worth showing to the user."""


class Cancelled(Exception):
    """The job was cancelled (app closing)."""


@dataclass
class Result:
    status: str                    # done | error | skipped
    output: Path | None            # main output (shown, revealed, previewed)
    message: str                   # one line for the job card
    files: list[Path] = field(default_factory=list)   # everything written
    in_place: bool = False         # True if the source itself was modified


# --------------------------------------------------------------------------- inputs
def is_candidate(p: Path) -> bool:
    return p.is_file() and (not SUPPORTED or p.suffix.lower() in SUPPORTED)


def _natural_key(p: Path):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.name)]


def expand_inputs(paths: Iterable[str | Path]) -> list[Path]:
    """Files are taken as-is (if supported); folders become one job or are searched."""
    out: list[Path] = []
    seen: set[Path] = set()

    def add(p: Path) -> None:
        try:
            key = p.resolve()
        except OSError:
            key = p
        if key not in seen:
            seen.add(key)
            out.append(p)

    for raw in paths:
        p = Path(raw).expanduser()
        if p.is_dir():
            if ACCEPT_DIRS:
                add(p)
            else:
                for f in sorted(p.rglob("*"), key=_natural_key):
                    if is_candidate(f):
                        add(f)
        elif is_candidate(p):
            add(p)
    return out


def unique_path(path: Path, overwrite: str = "rename") -> Path:
    """`rename` -> name (2).ext, name (3).ext ... ; `overwrite` -> path as given."""
    if overwrite == "overwrite" or not path.exists():
        return path
    n = 2
    while True:
        cand = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not cand.exists():
            return cand
        n += 1


def check(cancel: threading.Event | None) -> None:
    if cancel is not None and cancel.is_set():
        raise Cancelled()


# --------------------------------------------------------------------------- the job
def process(src: Path, out_dir: Path, opts: dict, *, progress: Progress | None = None,
            cancel: threading.Event | None = None) -> Result:
    """Run one job. `opts` holds every key of OPTION_DEFAULTS plus:
        overwrite: "rename" | "overwrite"
    Call progress(frac, msg) as you go; call check(cancel) in long loops.
    Return Result("done"/"skipped"/"error", output, message, files).
    Raise CoreError for failures with a human message; anything else is reported with its type.
    """
    # droopy: replace this body with the script's logic (see references/core-contract.md)
    raise NotImplementedError("__APP_NAME__ core.process() is not implemented yet")


# --------------------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> int:
    """`python3 -m __APP_ID__.core file ...` - terminal use without the GUI."""
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="__APP_COMMENT__")
    ap.add_argument("paths", nargs="+", help="input files or folders")
    ap.add_argument("-o", "--out", help="output folder (default: next to each input)")
    ap.add_argument("--overwrite", action="store_true", help="replace existing files instead of renaming")
    # droopy: add one argument per OPTION_DEFAULTS key here
    args = ap.parse_args(argv)

    items = expand_inputs(args.paths)
    if not items:
        print("Nothing to do - no supported files found.", file=sys.stderr)
        return 1
    opts = {**OPTION_DEFAULTS, "overwrite": "overwrite" if args.overwrite else "rename"}
    rc = 0
    for p in items:
        try:
            res = process(p, Path(args.out) if args.out else p.parent, opts,
                          progress=lambda f, m: None)
        except CoreError as exc:
            res = Result("error", None, str(exc))
        tag = {"done": "ok  ", "skipped": "skip", "error": "FAIL"}[res.status]
        print(f"[{tag}] {p.name}: {res.message}" + (f" -> {res.output}" if res.output else ""))
        if res.status == "error":
            rc = 1
    return rc


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
