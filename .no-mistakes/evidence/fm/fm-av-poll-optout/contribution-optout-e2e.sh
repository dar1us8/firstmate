#!/usr/bin/env bash
set -euo pipefail

ROOT=/Users/darrylkwan/.no-mistakes/worktrees/ed75b620a487/01M2R9C6J8JZXN4EMRKA9RH9GD
HOME_FIXTURE=$(mktemp -d "${TMPDIR:-/tmp}/fm-optout-evidence.XXXXXX")
trap 'rm -rf "$HOME_FIXTURE"' EXIT
HEAD=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
mkdir -p "$HOME_FIXTURE"/{data/delivery,state,config,projects,fakebin,forge,root/bin,wt}
printf '# Backlog\n\n## Queued\n- [ ] delivery - Contribution https://github.com/o/r/pull/8 (repo: sample) (kind: ship)\n' > "$HOME_FIXTURE/data/backlog.md"
printf '#!/bin/sh\nexit 0\n' > "$HOME_FIXTURE/root/bin/fm-guard.sh"
printf '#!/bin/sh\nexit 1\n' > "$HOME_FIXTURE/fakebin/tmux"
printf '#!/bin/sh\nexit 0\n' > "$HOME_FIXTURE/fakebin/no-mistakes"
printf 'worktree=%s/wt\nkind=ship\n' "$HOME_FIXTURE" > "$HOME_FIXTURE/state/delivery.meta"
printf '%s\n' "$HEAD" > "$HOME_FIXTURE/forge/head"
: > "$HOME_FIXTURE/forge/calls"
chmod +x "$HOME_FIXTURE/root/bin/fm-guard.sh" "$HOME_FIXTURE/fakebin/tmux" "$HOME_FIXTURE/fakebin/no-mistakes"
chmod 600 "$HOME_FIXTURE/state/delivery.meta"

jq -n --arg head "$HEAD" '{schema:"fm-contributions.v1",task:"delivery",records:[{
  url:"https://github.com/o/r/pull/8",kind:"pr",checked_at:"2026-09-16T08:00:00Z",error:null,
  pending:[],seen:[],verdict:null,observation:{head:$head,state:"open",draft:false,
  mergeable:"mergeable",review_decision:"APPROVED",can_merge:false,checks:[],reviews:[],events:[]}}]}' \
  > "$HOME_FIXTURE/data/delivery/contributions.json"

cat > "$HOME_FIXTURE/fakebin/gh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$FORGE/calls"
case "$*" in
  'pr view '*headRefOid,reviewDecision*)
    jq -n --arg head "$(cat "$FORGE/head")" '{headRefOid:$head,reviewDecision:"APPROVED"}' ;;
  'pr view '*headRefOid*) cat "$FORGE/head" ;;
  *) printf 'unexpected gh call: %s\n' "$*" >&2; exit 1 ;;
esac
SH
chmod +x "$HOME_FIXTURE/fakebin/gh"

run_home() {
  PATH="$HOME_FIXTURE/fakebin:$PATH" FORGE="$HOME_FIXTURE/forge" FM_GATE_REFUSE_BYPASS=1 \
    FM_HOME="$HOME_FIXTURE" FM_ROOT_OVERRIDE="$HOME_FIXTURE/root" \
    FM_STATE_OVERRIDE="$HOME_FIXTURE/state" FM_DATA_OVERRIDE="$HOME_FIXTURE/data" \
    FM_CONFIG_OVERRIDE="$HOME_FIXTURE/config" FM_CONTRIBUTIONS_NOW=2026-09-16T08:00:00Z "$@"
}
show_checks() {
  find "$HOME_FIXTURE/state" -maxdepth 1 -name '*.check.sh' -exec basename {} \; | LC_ALL=C sort | paste -sd, -
}
count_calls() { wc -l < "$HOME_FIXTURE/forge/calls" | tr -d ' '; }

printf '1. Register a PR before opting out\n'
run_home "$ROOT/bin/fm-pr-check.sh" delivery https://github.com/o/r/pull/8 >/dev/null
printf '   registered checks: %s\n' "$(show_checks)"
printf '   contribution check present: %s\n' "$([ -f "$HOME_FIXTURE/state/contributions.check.sh" ] && echo yes || echo no)"

printf '\n2. Use the supported durable opt-out\n'
run_home "$ROOT/bin/fm-contributions.sh" disable | sed 's/^/   command output: /'
printf '   durable flag present: %s\n' "$([ -f "$HOME_FIXTURE/config/contributions-poll-disabled" ] && echo yes || echo no)"
printf '   contribution check present: %s\n' "$([ -e "$HOME_FIXTURE/state/contributions.check.sh" ] && echo yes || echo no)"
printf '   unrelated PR check retained: %s\n' "$([ -f "$HOME_FIXTURE/state/delivery.check.sh" ] && echo yes || echo no)"

printf '\n3. Simulate startup auto-arm while disabled\n'
: > "$HOME_FIXTURE/forge/calls"
run_home "$ROOT/bin/fm-contributions.sh" arm --if-owned
printf '   GitHub calls: %s\n' "$(count_calls)"
printf '   contribution check recreated: %s\n' "$([ -e "$HOME_FIXTURE/state/contributions.check.sh" ] && echo yes || echo no)"

printf '\n4. Register the PR again while disabled\n'
: > "$HOME_FIXTURE/forge/calls"
run_home "$ROOT/bin/fm-pr-check.sh" delivery https://github.com/o/r/pull/8 >/dev/null
printf '   GitHub calls (explicit PR-head read only):\n'
sed 's/^/     /' "$HOME_FIXTURE/forge/calls"
printf '   contribution check recreated: %s\n' "$([ -e "$HOME_FIXTURE/state/contributions.check.sh" ] && echo yes || echo no)"

printf '\n5. Invoke the contribution poll while disabled\n'
: > "$HOME_FIXTURE/forge/calls"
POLL_OUTPUT=$(run_home "$ROOT/bin/fm-contributions.sh" poll)
printf '   poll output bytes: %s\n' "$(printf %s "$POLL_OUTPUT" | wc -c | tr -d ' ')"
printf '   GitHub calls: %s\n' "$(count_calls)"
printf '   RESULT: durable opt-out survived startup/PR auto-arm and prevented contribution forge reads.\n'
