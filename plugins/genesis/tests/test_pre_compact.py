#!/usr/bin/env python3
r"""Regression tests for scripts/pre-compact.sh.

Run:  python3 plugins/genesis/tests/test_pre_compact.py

WHAT THIS COVERS
----------------
The 1.0.8 fix. A PreCompact hook can block compaction by exiting 2 — verified by
documentation and by an observed test before the fix was written; see the
Resolutions section of docs/PRIOR-ART.md. Until 1.0.8 this hook never used that:
every failure path was exit 0, so a failed snapshot let the summary proceed as
the only record of the session, silently.

The fix is deliberately narrow, and BOTH halves of that need testing, because
they fail in opposite directions:

  1. A transcript existed and its copy failed  ->  block (exit 2) and say so.
  2. Everything else                            ->  proceed (exit 0).

Half 2 is the half a naive suite would miss. A hook that blocked on every
failure would pass any test that only checked "does it block when cp fails",
while giving a user with an unwritable .genesis/ a session that can never
compact. So the no-transcript, missing-file and unwritable-project cases are
asserted to PROCEED, and that is not incidental coverage — it is the pin on the
scope.

TWO WAYS OF FAILING A COPY, on purpose:

  - a `cp` stub earlier on PATH that exits non-zero (CopyFailureViaStub). This is
    the CygpathPlumbing idiom from test_guard_writes.py: deterministic, and it
    works regardless of who is running the suite.
  - a real unreadable source file (CopyFailureForReal). Closer to the world, but
    it establishes nothing when run as root, so it skips there rather than
    passing vacuously.

MUTANTS
-------
Following test_guard_writes.py's `test_the_1_0_1_bug_reproduces_without_
normalisation`, which asserts that the PRE-FIX arrangement fails. A test that
would also pass against the broken script retires a risk that is still live, so
each mutant below breaks the fix in one specific way and asserts the behaviour
changes. If a mutant ever stops changing the outcome, the assertion above it has
stopped being load-bearing.

NOT COVERED HERE: that Claude Code honours exit 2 at PreCompact. That is a fact
about the harness, not about this script, and no test in this repo can establish
it. It rests on the fetched exit-code table and the recorded observation in
docs/PRIOR-ART.md. Do not add a test that appears to cover it.
"""

import json
import os
import pathlib
import re
import stat
import subprocess
import tempfile
import unittest

HOOK = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "pre-compact.sh"


# ---------------------------------------------------------------------------
# helpers


def run_hook(project, transcript=None, trigger="manual", env_extra=None,
             script=None, raw_input=None):
    """Run the hook. Returns the CompletedProcess; callers assert on returncode."""
    if raw_input is None:
        payload = {"trigger": trigger}
        if transcript is not None:
            payload["transcript_path"] = transcript
        raw_input = json.dumps(payload)

    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = project
    if env_extra:
        env.update(env_extra)

    return subprocess.run(
        ["bash", str(script or HOOK)],
        input=raw_input, capture_output=True, text=True, env=env, cwd=project,
    )


def write_transcript(path, lines=3):
    with open(path, "w") as fh:
        for i in range(lines):
            fh.write(json.dumps({"type": "user", "seq": i}) + "\n")
    return path


def snapshots(project):
    """Every transcript.jsonl under .genesis/backups/."""
    root = os.path.join(project, ".genesis", "backups")
    if not os.path.isdir(root):
        return []
    return [
        os.path.join(root, d, "transcript.jsonl")
        for d in sorted(os.listdir(root))
        if os.path.isfile(os.path.join(root, d, "transcript.jsonl"))
    ]


def cp_stub(bindir, body):
    """Put a `cp` earlier on PATH than the real one."""
    os.makedirs(bindir, exist_ok=True)
    path = os.path.join(bindir, "cp")
    with open(path, "w") as fh:
        fh.write(body)
    os.chmod(path, 0o755)
    return {"PATH": bindir + os.pathsep + os.environ.get("PATH", "")}


def mutate(tmpdir, name, pattern, replacement, count=1):
    """Write a copy of the hook with one substitution applied.

    Asserts the substitution actually landed. A mutant that silently failed to
    apply would be a test that passes because nothing changed.

    The replacement goes through a lambda so that `$` and `\\` in shell text are
    never read as regex replacement syntax.
    """
    src = HOOK.read_text()
    out, n = re.subn(pattern, lambda _m: replacement, src, count=count)
    assert n == count, f"mutant {name!r} did not apply ({n} of {count} matches)"
    path = os.path.join(tmpdir, f"mutant-{name}.sh")
    with open(path, "w") as fh:
        fh.write(out)
    return path


class HookCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        self.project = os.path.join(self.root, "project")
        os.makedirs(self.project)
        self.transcript = write_transcript(os.path.join(self.root, "transcript.jsonl"))
        self.addCleanup(self.tmp.cleanup)


# ---------------------------------------------------------------------------


