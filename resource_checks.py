"""Bounded adversarial probes: at most 24 children and 320 MiB requested in total.

Run only in an authorized Linux test environment with enough free memory. The new
launcher verifies aggregate limits before allowing these probes to start.
"""
import json
from pathlib import Path
import tempfile
import unittest
from jsonl_adapter import JsonlCandidate

VIEW={'grants':{},'effects':{},'clock':0,'role':'operator','evidence_sequence':0,'incidents':[]}
FINISH='''\nprint(json.dumps({'protocol':'arquia.io/1','id':request['id'],'candidate':{'name':'probe','version':'1'},'response':{'commands':[],'observed':{'active_grants':[],'outcomes':{},'incidents':[]}},'checkpoint':{'children':len(children)}}))\n'''

class AggregateResourceTests(unittest.TestCase):
    def candidate(self,body):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup);root=Path(folder.name)
        (root/'probe.py').write_text('import os,time,json,sys\nrequest=json.loads(sys.stdin.readline())\nchildren=[]\n'+body+FINISH)
        (root/'CANDIDATE.json').write_text(json.dumps({'schema':'arquia.candidate/1','name':'probe','version':'1',
            'files':['probe.py'],'command':['/usr/bin/python3','-I','/candidate/probe.py']}))
        return JsonlCandidate(root,accept_external_code=True)

    def test_process_growth_hits_aggregate_limit_and_group_is_removed(self):
        candidate=self.candidate('''for _ in range(24):
    try:pid=os.fork()
    except OSError:break
    if pid==0:
        time.sleep(.4);os._exit(0)
    children.append(pid)
for pid in children:os.waitpid(pid,0)
''')
        candidate.respond({'op':'timeout'},VIEW)
        self.assertLess(candidate.state['children'],16)
        self.assertGreater(candidate.state['children'],0)
        boundary=candidate.transcript[-1]['resource_boundary']
        self.assertTrue(boundary['cleanup_verified']);self.assertTrue(boundary['payload_released'])
        self.assertGreater(boundary['observed_counters']['pids.events']['max'],0)
        if 'pids.peak' in boundary['observed_counters']:
            self.assertLessEqual(boundary['observed_counters']['pids.peak'],16)
        print(json.dumps({'probe':'bounded-process-growth','receipt':boundary},sort_keys=True))

    def test_memory_growth_is_aggregate_and_oom_is_not_approval(self):
        candidate=self.candidate('''for _ in range(2):
    pid=os.fork()
    if pid==0:
        allocation=bytearray(160*1024*1024)
        time.sleep(.6);os._exit(0)
    children.append(pid)
for pid in children:os.waitpid(pid,0)
''')
        with self.assertRaises(ValueError):candidate.respond({'op':'timeout'},VIEW)
        boundary=candidate.transcript[-1]['resource_boundary']
        self.assertTrue(boundary['cleanup_verified'])
        self.assertGreater(boundary['observed_counters']['memory.events']['oom_kill'],0)
        self.assertNotEqual(candidate.transcript[-1]['exit_code'],0)
        print(json.dumps({'probe':'bounded-aggregate-memory','receipt':boundary},sort_keys=True))

    def test_detached_descendants_are_removed_after_timeout(self):
        candidate=self.candidate('''pid=os.fork()
if pid==0:
    os.setsid();time.sleep(10);os._exit(0)
children.append(pid)
time.sleep(10)
''')
        with self.assertRaisesRegex(ValueError,'timeout'):candidate.respond({'op':'timeout'},VIEW)
        boundary=candidate.transcript[-1]['resource_boundary']
        self.assertTrue(boundary['cleanup_verified'])
        self.assertEqual(len(candidate.transcript),1)
        print(json.dumps({'probe':'detached-descendant-cleanup','receipt':boundary},sort_keys=True))

if __name__=='__main__':unittest.main()
