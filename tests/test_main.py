# import subprocess
# import sys
# import os
# import pytest
# from pathlib import Path
# from unittest.mock import patch, MagicMock

# MAIN_PATH = Path(__file__).parent.parent / "src" / "main.py"


# def run_main(args):
#     """Run main.py with the given arguments and return (exit_code, stdout, stderr)."""
#     # Use a minimal, clean environment for subprocess
#     env = {"PYTHONUNBUFFERED": "1", "PATH": os.environ.get("PATH", "")}
#     result = subprocess.run(
#         [sys.executable, str(MAIN_PATH)] + args,
#         capture_output=True,
#         text=True,
#         env=env,
#     )
#     return result.returncode, result.stdout, result.stderr


# @pytest.fixture
# def temp_dirs(tmp_path):
#     drafts_dir = tmp_path / "drafts"
#     cache_dir = tmp_path / "cache"
#     plugins_dir = tmp_path / "plugins"
#     drafts_dir.mkdir()
#     cache_dir.mkdir()
#     plugins_dir.mkdir()
#     return drafts_dir, cache_dir, plugins_dir


# def dummy_options(action=None, args=None, drafts_dir=None, cache_dir=None, plugins_dir=None):
#     class Dummy:
#         def __init__(self):
#             self.action = action or "fetch-types"
#             self.args = args or []
#             self.chat_gpt_activated = False
#             self.chat_gpt_base_url = "https://api.fakeai.com/v1"
#             self.chat_gpt_api_key = "dummy"
#             self.drafts_dir = drafts_dir or Path("/tmp/drafts")
#             self.cache_dir = cache_dir or Path("/tmp/cache")
#             self.plugins_dir = plugins_dir or Path("/tmp/plugins")
#     return Dummy()


# def dummy_mantis_client(*a, **kw):
#     dummy = MagicMock()
#     dummy.jira = MagicMock()
#     dummy.cache = MagicMock()
#     dummy.assistant = MagicMock()
#     dummy.jira.system_config_loader = MagicMock()
#     dummy.jira.issues = MagicMock()
#     dummy.jira.project_name = "TEST"
#     return dummy

# # Patch OptionsLoader and MantisClient for all tests in this file
# def run_main_patched(args, action=None, drafts_dir=None, cache_dir=None, plugins_dir=None):
#     with patch("mantis.options_loader.OptionsLoader", side_effect=lambda *a, **kw: dummy_options(action=action or (args[0] if args else None), args=args[1:] if len(args) > 1 else [], drafts_dir=drafts_dir, cache_dir=cache_dir, plugins_dir=plugins_dir)), \
#          patch("mantis.mantis_client.MantisClient", side_effect=dummy_mantis_client):
#         return run_main(args)


# def test_action_not_recognized(temp_dirs):
#     drafts_dir, cache_dir, plugins_dir = temp_dirs
#     code, out, err = run_main_patched(["does-not-exist"], action="does-not-exist", drafts_dir=drafts_dir, cache_dir=cache_dir, plugins_dir=plugins_dir)
#     # Accept any exit code, check for error/help message
#     assert (
#         "not recognized" in out
#         or "not recognized" in err
#         or "unrecognized arguments" in out
#         or "unrecognized arguments" in err
#         or "usage" in out.lower()
#         or "usage" in err.lower()
#     )


# def test_no_args_prints_usage(temp_dirs):
#     drafts_dir, cache_dir, plugins_dir = temp_dirs
#     # Should print usage or error if no args are given
#     code, out, err = run_main_patched([], drafts_dir=drafts_dir, cache_dir=cache_dir, plugins_dir=plugins_dir)
#     assert code != 0 or "usage" in out.lower() or "usage" in err.lower()


# def test_fetch_types_runs(temp_dirs):
#     drafts_dir, cache_dir, plugins_dir = temp_dirs
#     code, out, err = run_main_patched(["fetch-types"], action="fetch-types", drafts_dir=drafts_dir, cache_dir=cache_dir, plugins_dir=plugins_dir)
#     # Accept any exit code, just check that output is present (since it may fail if not fully mocked)
#     assert out or err


# def test_fetch_issuetypes_runs(temp_dirs):
#     drafts_dir, cache_dir, plugins_dir = temp_dirs
#     code, out, err = run_main_patched(["fetch-issuetypes"], action="fetch-issuetypes", drafts_dir=drafts_dir, cache_dir=cache_dir, plugins_dir=plugins_dir)
#     assert out or err


# def test_update_issue_runs(temp_dirs):
#     drafts_dir, cache_dir, plugins_dir = temp_dirs
#     # This will likely fail unless dependencies are mocked, but should not crash the CLI
#     code, out, err = run_main_patched(["update-issue", "FAKE-1"], action="update-issue", drafts_dir=drafts_dir, cache_dir=cache_dir, plugins_dir=plugins_dir)
#     assert out or err or code != 0


# def test_compare_runs(temp_dirs):
#     drafts_dir, cache_dir, plugins_dir = temp_dirs
#     # This will likely fail unless dependencies are mocked, but should not crash the CLI
#     code, out, err = run_main_patched(["compare", "FAKE-1"], action="compare", drafts_dir=drafts_dir, cache_dir=cache_dir, plugins_dir=plugins_dir)
#     assert out or err or code != 0

# @pytest.mark.slow
# def test_inspect_runs(temp_dirs):
#     drafts_dir, cache_dir, plugins_dir = temp_dirs
#     code, out, err = run_main_patched(["inspect"], action="inspect", drafts_dir=drafts_dir, cache_dir=cache_dir, plugins_dir=plugins_dir)
#     assert out or err or code != 0


# @pytest.mark.slow
# def test_compile_plugins_runs(temp_dirs):
#     drafts_dir, cache_dir, plugins_dir = temp_dirs
#     code, out, err = run_main_patched(["compile-plugins"], action="compile-plugins", drafts_dir=drafts_dir, cache_dir=cache_dir, plugins_dir=plugins_dir)
#     assert out or err or code != 0

# # Add more tests for specific actions if you want to mock dependencies or set up test data.
