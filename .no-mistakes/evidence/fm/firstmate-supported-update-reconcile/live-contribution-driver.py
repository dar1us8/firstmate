import os, subprocess, pathlib, json, threading, http.server, urllib.parse, tempfile, shutil, socketserver, signal, time
ROOT=pathlib.Path.cwd()
EVIDENCE=pathlib.Path(os.environ["FM_VALIDATION_EVIDENCE"])
HOME=pathlib.Path(tempfile.mkdtemp(prefix='live-home-',dir=ROOT/'.validation-tmp'))
log=[]
requests=[]
comment=[]
HEAD='a'*40
pause_poll=threading.Event(); poll_started=threading.Event(); release_poll=threading.Event()
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path=urllib.parse.urlsplit(self.path).path.removeprefix('/api/v3')
        requests.append(path)
        if path=='/repos/example/lab/issues/1':
            if pause_poll.is_set():
                poll_started.set(); assert release_poll.wait(4)
            data={'state':'open','user':{'login':'author'},'labels':[], 'html_url':'https://github.com/example/lab/issues/1'}
        elif path.endswith('/comments'): data=comment
        elif path.endswith('/events'): data=[]
        else:
            self.send_error(404);return
        payload=json.dumps(data).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
    def do_POST(self):
        path=urllib.parse.urlsplit(self.path).path
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        requests.append({'method':'POST','path':path,'query':body.get('query','')})
        payload=json.dumps({'data':{'repository':{'pullRequest':{'id':'PR_synthetic','number':2,'isDraft':False,'headRefOid':HEAD,'reviewDecision':'APPROVED','state':'OPEN','url':'https://github.com/example/lab/pull/2'}}}}).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
    def log_message(self,*args): pass
