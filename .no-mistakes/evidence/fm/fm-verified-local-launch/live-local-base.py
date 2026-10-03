import os, subprocess, pathlib, json, time, shutil, tempfile
ROOT = pathlib.Path.cwd()
EVID = pathlib.Path('/Users/darrylkwan/.no-mistakes/evidence/01M414EE49HY4BQ9F5YY638BDM')
LAB = pathlib.Path(tempfile.mkdtemp(prefix='live-base-', dir=ROOT / '.test-tmp'))
log = open(EVID / 'live-launch-transcript.log', 'w')
results = []
env = dict(os.environ)
for key in list(env):
    if (key.startswith('FM_') and key.endswith('_OVERRIDE')) or key in ['FM_GATE_REFUSE_BYPASS','FM_TEST_SEAM','FM_SPAWN_NO_GUARD','FM_TASK_ID','TMUX','HERDR_ENV','HERDR_SESSION','TASKS_AXI_FILE','TASKS_AXI_BACKEND','CLAUDE_CONFIG_DIR']:
        env.pop(key, None)
env.update(HOME=str(LAB / 'user-home'), FM_HOME=str(LAB / 'home'), TREEHOUSE_ROOT=str(LAB / 'slots'), TMPDIR=str(ROOT / '.test-tmp'), GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', TREEHOUSE_NO_UPDATE_CHECK='1')
(LAB / 'user-home').mkdir()
socket = 'fm-local-live-' + str(os.getpid())
# tmux's short socket directory is an incidental toolchain temp file.
def run(args, check=True, e=None, timeout=120, visible=True):
    p = subprocess.run(list(map(str,args)), cwd=ROOT, env=e or env, capture_output=True, text=True, timeout=timeout)
    if visible:
        log.write('$ ' + ' '.join(map(str,args)) + '\n' + p.stdout + p.stderr + 'exit=' + str(p.returncode) + '\n'); log.flush()
    if check and p.returncode:
        raise RuntimeError(p.stdout + p.stderr)
    return p

def git(*args): return run(['git','-C',LAB/'project',*args], visible=False).stdout.strip()
def brief(id, ship=False):
    args = ['bin/fm-brief.sh',id,'project'] + (['--mode','no-mistakes'] if ship else ['--scout'])
    run(args)
    path = LAB/'home/data'/id/'brief.md'
    path.write_text(path.read_text().replace('{TASK}','Verify local launch in this disposable lab; do not publish anything.').replace('{FIRSTMATE_SPEC}','Inspect only; the launch receiver records its actual working directory and input.'))

def spawn(label, extra, ship=False, expected=None):
    id = 'lv-' + str(os.getpid()) + '-' + label
    brief(id, ship)
    args = ['bin/fm-spawn.sh',id,LAB/'project','--backend','tmux','--harness','/bin/bash '+str(LAB/'receiver.sh')+' __BRIEF__']
    args += ['--mode','no-mistakes','--yolo','off'] if ship else ['--scout']
    args += extra
    (EVID/('git-'+label+'.jsonl')).write_text('')
    e = dict(env, GIT_TRACE2_EVENT=str(EVID/('git-'+label+'.jsonl')))
    before = git('rev-parse','HEAD')
    acquisition_trace = EVID/'treehouse-acquisition.jsonl'
    start_line = len(acquisition_trace.read_text().splitlines())
    p = run(args, check=expected is None, e=e)
    new_events = [json.loads(line) for line in acquisition_trace.read_text().splitlines()[start_line:]]
    treehouse_transport = [event['argv'] for event in new_events if event.get('event')=='start' and any(word in ['fetch','ls-remote','push','clone'] for word in event['argv'][1:])]
    if expected:
        assert p.returncode != 0 and expected in p.stdout+p.stderr, (label,p.stdout,p.stderr)
        assert not (LAB/'home/state'/ (id+'.meta')).exists()
        assert git('rev-parse','HEAD') == before
        run(['tmux','-L',socket,'capture-pane','-p','-t','local-base:fm-'+id],check=False)
    else:
        meta = LAB/'home/state'/ (id+'.meta')
        fields = dict(line.split('=',1) for line in meta.read_text().splitlines() if '=' in line)
        wt = pathlib.Path(fields['worktree'])
        assert wt != LAB/'project'
        actual = run(['git','-C',wt,'rev-parse','HEAD']).stdout.strip()
        assert actual == sha
        assert not run(['git','-C',wt,'status','--porcelain']).stdout.strip()
        owner = (wt.parent/'.fm-slot-owner').read_text()
        assert 'task='+id in owner
        for _ in range(30):
            received = LAB/('received-'+id)
            if received.exists() and '## Captain\'s intent' in received.read_text(): break
            time.sleep(.1)
        assert received.exists() and '## Captain\'s intent' in received.read_text(), 'worker did not receive launch brief'
        log.write('PERSISTED METADATA\n'+meta.read_text()+'SLOT OWNER\n'+owner+'WORKER RECEIPT\n'+received.read_text()+'PANE\n')
        run(['tmux','-L',socket,'capture-pane','-p','-t',fields['window']])
        assert fields['kind'] == ('ship' if ship else 'scout')
        if ship: assert fields['mode'] == 'no-mistakes' and fields['yolo'] == 'off'
        results.append(dict(label=label,result='pass',worktree=str(wt),head=actual,treehouse_transport=treehouse_transport))
        return wt
    results.append(dict(label=label,result='pass',refusal=expected,treehouse_transport=treehouse_transport))

try:
    run(['bin/fm-lab-home.sh','create',LAB/'home'])
    run(['git','init','-q','-b','trunk',LAB/'project'])
    (LAB/'project/readme').write_text('initial\n')
    git('add','readme'); git('-c','user.name=Live Test','-c','user.email=test@example.invalid','commit','-qm','initial')
    oldsha=git('rev-parse','HEAD')
    (LAB/'project/readme').write_text('verified local commit\n')
    git('add','readme'); git('-c','user.name=Live Test','-c','user.email=test@example.invalid','commit','-qm','verified')
    sha=git('rev-parse','HEAD')
    run(['git','clone','-q','--bare',LAB/'project',LAB/'origin.git'])
    git('remote','add','origin','file://'+str(LAB/'origin.git'))
    git('fetch','-q','origin'); git('remote','set-head','origin','--auto')
    git('remote','set-url','origin','file://'+str(LAB/'unreachable.git'))
    (LAB/'receiver.sh').write_text('#!/bin/bash\nprintf "cwd=%s\\nhead=%s\\ntask=%s\\n" "$PWD" "$(git rev-parse HEAD)" "$FM_TASK_ID" > "$FM_HOME/../received-$FM_TASK_ID"\ncat "$1" >> "$FM_HOME/../received-$FM_TASK_ID"\nwhile IFS= read -r line; do printf "%s\\n" "$line" >> "$FM_HOME/../received-$FM_TASK_ID"; done\n')
    (EVID/'treehouse-acquisition.jsonl').write_text('')
    env['GIT_TRACE2_EVENT'] = str(EVID/'treehouse-acquisition.jsonl')
    run(['tmux','-L',socket,'-f','/dev/null','new-session','-d','-s','local-base','-x','120','-y','40','-c',LAB/'project','/bin/bash --noprofile --norc'])
    run(['tmux','-L',socket,'set-option','-g','default-shell','/bin/bash'])
    run(['tmux','-L',socket,'set-option','-g','default-command','/bin/bash --noprofile --norc'])
    env['TMUX'] = run(['tmux','-L',socket,'display-message','-p','#{socket_path},#{pid},0'],visible=False).stdout.strip()
    first=spawn('ship-a',['--local-base',sha],ship=True)
    second=spawn('ship-b',['--local-base='+sha],ship=True)
    assert first != second, 'parallel tasks share a copy'
    (first/'uncommitted-worker-work').write_text('parallel work must survive\n')
    third=spawn('scout',['--local-base',sha])
    assert len({first,second,third}) == 3
    assert (first/'uncommitted-worker-work').read_text() == 'parallel work must survive\n'
    assert run(['git','-C',first,'rev-parse','HEAD']).stdout.strip() == sha
    log.write('Parallel worker uncommitted work survived the next isolated launch.\n')
    hooks=LAB/'hooks'; hooks.mkdir()
    hook=hooks/'post-checkout'
    git('config','core.hooksPath',str(hooks))
    hook.write_text('#!/bin/bash\nprintf "%s" "$PWD" > "'+str(LAB/'acquired-path')+'"\nprintf "preserve acquired work\\n" > keep-untracked\n')
    hook.chmod(0o700)
    spawn('dirty-acquired',['--local-base',sha],expected='is not clean')
    acquired=pathlib.Path((LAB/'acquired-path').read_text())
    assert (acquired/'keep-untracked').read_text() == 'preserve acquired work\n'
    assert run(['git','-C',acquired,'rev-parse','HEAD']).stdout.strip() == sha
    log.write('Refused acquired copy preserved its uncommitted file and HEAD.\n')
    hook.write_text('#!/bin/bash\nprintf "%s" "$PWD" > "'+str(LAB/'acquired-path')+'"\ngit update-ref refs/remotes/origin/trunk '+oldsha+'\n')
    spawn('changed-tip',['--local-base',sha],expected='exactly matching')
    acquired=pathlib.Path((LAB/'acquired-path').read_text())
    assert run(['git','-C',acquired,'rev-parse','HEAD']).stdout.strip() == sha
    git('update-ref','refs/remotes/origin/trunk',sha)
    hook.write_text('#!/bin/bash\nprintf "%s" "$PWD" > "'+str(LAB/'acquired-path')+'"\ngit reset --hard '+oldsha+'\n')
    spawn('wrong-acquired-head',['--local-base',sha],expected='acquired HEAD')
    acquired=pathlib.Path((LAB/'acquired-path').read_text())
    assert run(['git','-C',acquired,'rev-parse','HEAD']).stdout.strip() == oldsha
    log.write('Wrong acquired HEAD remained untouched after launch refusal.\n')
    git('config','--unset','core.hooksPath')
    spawn('wrong-sha',['--local-base',oldsha],expected='exactly matching')
    spawn('missing-object',['--local-base','0'*40],expected='locally available commit')
    spawn('short-sha',['--local-base',sha[:12]],expected='full lowercase commit SHA')
    (LAB/'project/keep-untracked').write_text('preserve me\n')
    spawn('dirty-source',['--local-base',sha],expected='spawning project is not clean')
    assert (LAB/'project/keep-untracked').read_text() == 'preserve me\n'
    (LAB/'project/keep-untracked').unlink()
    git('symbolic-ref','--delete','refs/remotes/origin/HEAD')
    spawn('missing-default',['--local-base',sha],expected='unambiguous local symbolic origin/HEAD')
    git('symbolic-ref','refs/remotes/origin/HEAD','refs/remotes/origin/trunk')
    git('checkout','--quiet','--detach',sha); git('update-ref','refs/heads/trunk',oldsha)
    spawn('ambiguous-branch',['--local-base',sha],expected='refusing ambiguous Treehouse base selection')
    git('update-ref','refs/heads/trunk',sha)
    spawn('orca',['--local-base',sha,'--backend','orca'],expected='requires a Treehouse-backed')
    spawn('relaunch',['--local-base',sha,'--relaunch'],expected='only to fresh ship/scout')
    spawn('secondmate',['--local-base',sha,'--secondmate'],expected='only to fresh ship/scout')
    acquisition_events = [json.loads(line) for line in (EVID/'treehouse-acquisition.jsonl').read_text().splitlines()]
    acquisition_commands = [event['argv'] for event in acquisition_events if event.get('event')=='start']
    acquisition_transport = [argv for argv in acquisition_commands if any(word in ['fetch','ls-remote','push','clone'] for word in argv[1:])]
    assert not acquisition_transport, acquisition_transport
    log.write('Real Treehouse acquisition transport commands before default-route tests: '+json.dumps(acquisition_transport)+'\n')
    # Confirm the ordinary route still attempts transport and refuses an unreachable origin.
    spawn('default-unreachable',[],expected='did not enter an isolated worktree')
    # Restore the disposable, explicitly authorized fixture remote for the ordinary fetch route.
    git('remote','set-url','origin','file://'+str(LAB/'origin.git'))
    spawn('default-fetch',[])
    for item in results:
        trace = EVID/('git-'+item['label']+'.jsonl')
        events = [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
        commands = [event['argv'] for event in events if event.get('event')=='start']
        transports = [argv for argv in commands if any(word in ['fetch','ls-remote','push','clone'] for word in argv[1:])] + item['treehouse_transport']
        item['transport_commands']=transports
        log.write('TRANSPORT '+item['label']+' '+json.dumps(transports)+'\n')
        if item['label'].startswith('default-'): assert transports, 'default route did not fetch'
        else: assert not transports, 'local launch attempted transport'
    (EVID/'live-launch-results.json').write_text(json.dumps(results,indent=2)+'\n')
    log.write('All live assertions passed. No model CLI, credentials, publication, security setting, or production session was changed.\n')
finally:
    run(['tmux','-L',socket,'kill-server'],check=False)
    for base, dirs, files in os.walk(LAB): os.chmod(base, 0o700)
    shutil.rmtree(LAB)
    log.write('Disposable home and private tmux session removed.\n'); log.close()