class HappyPath(HookCase):
    """A copy that succeeds must not block, and must actually copy."""

    def test_exits_zero_and_writes_the_snapshot(self):
        proc = run_hook(self.project, self.transcript)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        found = snapshots(self.project)
        self.assertEqual(len(found), 1, f"expected one snapshot, got {found}")
        with open(found[0]) as snap, open(self.transcript) as src:
            self.assertEqual(snap.read(), src.read())

    def test_says_nothing_on_success(self):
        """A hook that narrates every success is noise on every compaction."""
        self.assertEqual(run_hook(self.project, self.transcript).stderr, "")

    def test_trigger_names_the_snapshot_directory(self):
        run_hook(self.project, self.transcript, trigger="auto")
        found = snapshots(self.project)
        self.assertTrue(found[0].endswith("-auto/transcript.jsonl"), found)

    def test_durable_state_is_snapshotted_alongside(self):
        with open(os.path.join(self.project, "STATE.md"), "w") as fh:
            fh.write("# state\n")
        run_hook(self.project, self.transcript)
        d = os.path.dirname(snapshots(self.project)[0])
        self.assertTrue(os.path.isfile(os.path.join(d, "STATE.md")))


class ProceedsWithoutBlocking(HookCase):
    """The half a naive suite would miss.

    Each of these is a failure the hook must NOT block on. If any starts
    blocking, a user hits a session that cannot compact for a reason that never
    lost anything.
    """

    def test_no_transcript_path_in_payload(self):
        proc = run_hook(self.project, transcript=None)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(snapshots(self.project), [])

    def test_transcript_path_that_does_not_exist(self):
        missing = os.path.join(self.root, "gone.jsonl")
        proc = run_hook(self.project, missing)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(snapshots(self.project), [])

    def test_malformed_payload_fails_open(self):
        proc = run_hook(self.project, raw_input="{not json")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_empty_payload_fails_open(self):
        proc = run_hook(self.project, raw_input="")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_unwritable_project_does_not_block(self):
        """mkdir fails, so no snapshot is possible at all — and it still proceeds.

        This is the full-disk shape, and the reason the scope stops at cp: a hook
        that blocked here would leave the session permanently uncompactable.
        """
        if os.geteuid() == 0:
            self.skipTest("running as root: a read-only directory does not deny")
        locked = os.path.join(self.root, "locked")
        os.makedirs(locked)
        os.chmod(locked, stat.S_IRUSR | stat.S_IXUSR)
        self.addCleanup(os.chmod, locked, 0o755)
        proc = run_hook(locked, self.transcript)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class CopyFailureViaStub(HookCase):
    """The blocking path, forced deterministically with a cp stub."""

    def setUp(self):
        super().setUp()
        self.env = cp_stub(
            os.path.join(self.root, "bin"),
            '#!/bin/sh\necho "cp: fake failure: No space left on device" >&2\nexit 1\n',
        )

    def result(self):
        return run_hook(self.project, self.transcript, env_extra=self.env)

    def test_blocks_with_exit_two(self):
        self.assertEqual(self.result().returncode, 2)

    def test_message_says_what_was_expected_and_did_not_happen(self):
        err = self.result().stderr
        self.assertIn("COMPACTION BLOCKED", err)
        self.assertIn("transcript snapshot failed", err)
        self.assertIn("was expected at", err)
        self.assertIn("the copy did not succeed", err)

    def test_message_names_both_paths_and_the_underlying_error(self):
        err = self.result().stderr
        self.assertIn(self.transcript, err)
        self.assertIn("transcript.jsonl", err)
        self.assertIn("No space left on device", err)

    def test_message_explains_why_blocking_rather_than_proceeding(self):
        err = self.result().stderr
        self.assertIn("lossy", err)
        self.assertIn("only record", err)

    def test_message_names_the_way_out(self):
        """The andon finding: a halt that does not say how to clear it is worse
        than the graduated version. This hook has no time-box, so the message
        carries the escalation instead."""
        err = self.result().stderr
        self.assertIn("Fix the cause and compact again", err)
        self.assertIn("disk space", err)
        self.assertIn("/plugin disable genesis", err)

    def test_message_is_explicit_that_skip_verify_does_not_apply(self):
        """The plugin has one skip file and it is for a different hook. A reader
        who tries it and finds it ignored is worse off than one who was told."""
        err = self.result().stderr
        self.assertIn("NO SKIP FILE", err)
        self.assertIn(".genesis/skip-verify", err)

    def test_stdout_stays_clean(self):
        """PreCompact stdout is not a context channel; the message goes to stderr."""
        self.assertEqual(self.result().stdout, "")


class CopyFailureForReal(HookCase):
    """The same block, provoked by a genuinely unreadable source file."""

    def test_unreadable_transcript_blocks(self):
        if os.geteuid() == 0:
            self.skipTest("running as root: mode 000 does not deny")
        os.chmod(self.transcript, 0)
        self.addCleanup(os.chmod, self.transcript, 0o644)
        proc = run_hook(self.project, self.transcript)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("COMPACTION BLOCKED", proc.stderr)

    def test_no_partial_snapshot_is_left_claiming_success(self):
        """A half-written file would be worse than none: it looks like a record."""
        if os.geteuid() == 0:
            self.skipTest("running as root: mode 000 does not deny")
        os.chmod(self.transcript, 0)
        self.addCleanup(os.chmod, self.transcript, 0o644)
        run_hook(self.project, self.transcript)
        for snap in snapshots(self.project):
            self.assertGreater(os.path.getsize(snap), 0, f"empty snapshot: {snap}")


