# Wrapping a non-Python tool (or a Python script that must run as a process)

Use `runner.run_command()` from `<pkg>/runner.py` inside `process()`:

```python
from . import runner

def process(src, out_dir, opts, *, progress=None, cancel=None):
    tool = runner.find_tool("ffmpeg")
    if not tool:
        raise CoreError("ffmpeg is not installed")
    target = unique_path(out_dir / f"{src.stem}.{opts['format']}", opts["overwrite"])
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [tool, "-y", "-i", str(src), "-q:v", str(opts["quality"]), str(target)]
    rc, tail = runner.run_command(cmd, progress=progress, cancel=cancel,
                                  line_re=re.compile(r"time=(?P<cur>\d+)"))  # optional override
    if rc != 0:
        raise CoreError(tail.splitlines()[-1] if tail else f"{tool} failed ({rc})")
    return Result("done", target, f"{opts['format'].upper()} written", [target])
```

Discovery (Phase 0):
1. `tools/analyze.py <command>` parses `--help` into options; confirm each with the user.
2. If the user named a sample file, run the tool once in the scratchpad with output captured
   and look for progress lines: `NN%`, `x/y`, `frame=`, `time=`. If found, write a `line_re`
   with named groups `pct` or `cur`/`tot` (tot may need to be measured first, e.g. duration
   via ffprobe - then compute `frac` yourself in a callback instead of `line_re`).
3. Without any pattern, progress is per job (0 -> 1); say so in the README.

Manifest: `kind: "wrapped"`, add `tool_checks: [{"cmd": "ffmpeg", "hint": "sudo dnf install ffmpeg"}]`
so install.sh warns when the tool is missing. `py_deps` stays empty unless the wrapper needs Python
packages.

Cancel: `run_command` kills the process group when `cancel` is set; partial outputs should be
removed in `process()` (`target.unlink(missing_ok=True)` in an `except Cancelled`).
