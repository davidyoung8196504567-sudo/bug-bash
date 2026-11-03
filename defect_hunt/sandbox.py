"""Run a test file against one implementation in an isolated temp directory.

Phase 0: plain subprocess + timeout. Phase 2 replaces this with a Docker
container (no network, read-only filesystem, CPU/memory limits).
"""
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

TIMEOUT_SECONDS = 30


@dataclass
class RunResult:
    passed: bool
    timed_out: bool
    output: str


def run_tests(impl_source: str, test_source: str, timeout: int = TIMEOUT_SECONDS) -> RunResult:
    """Write impl as impl.py and tests as test_candidate.py, run pytest."""
    with tempfile.TemporaryDirectory(prefix="defect_hunt_") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "impl.py").write_text(impl_source, encoding="utf-8")
        (tmp_path / "test_candidate.py").write_text(test_source, encoding="utf-8")
        cmd = [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider",
               "test_candidate.py"]
        try:
            proc = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True,
                                  timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            return RunResult(passed=False, timed_out=True, output=str(exc))
        # pytest exit codes: 0 = all passed, 1 = failures, 5 = no tests collected
        return RunResult(passed=proc.returncode == 0, timed_out=False,
                         output=proc.stdout + proc.stderr)
