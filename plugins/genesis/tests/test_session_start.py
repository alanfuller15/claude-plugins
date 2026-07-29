#!/usr/bin/env python3
"""Regression tests for scripts/session-start.sh.

Run:  python3 plugins/genesis/tests/test_session_start.py

The first-run block added in 1.0.2 exists because with nothing configured this
hook emitted git state and stopped, which reads as "installed something,
nothing happened". Every no-op was correct; none was legible.

Two constraints on it are hard, and both are load-bearing enough to test rather
than trust:

  1. AT MOST FOUR LINES, and only when no state file was found. This text
     enters context every session.
  2. When state files DO exist, output is byte-identical to what the hook
     produced before the block existed. That one is checked by running the
     previous committed version of the script side by side, rather than by
     asserting on a snapshot that could drift with it.
"""

import os
import pathlib
import subprocess
import tempfile
import unittest

HOOK = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "session-start.sh"
REPO = HOOK.parent.parent.parent.parent


def run_hook(project, script=None):
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = project
    proc = subprocess.run(
        ["bash", str(script or HOOK)],
        capture_output=True, text=True, env=env, cwd=project,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return proc.stdout


def genesis_block(output):
    """The lines of the first-run block, without its header or trailing blank."""
    lines = output.splitlines()
    if "## genesis" not in lines:
        return None
    start = lines.index("## genesis")
    out = []
    for line in lines[start + 1:]:
        if not line.strip():
            break
        out.append(line)
    return out


def git_init(path):
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, capture_output=True)


class FirstRunBlock(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_empty_non_repo_project(self):
        """The reported case: nothing configured, no repository."""
        block = genesis_block(run_hook(self.root))
        self.assertIsNotNone(block, "first-run block missing")
        self.assertEqual(len(block), 3)
        self.assertTrue(block[0].startswith("state: no STATE.md"))
        self.assertTrue(block[1].startswith("gate: no .claude/verify.sh"))
        self.assertIn(f"project root is {self.root} (no git repository here)", block[2])

    def test_at_most_four_lines(self):
        """The hard limit, asserted directly rather than assumed."""
        git_init(self.root)
        block = genesis_block(run_hook(self.root))
        self.assertLessEqual(len(block), 4, f"block grew past its ceiling: {block}")

    def test_gate_line_absent_when_gate_exists(self):
        os.makedirs(os.path.join(self.root, ".claude"))
        with open(os.path.join(self.root, ".claude", "verify.sh"), "w") as fh:
            fh.write("#!/usr/bin/env bash\nexit 0\n")
        block = genesis_block(run_hook(self.root))
        self.assertFalse(any(l.startswith("gate:") for l in block), block)
        self.assertTrue(any("write guard active" in l for l in block), block)

    # --- the three git states on the root line ---

    def test_repository_root(self):
        git_init(self.root)
        block = genesis_block(run_hook(self.root))
        self.assertIn(f"project root is {self.root} (git repository root)", block[-1])

    def test_inside_repository(self):
        """The misaimed root: a real repo, but the session is rooted below it."""
        git_init(self.root)
        sub = os.path.join(self.root, "plugins", "genesis")
        os.makedirs(sub)
        block = genesis_block(run_hook(sub))
        self.assertIn(
            f"project root is {sub} (inside repository {self.root})", block[-1]
        )

    def test_no_repository(self):
        block = genesis_block(run_hook(self.root))
        self.assertIn("(no git repository here)", block[-1])


class StateFilesPresent(unittest.TestCase):
    """When state exists, the block must not appear at all."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_block_absent_when_state_file_exists(self):
        with open(os.path.join(self.root, "STATE.md"), "w") as fh:
            fh.write("# state\nin progress\n")
        self.assertIsNone(genesis_block(run_hook(self.root)))

    def test_block_absent_for_every_recognised_state_file(self):
        for name in ("STATE.md", "docs/STATE.md", "HANDOFF.md", "docs/HANDOFF.md"):
            with self.subTest(name=name):
                d = tempfile.mkdtemp()
                os.makedirs(os.path.join(d, os.path.dirname(name)), exist_ok=True)
                with open(os.path.join(d, name), "w") as fh:
                    fh.write("x\n")
                self.assertIsNone(genesis_block(run_hook(d)), name)

    def test_output_identical_to_previous_version(self):
        """The hard requirement, checked against the pre-1.0.2 script itself.

        Asserting on a stored snapshot would drift with the file it is meant to
        pin. Running the old version side by side does not.

        PINNED TO A COMMIT, not to HEAD. `HEAD` was the obvious spelling and it
        is a trap: the first commit containing this test makes HEAD the *new*
        script, so the test would compare the new version against itself and
        pass for all time without checking anything.
        """
        BASELINE = "a84fb3f"  # last commit before the first-run block existed
        prev = subprocess.run(
            ["git", "show", f"{BASELINE}:plugins/genesis/scripts/session-start.sh"],
            cwd=REPO, capture_output=True, text=True,
        )
        if prev.returncode != 0:
            self.skipTest(f"baseline {BASELINE} unavailable (shallow or non-git tree)")
        self.assertNotIn("## genesis", prev.stdout, "baseline already has the block")

        old = os.path.join(self.root, "old-session-start.sh")
        with open(old, "w") as fh:
            fh.write(prev.stdout)

        project = os.path.join(self.root, "proj")
        os.makedirs(project)
        git_init(project)
        with open(os.path.join(project, "STATE.md"), "w") as fh:
            fh.write("# state\nin progress\n")

        self.assertEqual(
            run_hook(project, script=old),
            run_hook(project),
            "output changed for a project that has state files",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
