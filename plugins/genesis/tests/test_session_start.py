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

Constraint 2 was relaxed exactly once, in 1.0.5, for the one-line prior-art
notice — which fires whether or not state files exist, because a mature project
that has never checked the field is the case that most needs it. The test was
not deleted: it now requires that removing that ONE line reproduces the baseline
byte for byte. The guarantee it was protecting (nothing else drifted into every
session's context) still holds, and the exemption is bounded to a single line by
the assertion rather than by anyone's intention.
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
        self.assertEqual(len(block), 4)
        self.assertTrue(block[0].startswith("state: no STATE.md"))
        self.assertTrue(block[1].startswith("gate: no .claude/verify.sh"))
        self.assertTrue(block[2].startswith("prior-art: none recorded"))
        self.assertIn(f"project root is {self.root} (no git repository here)", block[3])

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

    def test_output_identical_to_previous_version_but_for_the_prior_art_line(self):
        """The hard requirement, checked against the pre-1.0.2 script itself.

        Asserting on a stored snapshot would drift with the file it is meant to
        pin. Running the old version side by side does not.

        ONE deliberate exemption, added in 1.0.5: the prior-art notice. Deleting
        that single line from the new output must reproduce the baseline exactly
        — so the exemption cannot quietly widen into a second line, or into a
        change anywhere else in the injected text.

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

        current = run_hook(project)
        exempt = [l for l in current.splitlines() if l.startswith("prior-art: ")]
        self.assertEqual(len(exempt), 1, f"expected exactly one exempt line: {exempt}")

        # Removed with its own trailing blank, and only once: a string edit
        # rather than a line filter, so the surrounding text cannot be
        # reflowed by the removal and pass on a technicality.
        stripped = current.replace(exempt[0] + "\n\n", "", 1)
        self.assertNotEqual(stripped, current, "exempt line not removed")

        self.assertEqual(
            run_hook(project, script=old),
            stripped,
            "output changed for a project that has state files, beyond the one "
            "exempt line",
        )


class PriorArtLine(unittest.TestCase):
    """The 1.0.5 notice: one line, both branches, silent once acted on.

    The off switch is the point. It requires no configuration — recording the
    pass in the durable state, which is what the skill's step 4 asks for, is
    what stops the line. A setting or a marker file would be a preference
    someone has to remember.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def lines(self, output):
        return [l for l in output.splitlines() if l.startswith("prior-art: ")]

    def write_state(self, body):
        with open(os.path.join(self.root, "STATE.md"), "w") as fh:
            fh.write(body)

    def test_fires_with_no_state_at_all(self):
        self.assertEqual(len(self.lines(run_hook(self.root))), 1)

    def test_fires_when_state_exists_but_records_no_pass(self):
        """The mature project — the case the notice exists for."""
        self.write_state("# state\nshipping the parser rewrite\n")
        self.assertEqual(len(self.lines(run_hook(self.root))), 1)

    def test_silent_when_the_state_records_a_pass(self):
        for body in (
            "# state\nprior art: searched and did not find\n",
            "# state\nPrior-Art pass done for the scheduler\n",
            "# state\nPRIOR ART: exists — RFC 6455\n",
        ):
            with self.subTest(body=body):
                self.write_state(body)
                self.assertEqual(self.lines(run_hook(self.root)), [])

    def test_silent_when_any_recognised_state_file_records_a_pass(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "docs"))
        with open(os.path.join(d, "STATE.md"), "w") as fh:
            fh.write("# state\nin progress\n")
        with open(os.path.join(d, "docs", "HANDOFF.md"), "w") as fh:
            fh.write("prior-art pass recorded for the retry policy\n")
        self.assertEqual(self.lines(run_hook(d)), [])

    def test_never_more_than_one_line(self):
        """It is emitted from two branches; only one may ever reach context."""
        for setup in (lambda: None, lambda: self.write_state("# state\nx\n")):
            with self.subTest(setup=setup):
                setup()
                self.assertLessEqual(len(self.lines(run_hook(self.root))), 1)

    def test_names_the_skill_and_claims_only_what_is_checked(self):
        line = self.lines(run_hook(self.root))[0]
        self.assertIn("/genesis:prior-art", line)
        self.assertIn("none recorded in this project's state", line)
        # It must not assert a fact about the project's history that the hook
        # has no way to establish.
        self.assertNotIn("never", line)


if __name__ == "__main__":
    unittest.main(verbosity=2)
