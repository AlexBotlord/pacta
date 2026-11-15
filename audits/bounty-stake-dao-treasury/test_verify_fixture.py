"""Regression tests for the offline evidence consistency checker."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

DIR = Path(__file__).resolve().parent
FIXTURE = json.loads((DIR / "fixture.json").read_text())
CHECKER = (DIR / "verify_fixture.py").read_text()


class FixtureValidationTests(unittest.TestCase):
    def check_fixture(self, mutation=None):
        payload = copy.deepcopy(FIXTURE)
        if mutation:
            mutation(payload)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "fixture.json").write_text(json.dumps(payload))
            (path / "verify_fixture.py").write_text(CHECKER)
            return subprocess.run(
                [sys.executable, str(path / "verify_fixture.py")],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_valid(self):
        self.assertEqual(self.check_fixture().returncode, 0)

    def test_wrong_chain(self):
        self.assertNotEqual(self.check_fixture(lambda f: f.update(chainId=8453)).returncode, 0)

    def test_wrong_block_hash(self):
        def mutate(f):
            next(iter(f["rpc"].values()))["block_hash"] = "0xdead"
        self.assertNotEqual(self.check_fixture(mutate).returncode, 0)

    def test_wrong_threshold(self):
        def mutate(f):
            next(iter(f["rpc"].values()))["threshold_raw"] = "0x" + "00" * 32
        self.assertNotEqual(self.check_fixture(mutate).returncode, 0)

    def test_truncated_owner_array(self):
        def mutate(f):
            next(iter(f["rpc"].values()))["owners_raw"] = "0x"
        self.assertNotEqual(self.check_fixture(mutate).returncode, 0)

    def test_inconsistent_mcp(self):
        def mutate(f):
            f["mcp"]["pacta_scan_control_plane"]["safe"]["ownerCount"] = 7
        self.assertNotEqual(self.check_fixture(mutate).returncode, 0)


if __name__ == "__main__":
    unittest.main()
