"""Bounded Linux user service for one isolated candidate request; never a global quota.

The service waits for one byte. Only after reading actual kernel cgroup controls
may the parent release the namespace-isolated payload. No implicit installation,
privilege elevation or uncontained fallback. The host kernel remains trusted.
"""
import os
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import uuid

MEMORY=256*1024**2
TASKS=16
ROOT=Path('/sys/fs/cgroup')
GATE=('import os,resource,sys; '
      'assert os.read(0,1)==b"1"; '
      'resource.setrlimit(resource.RLIMIT_AS,(268435456,268435456)); '
      'resource.setrlimit(resource.RLIMIT_CPU,(2,2)); '
      'resource.setrlimit(resource.RLIMIT_FSIZE,(262144,262144)); '
      'resource.setrlimit(resource.RLIMIT_NOFILE,(64,64)); '
      'os.execv(sys.argv[1],sys.argv[1:])')


def environment():
    if sys.platform!='linux' or not (ROOT/'cgroup.controllers').is_file():
        raise ValueError('aggregate isolation requires Linux cgroup v2')
    if any(not shutil.which(x,path=os.defpath) for x in ('systemd-run','systemctl')):
        raise ValueError('aggregate isolation requires an existing systemd user manager')
    runtime=Path('/run/user')/str(os.getuid())
    if not (runtime/'bus').exists():raise ValueError('user service bus unavailable; no uncontained fallback')
    return {'PATH':os.defpath,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path='+str(runtime/'bus')}


def ctl(unit,*args,env):
    return subprocess.run(['systemctl','--user','--no-ask-password',*args,unit],env=env,
                          capture_output=True,text=True,timeout=3)


def properties(unit,env):
    r=ctl(unit,'show','-p','LoadState,ActiveState,ControlGroup,KillMode',env=env)
    values=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
    if r.returncode and values.get('LoadState')!='not-found':raise ValueError('cannot inspect own service: '+r.stderr[:300])
    return values


def controls(group):
    values={n:(group/n).read_text().strip() for n in ('memory.max','memory.swap.max','pids.max','cpu.max')}
    quota,period=values['cpu.max'].split()
    if (not 0<int(values['memory.max'])<=MEMORY or values['memory.swap.max']!='0'
            or not 0<int(values['pids.max'])<=TASKS or quota=='max' or not 0<int(quota)<=int(period)):
        raise ValueError('aggregate resource limits not enforced')
    return values


def sample(group,evidence):
    for name in ('memory.events','pids.events','memory.peak','pids.peak'):
        try:
            raw=(group/name).read_text().strip()
            if name.endswith('.events'):
                values={k:int(v) for k,v in (line.split() for line in raw.splitlines())}
                dest=evidence.setdefault('observed_counters',{}).setdefault(name,{})
                for k,v in values.items():dest[k]=max(dest.get(k,0),v)
            else:evidence.setdefault('observed_counters',{})[name]=max(evidence.get('observed_counters',{}).get(name,0),int(raw))
        except FileNotFoundError:pass  # Some older kernels do not expose peak counters.


def run(command,raw,out,err,timeout,evidence):
    env=environment();unit='arquia-eval-'+uuid.uuid4().hex+'.service';group=None;proc=None
    evidence.update(controller='systemd-user/cgroup-v2',unit=unit,payload_released=False,cleanup_verified=False)
    evidence['utilities']={}
    for name in ('systemd-run','systemctl','bwrap','findmnt'):
        path=Path(shutil.which(name,path=os.defpath) or '')
        if not path.is_file():raise ValueError('required utility unavailable: '+name)
        evidence['utilities'][name]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    args=['systemd-run','--user','--no-ask-password','--quiet','--pipe','--wait','--collect','--unit='+unit,
          '--property=MemoryMax='+str(MEMORY),'--property=MemorySwapMax=0','--property=TasksMax='+str(TASKS),
          '--property=CPUQuota=100%','--property=RuntimeMaxSec=5s','--property=TimeoutStopSec=1s',
          '--property=KillMode=control-group','--property=OOMPolicy=kill','--property=NoNewPrivileges=yes',
          '--property=ExecStopPost=/usr/bin/sleep 0.05',
          '--',sys.executable,'-I','-c',GATE,shutil.which(command[0],path=os.defpath) or command[0],*command[1:]]
    stop=threading.Event();monitor=None
    try:
        proc=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=out,stderr=err,env=env)
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            state=properties(unit,env)
            if state.get('ActiveState')=='active' and state.get('ControlGroup'):
                relative=Path(state['ControlGroup'].lstrip('/'))
                if '..' in relative.parts:raise ValueError('unsafe service cgroup path')
                group=ROOT/relative
                evidence['limits']=controls(group)
                if state.get('KillMode')!='control-group':raise ValueError('group cleanup unavailable')
                break
            if proc.poll() is not None:raise ValueError('aggregate boundary did not start')
            time.sleep(.01)
        else:raise ValueError('aggregate boundary startup timeout')
        def observe():
            while not stop.wait(.01):
                try:sample(group,evidence)
                except (OSError,ValueError) as exc:evidence['counter_error']=type(exc).__name__
        sample(group,evidence);monitor=threading.Thread(target=observe,daemon=True);monitor.start()
        evidence['payload_released']=True
        try:proc.communicate(b'1'+raw,timeout=timeout)
        except subprocess.TimeoutExpired:raise ValueError('candidate timeout; no retry')
        return proc.returncode
    finally:
        stop.set()
        if monitor:monitor.join(timeout=1)
        if group is not None:
            try:sample(group,evidence)
            except (OSError,ValueError):pass
        # Every operation targets only this fresh, never-reused unit identifier.
        state=properties(unit,env)
        if state.get('LoadState')!='not-found':
            result=ctl(unit,'stop',env=env)
            evidence['stop_exit_code']=result.returncode
        if proc is not None:
            try:proc.wait(timeout=3)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=2)
            if proc.stdin is not None and not proc.stdin.closed:proc.stdin.close()
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            state=properties(unit,env)
            try:empty=group is None or 'populated 0' in (group/'cgroup.events').read_text()
            except FileNotFoundError:empty=True
            if state.get('LoadState')=='not-found' and empty:
                evidence['cleanup_verified']=True;break
            time.sleep(.01)
        evidence['process_exit_code']=proc.returncode if proc is not None else None
        if not evidence['cleanup_verified']:raise ValueError('candidate group cleanup unverified; do not retry')