server=None
waiters=[]
try:
    for p in ['state','data','config','projects','gh-config']: (HOME/p).mkdir()
    (HOME/'data/backlog.md').write_text('# Backlog\n\n## Queued\n- [ ] issue - Synthetic issue https://github.com/example/lab/issues/1 (repo: sample) (kind: ship)\n')
    socket_path=str(HOME.relative_to(ROOT)/'forge.sock')
    class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer): daemon_threads=True
    server=Server(socket_path,Handler)
    (HOME/'gh-config/config.yml').write_text('http_unix_socket: '+socket_path+'\n')
    threading.Thread(target=server.serve_forever,daemon=True).start()
    env={k:v for k,v in os.environ.items() if not k.startswith(('FM_','GH_','GITHUB_','TASKS_AXI_'))}
    env.update(FM_HOME=str(HOME),FM_ROOT_OVERRIDE=str(ROOT),FM_STATE_OVERRIDE=str(HOME/'state'),FM_DATA_OVERRIDE=str(HOME/'data'),FM_CONFIG_OVERRIDE=str(HOME/'config'),GH_CONFIG_DIR=str(HOME/'gh-config'),GH_HOST='localhost',GH_ENTERPRISE_TOKEN='synthetic-local-only-token',GH_TOKEN='synthetic-local-only-token',GH_NO_UPDATE_NOTIFIER='1',GH_NO_EXTENSION_UPDATE_NOTIFIER='1',GH_TELEMETRY='0',NO_PROXY='localhost,127.0.0.1',TMPDIR=str(ROOT/'.validation-tmp'))
    def cli(*args,expect=0):
        p=subprocess.run([str(ROOT/'bin/fm-contributions.sh'),*args],env=env,text=True,capture_output=True,timeout=35)
        assert p.returncode==expect,(args,p.returncode,p.stdout,p.stderr)
        log.append({'command':'fm-contributions.sh '+' '.join('scenario-input.json' if a.endswith('scenario-input.json') else a for a in args),'exit':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()})
        return p.stdout
    # Real gh talks exclusively to the disposable local TLS API; no CLI shim.
    cli('poll')
    rec=HOME/'data/issue/contributions.json'
    assert rec.exists() and json.loads(rec.read_text())['records'][0]['error'] is None, rec.read_text() if rec.exists() else 'no record'
    assert len(requests)==3,requests
    cli('arm','--if-owned')
    check=HOME/'state/contributions.check.sh'; trust=HOME/'state/contributions.check-trust'
    assert check.exists() and trust.exists()
    saved=rec.read_bytes(); other=HOME/'state/unrelated.check.sh';other.write_text('#!/bin/sh\nexit 0\n');other.chmod(0o700)
    cli('disable'); assert not check.exists() and not trust.exists()
    start=len(requests)
    for args in [('arm',),('arm','--if-owned'),('poll',)]: assert cli(*args)==''
    assert len(requests)==start and rec.read_bytes()==saved and other.exists()
    snapshot_input=subprocess.run([str(ROOT/'bin/fm-fleet-snapshot.sh'),'--contribution-input'],env=env,text=True,capture_output=True,check=True).stdout
    (HOME/'scenario-input.json').write_text(snapshot_input)
    snapshot=json.loads(cli('snapshot',str(HOME/'scenario-input.json'),'--all')); assert snapshot['checked']==1
    assert json.loads(cli('pending'))==[]
    log.append({'observation':'Disabled poll and all arm variants produced no output or API requests; cached ownership and unrelated check survived.','api_requests_while_disabled':len(requests)-start})
    # Independently reproduce the missing opt-out on the maintained parent.
    start=len(requests)
    for action in ['poll','arm']:
        before=subprocess.run([str(ROOT/'.validation-tmp/bin/fm-contributions.sh'),action],env=env,text=True,capture_output=True,timeout=35)
        assert before.returncode==0,(before.stdout,before.stderr)
    assert len(requests)-start==3 and check.exists() and trust.exists()
    log.append({'observation':'Maintained parent ignored the same opt-out flag: poll still made three API requests and arm restored registration. Candidate suppresses both, reproducing the regression before/after.','parent_api_requests_while_disabled':len(requests)-start,'parent_arm_stdout':before.stdout.strip()})
    cli('disable')
    cli('enable'); assert check.exists() and trust.exists() and not (HOME/'config/contributions-poll-disabled').exists()
    # Trust is validated through the shipped custom-check consumer.
    p=subprocess.run(['bash','-c','. "$1/bin/fm-pr-lib.sh"; . "$1/bin/fm-check-lib.sh"; fm_custom_check_registered "$2/state" contributions','_',str(ROOT),str(HOME)],env=env,capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    comment.append({'id':12,'user':{'login':'maintainer'},'author_association':'OWNER','body':'Synthetic maintainer feedback','html_url':'https://github.com/example/lab/issues/1#issuecomment-12','updated_at':'2026-10-23T00:00:00Z'})
    p=subprocess.run(['bash',str(check)],env=env,capture_output=True,text=True,timeout=35)
    assert p.returncode==0,(p.stdout,p.stderr)
    pending=json.loads(cli('pending'));assert len(pending)==1 and pending[0]['author']=='maintainer',pending
    wake=(HOME/'state/.wake-queue').read_text(); lines=len(wake.splitlines())
    cli('poll'); assert len((HOME/'state/.wake-queue').read_text().splitlines())==lines
    log.append({'observation':'Enable restored authenticated registration; its real CLI poll captured a maintainer comment and exactly one durable wake; replay did not duplicate it.','pending_count':len(pending),'durable_wakes':lines})
    # Disable waits for an already-running real observation; once complete it is silent.
    pause_poll.set()
    poll=subprocess.Popen([str(ROOT/'bin/fm-contributions.sh'),'poll'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    assert poll_started.wait(4)
    # Stop actual arm and poll shells only after both reach the real held lock.
    for action in ['arm','poll']:
        trace=HOME/(action+'.trace'); stream=trace.open('w')
        waiter=subprocess.Popen(['bash','-x',str(ROOT/'bin/fm-contributions.sh'),action],env=env,stdout=subprocess.PIPE,stderr=stream,text=True)
        waiters.append((waiter,stream))
        deadline=time.monotonic()+2
        while '+ fm_lock_acquire_wait ' not in trace.read_text():
            assert waiter.poll() is None and time.monotonic()<deadline,'waiter never reached held lock'
            time.sleep(0.01)
        os.kill(waiter.pid,signal.SIGSTOP)
    disable=subprocess.Popen([str(ROOT/'bin/fm-contributions.sh'),'disable'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    release_poll.set()
    pout,perr=poll.communicate(timeout=35);dout,derr=disable.communicate(timeout=35)
    assert poll.returncode==0 and disable.returncode==0,(perr,derr)
    pause_poll.clear();start=len(requests)
    for waiter,stream in waiters:
        os.kill(waiter.pid,signal.SIGCONT)
        wout,_=waiter.communicate(timeout=35);stream.close()
        assert waiter.returncode==0 and wout==''
    assert not check.exists() and not trust.exists() and len(requests)==start
    assert cli('poll')=='' and cli('arm')=='' and len(requests)==start
    log.append({'observation':'Disable serialized with an in-flight real-gh poll. Pre-existing arm and poll processes were SIGSTOPped after reaching the real held lock, then resumed after disable completed; neither restored registration nor made an API request.','disable_stdout':dout.strip(),'api_requests_after_disable':len(requests)-start})
    # Explicit PR-ready registration still reads its head and keeps the exact merge poll.
    (HOME/'state/delivery.meta').write_text('kind=ship\nmode=no-mistakes\nworktree='+str(ROOT)+'\n')
    p=subprocess.run([str(ROOT/'bin/fm-pr-check.sh'),'delivery','https://github.com/example/lab/pull/2'],env=env,text=True,capture_output=True,timeout=35)
    assert p.returncode==0,(p.stdout,p.stderr)
    if ('pr_head='+HEAD) not in (HOME/'state/delivery.meta').read_text():
        debug=subprocess.run(['gh','pr','view','https://github.com/example/lab/pull/2','--json','headRefOid','-q','.headRefOid'],env=env,text=True,capture_output=True)
        raise AssertionError((debug.stdout,debug.stderr,requests))
    assert (HOME/'state/delivery.check.sh').exists() and not check.exists()
    assert any(isinstance(r,dict) and 'headRefOid' in r['query'] for r in requests)
    assert not any(isinstance(r,str) and '/pulls/' in r for r in requests)
    log.append({'observation':'While opted out, PR-ready registration performed its explicit GraphQL head read, saved the exact head and armed the independent merge check, without arming contribution polling.','registration_stdout':p.stdout.strip(),'head':HEAD})
    # Adversarial symlink flag stays disabled and enable must not remove it.
    cli('disable'); flag=HOME/'config/contributions-poll-disabled';flag.unlink();flag.symlink_to(HOME/'missing-target')
    start=len(requests)
    assert cli('poll')=='';assert cli('arm')==''
    cli('enable',expect=1);assert flag.is_symlink() and len(requests)==start
    log.append({'observation':'A dangling opt-out symlink suppresses polling and arming; enable refuses unsafe removal.','api_requests':len(requests)-start})
    # Enroll uses the real durable ownership writer, with no forge discovery.
    flag.unlink();cli('enroll','delivery','https://github.com/example/lab/pull/2')
    owned=json.loads(cli('owned'));assert any(r['url'].endswith('/pull/2') for r in owned)
    log.append({'observation':'Explicit enrollment persisted a new owned PR without repository-wide discovery.'})
    # A registered shim must retain an alternate config root, even without caller overrides.
    (HOME/'alternate-config').mkdir(); env['FM_CONFIG_OVERRIDE']=str(HOME/'alternate-config')
    cli('arm','--if-owned'); saved_shim=HOME/'saved-check.sh';saved_shim.write_bytes(check.read_bytes())
    cli('disable'); assert (HOME/'alternate-config/contributions-poll-disabled').exists()
    child_env=env.copy();child_env.pop('FM_CONFIG_OVERRIDE'); start=len(requests)
    p=subprocess.run(['bash',str(saved_shim)],env=child_env,text=True,capture_output=True,timeout=35)
    assert p.returncode==0 and p.stdout=='' and len(requests)==start,(p.stdout,p.stderr)
    log.append({'observation':'A previously registered shim retained the alternate configuration root and remained forge-silent after disable, even when its caller omitted FM_CONFIG_OVERRIDE.','api_requests':len(requests)-start})
    (EVIDENCE/'contribution-cli-transcript.json').write_text(json.dumps({'result':'pass','driver':'Unmodified product CLI and installed gh against disposable Unix-socket HTTP API using the http_unix_socket setting; no production accounts or data.','steps':log,'api_requests':requests},indent=2)+'\n')
    print('live contribution CLI scenarios passed')
finally:
    for waiter,stream in waiters:
        if waiter.poll() is None:
            os.kill(waiter.pid,signal.SIGCONT);waiter.terminate();waiter.wait(timeout=5)
        stream.close()
    if server:server.shutdown();server.server_close()
    os.chdir(ROOT)
    shutil.rmtree(HOME)
