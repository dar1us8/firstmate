# Independent Test: SDK compatibility and bounded fixture correction

Target: 1114ae0a012d30ca42f731ca0009df4f5b851504.
Production baseline: 6407052f4c521e39401ce2305dfa45d201249827.
Verdict: go for this assigned Test phase; no merge, installation, PR, or CI verdict is implied.

## Executed in this iteration

- Provisioned actual SDK1.2.0 inside `.test-independent-round2/sdk12` using the retained integrity lock and `npm ci --install-strategy=nested --ignore-scripts --no-audit --no-fund`.
- Ran `FM_PI_BRANCH_LIVE_E2E=1 FM_PI_PACKAGE_DIR=<actual-package> TMPDIR=<worktree-local-directory> bash bin/fm-test-run.sh tests/fm-pi-branch-live-e2e.test.sh` once on the corrected target for each SDK. Both completed with exit 0; no failed command was retried.
- Created a disposable baseline with `git archive 6407052f4c521e39401ce2305dfa45d201249827`. Replaced only the canonical first probe/fixture with the corrected executable contract, leaving baseline production and every remaining baseline probe unchanged. Ran the same canonical guard once against each SDK; both completed with exit 0. These are matched corrected-fixture controls, not untouched historical baseline executions.
- Ran `bash bin/fm-test-run.sh tests/fm-pi-branch-extension.test.sh tests/fm-pi-watch-extension.test.sh` with worktree-local TMPDIR. Both completed with exit 0, preserving portable cancellation, pending-wake replacement, generation, ownership, and message-consumption controls. These mocked-interface controls are supplemental, not live proof.
- Extracted actual `LIVE_OK` and `CANCEL_OK` records from the four live transcripts into `independent-round2-request-boundaries.json` without synthesizing observations.

## Product-level observations

The corrected first probe uses actual DefaultResourceLoader, ModelRuntime, AgentSession, ExtensionRunner, SessionManager, extension inputs, user message consumption, provider requests, and settlement events.
Only the provider transport and canonical arm fixture are disposable substitutes; the production consumers and vendor sessions are real.
Both SDKs reject the branch offer for an empty branch runtime and for `openai/no-such-live-model`.
The executable assertions require the latter rejection to name the unusable pin and its supervision-pin classification.
Both fallback wakes reach actual main provider inputs and persistent session context, with two settlements and two delivery confirmations.
No branch outcome or claimed row remains, and the durable notification row remains available.
The replacement fixture retires its previous polling process before receiving the second trigger.
The raw records identify the process that consumed each trigger.

SDK1.2 accepts actual prompt-bearing user and no-prompt custom events through the vendor runner with both production consumers loaded.
Its dedicated processing run opens through the custom event boundary and is cancelled before a second provider request: two settlements, one completion at that point.
The subsequent ordinary request then executes, giving the final recorded three settlements and two completions.
Stored processing history is retained, while subsequent request-local context and provider input exclude its envelope and preserve both ordinary user turns.
Separate ordinary user and unrelated custom runs survive away posture and retain their expected provider content and unprocessed outcomes.
SDK1.1 completes all applicable older controls, including ordinary user preservation; its absent SDK1.2 custom-opening boundaries remain explicitly N/A.
Both SDKs complete real streaming follow-up consumption and successor delivery, plus existing retry/history/rendering controls.
No ordinary-dialog duplication repair is claimed.

## Earlier evidence and causal limits

The original SDK1.1 target and unchanged baseline pinned-delivery timeouts remain failed executions in `live-sdk11-full.log` and `live-sdk11-baseline.log`.
The original unchanged successful replay in `live-sdk11-replay.log` remains contrary evidence, not a cure for those failures.
The retained repair retirement-invariant failure shows two canonical fixture arms alive after replacement (`repair-sdk11-fixture-contract-before.log`).
This proves an executable fixture-contract defect consistent with the intermittent timeout.
Historical timeout logs do not identify the consuming process, so neither this report nor the passing corrected checks prove that defect caused every historical failure or that production delivery has no other defects.
The correction preserves the original internal waits and assertions and adds real consumption/request observations rather than weakening the check or inflating its timeout.
Intermediate repair failures and all earlier raw artifacts remain untouched.

The prior independent compiler tests in `types-sdk11.log` and `types-sdk12.log` compiled the actual production consumers against both real declaration sets with TypeScript5.9.3 and exited 0.
`types-sdk11-reviewed-control.log` reproduced the reported two TS2339 errors before the predicate correction.
Production consumers are unchanged by the fixture-only repair being retested here.
These are retained earlier-round compiler results, not fresh live scenarios or newly executed static analysis; no compiler, linter, or formatter was run in this iteration.

## Isolation and evidence

SDK1.1 remained the installed 1.1.0 package; SDK1.2 and all fixture homes stayed inside the worktree.
No external provider request, production credential access, global configuration change, operational home/session action, Herdr lifecycle, pipeline control, push, or broad suite execution was performed.
Only the existing canonical guard owned its fake arm and safe homes; no separate arm was provisioned.
The worktree-local dependencies and baseline copies were not prepare-owned and were removed after evidence capture.
No permanent source or test changes were made by this Test iteration.
This is a runtime compatibility/fixture change, not a new visual surface; provider/context transcripts are the relevant evidence, and no screenshot was captured.
