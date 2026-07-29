#!/usr/bin/env python3
"""Regression tests for scripts/guard-writes.sh.

Run:  python3 plugins/genesis/tests/test_guard_writes.py

WHAT THIS COVERS, AND WHAT IT CANNOT
------------------------------------
The bug that produced 1.0.1 was Windows-only: under Git Bash/MSYS the project
root arrives POSIX-style (/c/Users/marke) while the tool reports the target as
a native path (C:\\Users\\marke\\project\\file.md). Windows Python resolves the
POSIX form to C:\\c\\Users\\marke without complaint, so nothing in the project
ever matched the root and every write was denied.

Two of the three parts of the fix are testable anywhere:

  1. POSIX behaviour is unchanged by the refactor — covered end-to-end by
     running the real hook (PosixEndToEnd).
  2. The comparison logic is correct under Windows path semantics — covered by
     extracting the hook's python and running it against `ntpath`, which ships
     with CPython on every platform (WindowsSemantics). This is the part that
     actually catches the bug: the pre-fix arrangement is asserted to fail and
     the post-fix arrangement to pass, on macOS or Linux.

  3. That `cygpath` is consulted, and that its absence changes nothing — the
     invocation is covered with a stub (CygpathPlumbing); the stub is an
     identity translation, because a stub performing a REAL POSIX→Windows
     translation would hand C:\\... paths to POSIX python and the test would
     fail for reasons that say nothing about Windows.

NOT COVERED HERE, and not honestly coverable without Windows: that Git for
Windows' actual cygpath produces the strings this guard expects, and that the
MSYS environment presents $PWD/$HOME the way the fix assumes. That end of it
rests on manual testing on a real Windows box — see the 1.0.1 note in
plugins/genesis/README.md. Do not add a test that claims otherwise; a test that
passes on macOS while asserting Windows behaviour would be worse than no test,
because it would retire a risk that is still live.
"""

import contextlib
import io
import json
import ntpath
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

GUARD = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "guard-writes.sh"

# ---------------------------------------------------------------------------
# helpers


