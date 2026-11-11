"""Tests for __APP_NAME__'s core module. /droopy adds cases for the script's real behaviour."""
import tempfile
import unittest
from pathlib import Path

from __APP_ID__ import core


class CoreTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)

    def tearDown(self):
        self._t.cleanup()

    def test_unique_path(self):
        p = self.tmp / "a.txt"
        self.assertEqual(core.unique_path(p), p)
        p.write_text("x")
        self.assertEqual(core.unique_path(p).name, "a (2).txt")
        self.assertEqual(core.unique_path(p, "overwrite"), p)

    def test_expand_inputs_ignores_unknown(self):
        (self.tmp / "notes.unknownext").write_text("x")
        if core.SUPPORTED:
            self.assertEqual(core.expand_inputs([self.tmp]), [])

    def test_missing_file_is_handled(self):
        try:
            res = core.process(self.tmp / "nope.bin", self.tmp, {**core.OPTION_DEFAULTS, "overwrite": "rename"})
            self.assertEqual(res.status, "error")
        except core.CoreError:
            pass  # also acceptable

    # droopy: add real tests here (one happy path per option, one skipped case, one error case)


if __name__ == "__main__":
    unittest.main()
