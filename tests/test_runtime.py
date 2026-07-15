import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "runtime"))

from the_native import lower_to_c
from the_runtime import compile_source

RUNTIME = ROOT / "tools" / "runtime" / "the_runtime.py"
LOADER = ROOT / "tools" / "runtime" / "the_loader.py"
EXAMPLE = ROOT / "examples" / "iters_and_strides.the"


class RuntimeTests(unittest.TestCase):
    def invoke(self, mode, source):
        return subprocess.run(
            [sys.executable, str(RUNTIME), mode, str(source)],
            text=True, capture_output=True, check=False,
        )

    def test_source_and_precompiled_execution_match(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / EXAMPLE.name
            source.write_bytes(EXAMPLE.read_bytes())

            source_run = self.invoke("run", source)
            self.assertEqual(source_run.returncode, 0, source_run.stderr)

            compiled = self.invoke("compile", source)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            asset = source.with_suffix(".then")
            self.assertTrue(asset.is_file())
            self.assertEqual(asset.read_bytes()[:8], b"THEBC001")

            asset_run = self.invoke("run", source)
            self.assertEqual(asset_run.returncode, 0, asset_run.stderr)
            self.assertEqual(asset_run.stdout, source_run.stdout)
            self.assertIn("hi there. Let's begin!", asset_run.stdout)
            self.assertIn("[1, 1.7, 2.4, 3.1, 3.8, 4.5]", asset_run.stdout)

            fast_run = subprocess.run(
                [sys.executable, str(LOADER), str(source)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(fast_run.returncode, 0, fast_run.stderr)
            self.assertEqual(fast_run.stdout, source_run.stdout)

            raw_run = subprocess.run(
                [sys.executable, str(LOADER), str(asset)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(raw_run.returncode, 0, raw_run.stderr)
            self.assertEqual(raw_run.stdout, source_run.stdout)

    def test_changed_source_ignores_stale_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / EXAMPLE.name
            source.write_bytes(EXAMPLE.read_bytes())
            self.assertEqual(self.invoke("compile", source).returncode, 0)
            source.write_text(source.read_text(encoding="utf-8").replace("hi there", "hello"), encoding="utf-8")
            result = self.invoke("run", source)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("hello. Let's begin!", result.stdout)

    def test_zero_stride_fails_instead_of_looping_forever(self):
        source_text = """PAGE test
PROC main()
ITER value stridethrough(1, 3, 0)
OUT value
ITEREND
PROCEND
ENTRY main
PAGEEND test
"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "zero.the"
            source.write_text(source_text, encoding="utf-8")

            interpreted = self.invoke("run", source)
            self.assertEqual(interpreted.returncode, 1)
            self.assertIn("stride step cannot be zero", interpreted.stderr)

            self.assertEqual(self.invoke("compile", source).returncode, 0)
            compiled = self.invoke("run", source)
            self.assertEqual(compiled.returncode, 1)
            self.assertIn("stride step cannot be zero", compiled.stderr)

    def test_numeric_workload_lowers_to_native_integer_loop(self):
        source = ROOT / "benchmarks" / "runtime" / "numeric_loop_large.the"
        program = compile_source(source.read_text(encoding="utf-8"), str(source))
        generated = lower_to_c(program)
        self.assertIn("static int64_t _the_main(void)", generated)
        self.assertIn("for (int64_t number", generated)
        self.assertIn("total = total + number", generated)
        self.assertIn('printf("%" PRId64', generated)


if __name__ == "__main__":
    unittest.main()
