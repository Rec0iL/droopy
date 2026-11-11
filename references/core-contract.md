# Porting the script into core.process()

`process(src, out_dir, opts, *, progress, cancel) -> Result` runs **one job** on the worker thread.

1. Validate: missing file -> `Result("error", None, "File not found")`; unsupported content that
   is not an error for the user -> `Result("skipped", None, "No <thing> inside this file")`.
2. Compute the target path with `unique_path(out_dir / name, opts["overwrite"])`. Create `out_dir`.
3. Do the work. Call `progress(frac, "short message")` at natural steps (reading, converting,
   writing) and `check(cancel)` inside long loops. Keep messages under ~60 chars.
4. Return `Result("done", main_output, "one-line summary", files=[all written])`. For in-place
   edits return `in_place=True` so the delete flow never deletes the source.
5. Raise `CoreError("human sentence")` for failures the user can act on. Let unexpected exceptions
   propagate; the worker reports them with their type.

Port, don't wrap: move the script's functions into core.py (or import the original script as a
module if it is clean and the user wants to keep editing it there - then `sys.path` must include
its folder in app.py; prefer copying). Replace `print()` with `progress()`. Remove `argparse`
from the logic path; `core.main()` provides the CLI.

Options: everything the interview exposed is a key in `OPTION_DEFAULTS` and arrives in `opts`.
Fixed knobs stay module constants.

Third-party imports: list each top-level module in the manifest `py_deps` (import names, for
install.sh) and `py_requirements` (pip specs, for requirements.txt).

Tests (tests/test_core.py): one happy path per option value that changes output, one skipped case,
one error case, `unique_path` rename vs overwrite, and `expand_inputs` filtering. Build sample
inputs in `tempfile` (e.g. Pillow can write most image formats; zipfile for archives). If the real
input type cannot be synthesised, look for a sample on the machine and `skipUnless` it exists.
