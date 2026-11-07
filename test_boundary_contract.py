import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import process_boundary as boundary

class BoundaryContractTests(unittest.TestCase):
    def test_unlimited_or_missing_kernel_limits_are_rejected(self):
        valid={'memory.max':'268435456','memory.swap.max':'0','pids.max':'16','cpu.max':'100000 100000'}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name,value in valid.items():(root/name).write_text(value)
            self.assertEqual(boundary.controls(root),valid)
            for name,bad in [('memory.max','max'),('memory.swap.max','max'),('pids.max','max'),('cpu.max','max 100000')]:
                (root/name).write_text(bad)
                with self.assertRaises(ValueError):boundary.controls(root)
                (root/name).write_text(valid[name])
            (root/'memory.max').unlink()
            with self.assertRaises(OSError):boundary.controls(root)

    def test_unavailable_aggregate_boundary_fails_before_foreign_source_loading(self):
        from jsonl_adapter import JsonlCandidate
        with (patch('jsonl_adapter.sys.platform','linux'),patch('jsonl_adapter.shutil.which',return_value='/usr/bin/bwrap'),
              patch.object(boundary,'environment',side_effect=ValueError('aggregate unavailable')),
              patch('jsonl_adapter.load_candidate') as read):
            with self.assertRaisesRegex(ValueError,'aggregate unavailable'):JsonlCandidate('.',accept_external_code=True)
            read.assert_not_called()

    def test_failed_transport_evidence_remains_in_result(self):
        from community_runner import evaluate
        class Broken:
            def __init__(self):self.transcript=[]
            def respond(self,event,view):
                self.transcript.append({'exit_code':9,'stderr':'bounded error','resource_boundary':{'cleanup_verified':True}})
                raise ValueError('candidate process failure')
        case={'id':'transport','events':[{'op':'timeout'}],'expect':{'dispatches':0}}
        result=evaluate(Broken,[case])[0]
        self.assertFalse(result['passed']);self.assertEqual(result['evidence_sufficient'],'inconclusive')
        self.assertEqual(result['last_transport']['exit_code'],9)
        self.assertTrue(result['last_transport']['resource_boundary']['cleanup_verified'])
