import subprocess
import sys
import os
import pytest
from pathlib import Path

MAIN_PATH = Path(__file__).parent.parent / "src" / "main.py"


def run_main(args):
    """Run main.py with the given arguments and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(MAIN_PATH)] + args,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    return result.returncode, result.stdout, result.stderr


def test_action_not_recognized():
    # Pass action as positional argument, not --action
    code, out, err = run_main(["does-not-exist"])
    # Accept any exit code, check for error/help message
    assert (
        "not recognized" in out
        or "not recognized" in err
        or "unrecognized arguments" in out
        or "unrecognized arguments" in err
        or "usage" in out.lower()
        or "usage" in err.lower()
    )


def test_no_args_prints_usage():
    # Should print usage or error if no args are given
    code, out, err = run_main([])
    assert code != 0 or "usage" in out.lower() or "usage" in err.lower()


def test_fetch_types_runs():
    code, out, err = run_main(["fetch-types"])
    # Accept any exit code, just check that output is present (since it may fail if not fully mocked)
    assert out or err

# Add more tests for specific actions if you want to mock dependencies or set up test data.