def run_guard(target, project=None, env_extra=None, cwd=None, raw_input=None):
    """Run the real hook. Returns parsed deny JSON, or None if it stayed silent."""
    payload = raw_input
    if payload is None:
        payload = json.dumps(
            {"tool_name": "Write", "tool_input": {"file_path": target}}
        )

    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    if project is not None:
        env["CLAUDE_PROJECT_DIR"] = project
    if env_extra:
        env.update(env_extra)

    proc = subprocess.run(
        ["bash", str(GUARD)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def assert_denied(case, result):
    case.assertIsNotNone(result, "expected a deny decision, hook stayed silent")
    decision = result["hookSpecificOutput"]["permissionDecision"]
    case.assertEqual(decision, "deny")


def extract_pathcheck():
    """Pull the decision snippet out of the shell script.

    The hook keeps its python inline so the plugin stays one file per hook with
    no sibling-path resolution to get wrong. Extracting it here is the price of
    that, and the markers exist for this.
    """
    lines = GUARD.read_text().splitlines()
    starts = [i for i, l in enumerate(lines) if l.rstrip().endswith("<<'PY_PATHCHECK'")]
    ends = [i for i, l in enumerate(lines) if l.strip() == "PY_PATHCHECK"]
    assert len(starts) == 1 and len(ends) == 1, "PY_PATHCHECK markers not found"
    return "\n".join(lines[starts[0] + 1 : ends[0]])


PATHCHECK = extract_pathcheck()


def run_pathcheck_as_windows(target, root, home):
    """Run the decision snippet with `os.path` swapped for `ntpath`.

    Inputs are given already-native, i.e. as cygpath would have produced them.
    Returns the parsed deny JSON, or None if it allowed.
    """
    real_path = os.path
    real_argv = sys.argv
    buf = io.StringIO()
    try:
        os.path = ntpath
        sys.argv = ["pathcheck", target, root, home]
        with contextlib.redirect_stdout(buf):
            try:
                exec(compile(PATHCHECK, "guard-writes.sh:PY_PATHCHECK", "exec"), {})
            except SystemExit:
                pass
    finally:
        os.path = real_path
        sys.argv = real_argv
    out = buf.getvalue().strip()
    return json.loads(out) if out else None


# ---------------------------------------------------------------------------


class PosixEndToEnd(unittest.TestCase):
    """The refactor must not change what the hook does on macOS/Linux."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        self.project = os.path.join(self.root, "project")
        os.makedirs(os.path.join(self.project, "docs"))
        self.addCleanup(self.tmp.cleanup)

    def test_in_project_allowed(self):
        self.assertIsNone(
            run_guard(os.path.join(self.project, "docs", "notes.md"), self.project)
        )

    def test_project_root_itself_allowed(self):
        self.assertIsNone(run_guard(self.project, self.project))

    def test_outside_project_denied(self):
        result = run_guard(os.path.join(self.root, "elsewhere.txt"), self.project)
        assert_denied(self, result)
        self.assertIn(
            "outside the project directory",
            result["hookSpecificOutput"]["permissionDecisionReason"],
        )

    def test_sibling_with_shared_prefix_denied(self):
        """`/x/project-evil` must not match root `/x/project` on a bare prefix."""
        assert_denied(
            self, run_guard(os.path.join(self.root, "project-evil", "x"), self.project)
        )

    def test_parent_traversal_denied(self):
        assert_denied(
            self, run_guard(os.path.join(self.project, "..", "escaped.txt"), self.project)
        )

    def test_home_claude_allowed(self):
        home = os.path.join(self.root, "home")
        os.makedirs(os.path.join(home, ".claude"))
        self.assertIsNone(
            run_guard(
                os.path.join(home, ".claude", "settings.json"),
                self.project,
                env_extra={"HOME": home},
            )
        )

    def test_home_sibling_of_claude_denied(self):
        home = os.path.join(self.root, "home")
        os.makedirs(home, exist_ok=True)
        assert_denied(
            self,
            run_guard(
                os.path.join(home, ".claude-backup", "x"),
                self.project,
                env_extra={"HOME": home},
            ),
        )

    def test_falls_back_to_pwd_when_project_dir_unset(self):
        self.assertIsNone(
            run_guard(os.path.join(self.project, "notes.md"), None, cwd=self.project)
        )

    def test_relative_target_resolved_against_cwd(self):
        self.assertIsNone(run_guard("docs/notes.md", self.project, cwd=self.project))

    def test_no_path_in_payload_is_silent(self):
        self.assertIsNone(
            run_guard(
                None,
                self.project,
                raw_input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}),
            )
        )

    def test_notebook_path_is_checked(self):
        payload = json.dumps(
            {
                "tool_name": "NotebookEdit",
                "tool_input": {"notebook_path": os.path.join(self.root, "out.ipynb")},
            }
        )
        assert_denied(self, run_guard(None, self.project, raw_input=payload))

    def test_malformed_payload_fails_open(self):
        self.assertIsNone(run_guard(None, self.project, raw_input="{not json"))


class CygpathPlumbing(unittest.TestCase):
    """cygpath is consulted when present; its absence changes nothing."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        self.project = os.path.join(self.root, "project")
        os.makedirs(self.project)
        self.bindir = os.path.join(self.root, "bin")
        os.makedirs(self.bindir)
        self.log = os.path.join(self.root, "cygpath.log")
        stub = os.path.join(self.bindir, "cygpath")
        # Identity translation. A stub doing a real POSIX->Windows conversion
        # would feed C:\ paths to POSIX python and prove nothing about Windows.
        with open(stub, "w") as fh:
            fh.write(
                "#!/bin/sh\n"
                f'printf "%s\\n" "$*" >> "{self.log}"\n'
                'shift\n'
                'printf "%s" "$1"\n'
            )
        os.chmod(stub, 0o755)
        self.env = {"PATH": self.bindir + os.pathsep + os.environ.get("PATH", "")}
        self.addCleanup(self.tmp.cleanup)

    def calls(self):
        with open(self.log) as fh:
            return [l for l in fh.read().splitlines() if l.strip()]

    def test_cygpath_is_invoked_for_target_root_and_home(self):
        run_guard(os.path.join(self.project, "a.md"), self.project, env_extra=self.env)
        calls = self.calls()
        self.assertEqual(len(calls), 3, f"expected target/root/home, got {calls}")
        self.assertTrue(all(c.startswith("-w ") for c in calls), calls)

    def test_decisions_unchanged_when_cygpath_present(self):
        self.assertIsNone(
            run_guard(os.path.join(self.project, "a.md"), self.project, env_extra=self.env)
        )
        assert_denied(
            self,
            run_guard(os.path.join(self.root, "outside.md"), self.project, env_extra=self.env),
        )

    def test_cygpath_failure_does_not_break_the_guard(self):
        """A cygpath that errors must not turn every write into a deny."""
        with open(os.path.join(self.bindir, "cygpath"), "w") as fh:
            fh.write("#!/bin/sh\nexit 1\n")
        os.chmod(os.path.join(self.bindir, "cygpath"), 0o755)
        self.assertIsNone(
            run_guard(os.path.join(self.project, "a.md"), self.project, env_extra=self.env)
        )


class WindowsSemantics(unittest.TestCase):
    """The comparison logic under Windows path rules, via ntpath.

    Inputs are post-cygpath, i.e. native. This is where the 1.0.1 bug lives.
    """

    ROOT = r"C:\Users\marke\alan"
    HOME = r"C:\Users\marke"

    def test_in_project_allowed(self):
        self.assertIsNone(
            run_pathcheck_as_windows(r"C:\Users\marke\alan\docs\notes.md", self.ROOT, self.HOME)
        )

    def test_case_differences_do_not_matter(self):
        """normcase is the reason one comparison works on both platforms."""
        self.assertIsNone(
            run_pathcheck_as_windows(
                r"c:\users\MARKE\Alan\Docs\notes.md", r"C:\Users\Marke\alan", self.HOME
            )
        )

    def test_forward_slashes_in_target_allowed(self):
        self.assertIsNone(
            run_pathcheck_as_windows("C:/Users/marke/alan/notes.md", self.ROOT, self.HOME)
        )

    def test_outside_project_denied(self):
        assert_denied(
            self, run_pathcheck_as_windows(r"C:\Windows\Temp\x.txt", self.ROOT, self.HOME)
        )

    def test_sibling_with_shared_prefix_denied(self):
        assert_denied(
            self, run_pathcheck_as_windows(r"C:\Users\marke\alan-evil\x", self.ROOT, self.HOME)
        )

    def test_home_claude_allowed(self):
        self.assertIsNone(
            run_pathcheck_as_windows(
                r"C:\Users\marke\.claude\settings.json", self.ROOT, self.HOME
            )
        )

    def test_the_1_0_1_bug_reproduces_without_normalisation(self):
        """An unnormalised POSIX root denies an in-project write.

        This is the failure the first external bug report described, asserted
        directly: root as MSYS hands it over, target as the tool reports it.
        If this ever stops denying, the premise behind cygpath normalisation
        has changed and the fix should be revisited.
        """
        assert_denied(
            self,
            run_pathcheck_as_windows(
                r"C:\Users\marke\alan\docs\notes.md", "/c/Users/marke/alan", self.HOME
            ),
        )

    def test_normalisation_is_what_repairs_it(self):
        """Same case, root translated as cygpath -w would translate it."""
        self.assertIsNone(
            run_pathcheck_as_windows(
                r"C:\Users\marke\alan\docs\notes.md", r"C:\Users\marke\alan", self.HOME
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
