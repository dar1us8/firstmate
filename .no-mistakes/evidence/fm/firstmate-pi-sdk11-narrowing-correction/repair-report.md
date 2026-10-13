# Bounded Test fixture correction

Only `tests/fm-pi-branch-live-e2e.test.sh` changed; production delivery, mirroring, cancellation, SDK type predicates, runtime installation and operational homes did not change.
No linters, formatters, typechecks, full repository suite, pipeline-control commands, live operational monitoring or external provider requests were executed in this repair.

## Reproduction and causal limits

The retained `live-sdk11-full.log` and unchanged production baseline `live-sdk11-baseline.log` both timed out waiting for pinned watcher-owned main delivery; retained `live-sdk11-replay.log` passed without changes.
Those historical failures remain failures, not superseded by the replay.
The fresh unchanged focused guard in `repair-sdk11-before.log` also passed, so the historical timeout itself was not reproduced in this invocation.

The existing canonical fake arm did not implement `--restart`: after replacement, both the prior-generation arm and the current arm polled the same trigger file.
Production `fm-watch-arm.sh --restart` retires this home's previous watcher instead.
The added executable retirement invariant failed deterministically with the unchanged fixture in `repair-sdk11-fixture-contract-before.log` at the original 600-by-50ms bound.
Its trace records arm 46345 still alive alongside replacement arm 47059.
A retired generation consuming and deleting a shared trigger is consistent with the original intermittent missing delivery and unchanged baseline/replay split.
The historical logs do not identify which process read that trigger, so this is a demonstrated fixture-contract defect, not proof that it exclusively caused every historical timeout or that production delivery has no other defects.

The fixture now retires its own last recorded arm on `--restart`, retains original trigger polling and wait bounds, records the consuming arm, and requires one live arm before submitting the replacement trigger.
No production retirement/delivery algorithm was repaired or copied into a new framework.

## Actual SDK notification ownership proof

The first canonical probe no longer fabricates a successful main send callback or vendor events.
Both production extension factories load through the real DefaultResourceLoader; the real main AgentSession/ExtensionRunner receives the extension send, persists its user message and completes the intercepted local-provider request.
The branch retains its empty, isolated agent directory, while main has a separate local runtime with a placeholder key.
The existing branch settlement assertions still require rejection for both an unpromptable branch and `openai/no-such-live-model`, including the unusable pin's exact identity and supervision-pin error classification.
The existing accepted-offer, branch pointer/store, wake-reason and two confirmation assertions remain.
Additional assertions require two actual main requests/settlements, exact persisted fallback content, no fabricated branch outcome/claimed-row grant, and retention of the durable notification row.
All transport is intercepted in-process; no account or credentials were changed.

Two intermediate fixture-observation failures are retained:
- `repair-sdk11-after.log`: main session disposal invalidated its shared vendor extension runtime; reusing that stale runtime prevented actual pinned delivery. The fixture now reloads resources before replacement, as the vendor lifecycle requires.
- `repair-sdk11-runtime-contract-after.log`: both real deliveries completed, but an added assertion incorrectly required an idle SDK1.1 input to report streamingBehavior. Idle input has no such field. The fixture asserts its actual extension source, consumption, persisted state and request; existing real streaming follow-up assertions are unchanged.

These are not passing executions and were not discarded or counted as successful retries.
Each subsequent execution followed a concrete fixture correction; no unchanged failed guard was replayed until green.

## Focused verification

Commands used the canonical `bash bin/fm-test-run.sh tests/fm-pi-branch-live-e2e.test.sh` with `FM_PI_BRANCH_LIVE_E2E=1` and TMPDIR inside this worktree.
SDK1.1 used the unchanged installed actual package; SDK1.2 used `FM_PI_PACKAGE_DIR` pointing at the worktree-local actual package installed with npm's nested strategy and scripts disabled.
Package/compiler provenance from the preceding Test remains separate; this repair did not re-run static analysis.
New package version/runtime provenance and SDK1.2 integrity lock are retained in `repair-provenance.log` and `repair-sdk12-package-lock.json`.

- `repair-sdk11-final.log`: exit 0, complete focused guard, two real fallback requests and settlements. Only existing SDK1.2-only custom-boundary scenarios are N/A.
- `repair-sdk12-final.log`: exit 0, complete focused guard, two real fallback requests and settlements. Existing real event, streaming, cancellation, history, request-local filtering, user/unrelated preservation and unprocessed-outcome controls all passed.
- `repair-sdk11-baseline-control.log` and `repair-sdk12-baseline-control.log`: exit 0 on disposable `git archive` copies of unchanged production base 6407052f4c521e39401ce2305dfa45d201249827. Only the first fixture/probe was replaced with this corrected contract; remaining probes were the baseline's original tests. These are matched corrected-fixture controls, not claims that the untouched original fixture was repaired historically. Original baseline evidence is untouched.

`repair-request-boundaries.json` extracts actual emitted request/input/watch records from these logs, plus target cancellation records.
The SDK1.2 processing subprobe retains its two-settlement/one-completion cancelled-run assertion before the subsequent ordinary request; the final record has three settlements/two completions because that subsequent request actually ran.
Stored processing history and unprocessed outcomes remain intact while subsequent request-local context/provider input excludes the processing envelope.
No broader regression or remote CI verdict is claimed; CI remains required before a PR is ready.

Disposable dependencies, baseline copies and temporary fixture directories created by this repair were removed after evidence capture; no prepare-owned dependencies were removed.