class Mutants(HookCase):
    """Negative controls: break the fix, assert the behaviour changes.

    Each mutant targets one assertion in the classes above. These are what
    establish that this suite would catch the regression rather than passing
    because the outcome never depended on the fix.
    """

    def setUp(self):
        super().setUp()
        self.failing_cp = cp_stub(
            os.path.join(self.root, "bin"),
            '#!/bin/sh\necho "cp: fake failure" >&2\nexit 1\n',
        )

    def test_mutant_discarding_cp_status_stops_blocking(self):
        """The defect as it shipped from 1.0.0 to 1.0.7: cp runs, status ignored.

        `&& false` is appended to the condition rather than the cp being removed,
        so the mutant still performs the copy attempt and differs from the fix in
        exactly one respect — whether the exit status is acted on. If this mutant
        ever exits 2, the block is coming from somewhere other than the status
        check and CopyFailureViaStub is testing the wrong thing.
        """
        mutant = mutate(
            self.root, "swallow",
            r'if ! CP_ERR=\$\(cp "\$TRANSCRIPT" "\$DEST/transcript\.jsonl" 2>&1\); then',
            'if ! CP_ERR=$(cp "$TRANSCRIPT" "$DEST/transcript.jsonl" 2>&1) && false; then',
        )
        proc = run_hook(self.project, self.transcript,
                        env_extra=self.failing_cp, script=mutant)
        self.assertEqual(proc.returncode, 0,
                         "mutant still blocked: the status check is not what blocks")
        self.assertEqual(proc.stderr, "")

    def test_mutant_exiting_zero_instead_of_two_stops_blocking(self):
        """Pins the exit code specifically. Only 2 blocks at PreCompact; a hook
        that printed this message and exited 0 would look correct in a transcript
        and protect nothing."""
        mutant = mutate(self.root, "exit-zero", r"\n    exit 2\n", "\n    exit 0\n")
        proc = run_hook(self.project, self.transcript,
                        env_extra=self.failing_cp, script=mutant)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("COMPACTION BLOCKED", proc.stderr,
                      "mutant changed more than the exit code")

    def test_mutant_dropping_the_existence_guard_over_blocks(self):
        """Widen the scope by one condition and the narrowness breaks.

        Without `[ -f "$TRANSCRIPT" ]`, a payload with no usable transcript
        reaches cp and fails, so the hook blocks a compaction that lost nothing.
        This is the mutant that makes ProceedsWithoutBlocking load-bearing.
        """
        mutant = mutate(
            self.root, "no-existence-guard",
            r'if \[ "\$TRANSCRIPT" != "-" \] && \[ -f "\$TRANSCRIPT" \]; then',
            'if true; then',
        )
        missing = os.path.join(self.root, "gone.jsonl")
        self.assertEqual(run_hook(self.project, missing).returncode, 0,
                         "unmutated hook already blocks on a missing transcript")
        self.assertEqual(
            run_hook(self.project, missing, script=mutant).returncode, 2,
            "mutant did not over-block: the existence guard is not what prevents it",
        )

    def test_mutant_blocking_on_mkdir_makes_the_session_uncompactable(self):
        """The failure mode the scope exists to avoid, demonstrated.

        With `|| exit 2` on the backup mkdir, an unwritable project blocks every
        compaction forever — nothing the user does inside the session clears it.
        """
        if os.geteuid() == 0:
            self.skipTest("running as root: a read-only directory does not deny")
        mutant = mutate(
            self.root, "mkdir-blocks",
            r'mkdir -p "\$BACKUP_DIR" \|\| exit 0',
            'mkdir -p "$BACKUP_DIR" || exit 2',
        )
        locked = os.path.join(self.root, "locked")
        os.makedirs(locked)
        os.chmod(locked, stat.S_IRUSR | stat.S_IXUSR)
        self.addCleanup(os.chmod, locked, 0o755)
        self.assertEqual(run_hook(locked, self.transcript).returncode, 0,
                         "unmutated hook already blocks on an unwritable project")
        self.assertEqual(run_hook(locked, self.transcript, script=mutant).returncode, 2,
                         "mutant did not block: this case is not reaching mkdir")


class Retention(HookCase):
    """Pre-existing behaviour, pinned while the file is being changed."""

    def test_keeps_at_most_twenty_snapshots(self):
        backups = os.path.join(self.project, ".genesis", "backups")
        os.makedirs(backups)
        for i in range(25):
            os.makedirs(os.path.join(backups, f"20200101-0000{i:02d}-manual"))
        run_hook(self.project, self.transcript)
        kept = [d for d in os.listdir(backups)
                if os.path.isdir(os.path.join(backups, d))]
        self.assertLessEqual(len(kept), 20, f"retention did not prune: {len(kept)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
