"""Bounded one-request JSONL process adapter; foreign code requires Linux isolation.

Bubblewrap namespaces and readonly mounts are demonstrated restrictions, not a
claim of immunity to kernel exploits. No implicit installation or network.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
from measurement import canonical,file_hash
from schemas import read_json,strict_json
from verify_package import safe_file

MAX_MESSAGE=262144
MAX_STDERR=65536
TIMEOUT=2.0
ROOT=Path(__file__).resolve().parent


def load_candidate(directory):
    directory=Path(directory).resolve();m=read_json(directory/'CANDIDATE.json')
    if set(m)!= {'schema','name','version','files','command'} or m['schema']!='arquia.candidate/1':raise ValueError('candidate manifest schema')
    if not all(isinstance(m[x],str) and 0<len(m[x])<=100 for x in ('name','version')):raise ValueError('candidate identity')
    if not isinstance(m['files'],list) or not 1<=len(m['files'])<=128 or len(m['files'])!=len(set(m['files'])):raise ValueError('candidate file inventory')
    files={n:safe_file(directory,n) for n in m['files']}
    if sum(p.stat().st_size for p in files.values())>8*1024*1024:raise ValueError('candidate exceeds 8 MiB')
    if not isinstance(m['command'],list) or not 1<=len(m['command'])<=32 or not all(isinstance(x,str) and len(x)<=1000 for x in m['command']):raise ValueError('candidate command bounds')
    if not m['command'][0].startswith(('/usr/bin/','/candidate/')):raise ValueError('executable must be in /usr/bin or /candidate')
    return m,files


def limits():
    import resource
    resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(2,2))
    resource.setrlimit(resource.RLIMIT_FSIZE,(MAX_MESSAGE,MAX_MESSAGE))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))


class JsonlCandidate:
    def __init__(self,directory=None,*,accept_external_code=False,trusted_example=False):
        self.directory=ROOT/'examples' if trusted_example else Path(directory).resolve()
        self.trusted=trusted_example
        if not trusted_example and not accept_external_code:
            raise ValueError('external execution disabled; explicit --accept-external-code required')
        if not trusted_example and (sys.platform!='linux' or not shutil.which('bwrap')):
            raise ValueError('isolation unavailable; use an authorized isolated Linux environment')
        self.manifest,self.files=load_candidate(self.directory)
        self.source_hashes={n:file_hash(p) for n,p in self.files.items()}
        self.source_hashes['CANDIDATE.json']=file_hash(self.directory/'CANDIDATE.json')
        self.state={};self.sequence=0;self.transcript=[];self.identity=None

    def export_state(self):return copy.deepcopy(self.state)
    def restore(self,state):self.state=copy.deepcopy(state)
    def close(self):pass

    def respond(self,event,view):
        self.sequence+=1
        request={'protocol':'arquia.io/1','id':self.sequence,'event':event,'context':view,'checkpoint':self.state}
        raw=canonical(request)+b'\n'
        if len(raw)>MAX_MESSAGE:raise ValueError('request exceeds 256 KiB')
        for n,p in self.files.items():
            if file_hash(p)!=self.source_hashes[n]:raise ValueError('candidate changed during run')
        if file_hash(self.directory/'CANDIDATE.json')!=self.source_hashes['CANDIDATE.json']:raise ValueError('candidate manifest changed during run')
        with tempfile.TemporaryDirectory(prefix='arquia-jsonl-') as d:
            scratch=Path(d);work=scratch/'work';work.mkdir();src=scratch/'source';src.mkdir()
            if not self.trusted:
                fs=subprocess.run(['findmnt','-n','-T',str(scratch),'-o','FSTYPE'],capture_output=True,text=True,timeout=5)
                if fs.returncode or fs.stdout.strip() in ('','tmpfs','ramfs','devtmpfs'):
                    raise ValueError('external execution scratch requires persistent storage; set TMPDIR')
            for n,p in self.files.items():
                target=src/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes());target.chmod(0o555 if p.stat().st_mode & 0o111 else 0o444)
            if self.trusted:
                command=[sys.executable,'-I',str(src/'independent_candidate.py')]
            else:
                command=['bwrap','--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL',
                    '--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib',
                    '--symlink','usr/lib64','/lib64','--proc','/proc','--dev','/dev',
                    '--ro-bind',str(src),'/candidate','--bind',str(work),'/work','--chdir','/work',
                    '--clearenv','--setenv','PATH','/usr/bin:/bin','--setenv','HOME','/work',
                    '--setenv','TMPDIR','/work','--setenv','LANG','C.UTF-8','--',*self.manifest['command']]
            outpath=scratch/'stdout';errpath=scratch/'stderr'
            with outpath.open('wb') as out,errpath.open('wb') as err:
                kwargs={'start_new_session':True} if os.name=='posix' else {}
                if sys.platform=='linux':kwargs['preexec_fn']=limits
                proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=out,stderr=err,env={'PATH':os.defpath},**kwargs)
                try:proc.communicate(raw,timeout=TIMEOUT)
                except subprocess.TimeoutExpired:
                    if os.name=='posix':os.killpg(proc.pid,signal.SIGKILL)
                    else:proc.kill()
                    proc.wait(timeout=2);raise ValueError('candidate timeout; no retry')
            output=outpath.read_bytes()[:MAX_MESSAGE+1];error=errpath.read_bytes()[:MAX_STDERR+1]
            self.transcript.append({'request':request,'stdout_sha256':__import__('hashlib').sha256(output).hexdigest(),
                'stderr_sha256':__import__('hashlib').sha256(error).hexdigest(),'exit_code':proc.returncode,
                'stdout':output.decode('utf-8',errors='replace'),'stderr':error.decode('utf-8',errors='replace')})
            if proc.returncode!=0:raise ValueError('candidate process failure: '+str(proc.returncode))
            if len(output)>MAX_MESSAGE or len(error)>MAX_STDERR:raise ValueError('candidate output capacity exceeded')
            if not output.endswith(b'\n') or output.count(b'\n')!=1:raise ValueError('expected exactly one JSONL response')
            response=strict_json(output)
            if not isinstance(response,dict) or set(response)!= {'protocol','id','candidate','response','checkpoint'}:
                raise ValueError('invalid JSONL envelope')
            if response['protocol']!='arquia.io/1' or type(response['id'])is not int or response['id']!=request['id']:
                raise ValueError('response binding mismatch')
            identity={'name':self.manifest['name'],'version':self.manifest['version']}
            if response['candidate']!=identity:raise ValueError('candidate identity changed')
            self.identity=identity;self.state=response['checkpoint']
            return response['response']
