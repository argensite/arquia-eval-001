"""Linux-only acceptance suite: run explicitly; unavailable isolation is a failure."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonl_adapter import JsonlCandidate

class IsolationTests(unittest.TestCase):
    def candidate(self,body):
        tmp=tempfile.TemporaryDirectory(prefix='arquia-isolation-test-');self.addCleanup(tmp.cleanup)
        root=Path(tmp.name);(root/'probe.py').write_text(body)
        (root/'CANDIDATE.json').write_text(json.dumps({'schema':'arquia.candidate/1','name':'probe','version':'1',
            'files':['probe.py'],'command':['/usr/bin/python3','-I','/candidate/probe.py']}))
        return JsonlCandidate(root,accept_external_code=True)

    def test_host_files_environment_network_and_mount_boundary(self):
        c=self.candidate('''import os,sys,json,socket
r=json.loads(sys.stdin.readline())
assert 'ARQUIA_TEST_PRIVATE' not in os.environ
assert not os.path.exists('/home/jose-maria-garbini')
assert not os.path.exists('/run/user')
try:
 open('/usr/arquia-isolation-probe','w').write('x')
 raise AssertionError('system mount writable')
except OSError: pass
for path in ('/work/unaccounted-file','/unaccounted-file','/dev/unaccounted-file'):
 try:
  open(path,'w').write('x')
  raise AssertionError('unexpected writable filesystem: '+path)
 except OSError: pass
# An isolated network namespace has no default route. No outbound connection is attempted.
lines=open('/proc/net/route').read().splitlines()
assert len(lines)==1,lines
print(json.dumps({'protocol':'arquia.io/1','id':r['id'],'candidate':{'name':'probe','version':'1'},'response':{'commands':[],'observed':{'active_grants':[],'outcomes':{},'incidents':[]}},'checkpoint':{}}))
''')
        with patch.dict(os.environ,{'ARQUIA_TEST_PRIVATE':'synthetic marker'}):
            result=c.respond({'op':'timeout'},{})
        self.assertEqual(result['commands'],[])

    def test_unverified_cgroup_never_releases_payload(self):
        c=self.candidate('print("payload must stay blocked")')
        with patch('process_boundary.controls',side_effect=ValueError('invalid kernel quota')):
            with self.assertRaisesRegex(ValueError,'invalid kernel quota'):c.respond({'op':'timeout'},{})
        receipt=c.transcript[-1]
        self.assertFalse(receipt['resource_boundary']['payload_released'])
        self.assertTrue(receipt['resource_boundary']['cleanup_verified'])
        self.assertEqual(receipt['stdout'],'')

    def test_timeout_fails_and_is_not_retried(self):
        c=self.candidate('import time\ntime.sleep(20)\n')
        with self.assertRaisesRegex(ValueError,'timeout'):
            c.respond({'op':'timeout'},{})
        self.assertEqual(c.sequence,1)

    def test_malformed_extra_and_oversized_output_fail(self):
        for body in ('print("{}")','print("{}\\n{}")','print("x"*300000)'):
            with self.subTest(body=body):
                c=self.candidate(body)
                with self.assertRaises(ValueError):c.respond({'op':'timeout'},{})
