"""Run predeclared ARQUIA-EVAL-001 vectors against a bounded reference model."""
import json
import sys
from pathlib import Path
from engine import Gate, KnownBadGate

def evaluate(cls=Gate):
    cases=json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
    results=[]
    for case in cases:
        gate=cls()
        for event in case["events"]:
            gate.step(event)
        got=gate.snapshot()
        mismatches={key:{"expected":value,"actual":got.get(key)}
                    for key,value in case["expect"].items() if got.get(key)!=value}
        results.append({"id":case["id"],"pass":not mismatches,"mismatches":mismatches,"actual":got})
    return results

if __name__=="__main__":
    is_negative="--negative-control" in sys.argv
    result=evaluate(KnownBadGate if is_negative else Gate)
    print(json.dumps({"candidate":"known_bad_negative_control" if is_negative else "bounded_reference",
                      "passed":sum(int(x["pass"]) for x in result),
                      "total":len(result),"results":result},indent=2,ensure_ascii=False))
    sys.exit(0 if all(x["pass"] for x in result) else 1)
