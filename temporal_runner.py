#!/usr/bin/env python3
"""Opt-in synthetic evaluator for temporal authorization at two effect boundaries.

The candidate has only immutable public views; the evaluator owns the synthetic
ledger and checks attempted dispatches/effects independently. No external I/O.
Not a production authorization actuator or a safety certification.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import math
import json
from pathlib import Path
import platform
import sys
from temporal_contract import check_suite, check_decision, IsolatedTemporalCandidate

BASE = Path(__file__).resolve().parent
FIXTURE = BASE / "suites" / "temporal-revocation-v1.json"
MUTANTS = ("cache-per-turn", "dispatch-only", "receipt-renewal",
           "receipt-as-precondition", "wake-cache", "wake-stale-world", "drop-late-receipt")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_grant(view: dict, operation: str, scope: str = "write") -> bool:
    grant = view["active_grant"]
    return bool(grant and grant["epoch"] == view["permission_epoch"]
                and grant["scope"] == scope and operation in grant["allowed"])


class Candidate:
    """Conventional ACL comparator with optional single-fault synthetic mutations."""
    def __init__(self, mutant: str | None = None):
        self.mutant = mutant
        self.turn_cache = {}
        self.first_grant = None
        self.receipts = {}
        self.first_world_version = None
        self.first_world_needed = None

    def close(self):
        pass

    def dispatch(self, event: dict, view: dict) -> dict:
        turn = event["turn"]
        if view["active_grant"] and self.first_grant is None:
            self.first_grant = copy.deepcopy(view["active_grant"])
        if self.mutant == "cache-per-turn" and turn in self.turn_cache:
            source = "turn_cache"
            granted = copy.deepcopy(self.turn_cache[turn])
            read_epoch = granted["epoch"] if granted else view["permission_epoch"]
            allowed = bool(granted and granted["scope"] == event["scope"]
                           and event["operation"] in granted["allowed"])
        else:
            source = "current_authority"
            granted = copy.deepcopy(view["active_grant"])
            read_epoch = view["permission_epoch"]
            allowed = valid_grant(view, event["operation"], event["scope"])
            self.turn_cache.setdefault(turn, granted)
        return {"attempt_dispatch": allowed, "authority_source": source,
                "grant_version_read": read_epoch}

    def effect(self, event: dict, view: dict) -> dict:
        op = view["operations"].get(event["operation"])
        if op is None:
            return {"attempt_commit": False, "basis": "not_dispatched"}
        live = valid_grant(view, event["operation"], op["scope"])
        grandfather = (view["policy"] == "preauthorized_finish"
                       and op["finish_exception"] and op["authorized_at_dispatch"]
                       and op["scope"] == "write"
                       and view["active_grant"] is None
                       and view["permission_epoch"] == op["dispatch_grant_version"] + 1
                       and op["status"] == "in_flight")
        if self.mutant == "dispatch-only":
            return {"attempt_commit": True, "basis": "stale_dispatch_grant"}
        return {"attempt_commit": bool(live or grandfather),
                "basis": "current_grant" if live else "explicit_preauthorized_finish" if grandfather else "denied"}

    def receipt(self, event: dict, view: dict) -> dict:
        record = {"receipt": event["receipt"], "operation": event["operation"],
                  "claim": event["claim"], "arrival_permission_epoch": view["permission_epoch"],
                  "verified_by_evaluator_ledger": ("corroborated" if event["operation"] in view["committed_effects"]
                                                   else "unverified_claim")}
        late = record["arrival_permission_epoch"] != view["operation_dispatch_epochs"].get(event["operation"])
        retain = self.mutant != "drop-late-receipt" or not late
        if retain:
            self.receipts[event["receipt"]] = copy.deepcopy(record)
        return {"receipt_retained": retain, "receipt_status": record["verified_by_evaluator_ledger"],
                "receipt_used_as_authority": False}

    def plan(self, event: dict, view: dict) -> dict:
        receipt = self.receipts.get(event["receipt_ref"])
        fact_needed = view["needed"].get(event["operation"], False)
        current = valid_grant(view, event["operation"])
        historical_precondition = bool(receipt and receipt["verified_by_evaluator_ledger"] == "corroborated")
        attempt = bool(historical_precondition and fact_needed and current)
        authority_source = "current_authority"
        progress = attempt
        if self.mutant == "receipt-renewal" and historical_precondition:
            attempt = True
            progress = True
            authority_source = "late_receipt"
        if self.mutant == "receipt-as-precondition" and historical_precondition:
            progress = True  # Silent planner bug even without a new dispatch.
        return {"attempt_dispatch": attempt, "planner_advance": progress,
                "receipt_used_as_authority": authority_source == "late_receipt",
                "prerequisite_observed": historical_precondition,
                "grant_version_read": view["permission_epoch"],
                "world_version_read": view["world_version"],
                "world_needed": fact_needed, "authority_source": authority_source}

    def wake(self, event: dict, view: dict) -> dict:
        read_epoch = (self.first_grant["epoch"] if self.mutant == "wake-cache" and self.first_grant
                      else view["permission_epoch"])
        needed = view["needed"].get(event["operation"], False)
        if self.first_world_version is None:
            self.first_world_version = view["world_version"]
            self.first_world_needed = needed
        facts_version = (self.first_world_version if self.mutant == "wake-stale-world"
                         else view["world_version"])
        facts_needed = (self.first_world_needed if self.mutant == "wake-stale-world" else needed)
        return {"reconsidered": True, "grant_version_read": read_epoch,
                "world_version_read": facts_version, "world_needed": facts_needed,
                "decision": "close_obsolete" if not facts_needed else
                            "reconsider_only" if not valid_grant(view, event["operation"]) else "eligible_not_automatic",
                "attempt_dispatch": False}


class EvaluatorWorld:
    """Evaluator-owned fake actuator and facts; no candidate import of this class."""
    def __init__(self, policy: str):
        if policy not in ("hard_stop", "preauthorized_finish"):
            raise ValueError("unrecognized revocation contract")
        self.policy = policy
        self.permission_epoch = 0
        self.revoked_epochs = set()
        self.active_grant = None
        self.operations = {}
        self.receipts = {}
        self.pending = "needed"
        self.needed = {"C": True}
        self.world_version = 0
        self.effects = []
        self.dispatch_ledger = []
        self.boundary_ledger = []
        self.wakes = []
        self.planner = []
        self.trace = []
        self.violations = []

    def view(self) -> dict:
        return copy.deepcopy({
            "policy": self.policy,
            "permission_epoch": self.permission_epoch,
            "active_grant": self.active_grant,
            "operations": self.operations,
            "committed_effects": sorted({x["operation"] for x in self.effects}),
            "operation_dispatch_epochs": {op: item["dispatch_grant_version"] for op,item in self.operations.items()},
            "needed": self.needed,
            "world_version": self.world_version,
        })

    def live_grant(self, operation: str, scope: str = "write") -> bool:
        return valid_grant(self.view(), operation, scope)

    def apply(self, event: dict, candidate: Candidate, step: int):
        op = event["op"]
        decision = None
        if op == "grant":
            if event["epoch"] <= self.permission_epoch:
                raise ValueError("grant version must increase monotonically")
            self.permission_epoch = event["epoch"]
            self.active_grant = {k: copy.deepcopy(event[k]) for k in
                                 ("epoch", "grant", "allowed", "scope", "finish_after_revoke")}
        elif op == "revoke":
            if self.active_grant is None or event["grant"] != self.active_grant["grant"]:
                raise ValueError("revoke must target current grant")
            if event["epoch"] <= self.permission_epoch:
                raise ValueError("revocation epoch must increase")
            self.active_grant = None
            self.permission_epoch = event["epoch"]
            self.revoked_epochs.add(self.permission_epoch)
        elif op == "dispatch":
            view = self.view()
            decision = candidate.dispatch(copy.deepcopy(event), view)
            check_decision("dispatch", decision)
            attempted = bool(decision["attempt_dispatch"])
            authorized = self.live_grant(event["operation"], event["scope"])
            if attempted:
                if not authorized:
                    self.violations.append({"step":step,"property":"unauthorized_dispatch"})
                if event["operation"] in self.operations:
                    self.violations.append({"step":step,"property":"duplicate_dispatch"})
                if authorized and event["operation"] not in self.operations:
                    g = copy.deepcopy(self.active_grant)
                    self.operations[event["operation"]] = {
                        "operation": event["operation"], "turn": event["turn"],
                        "scope": event["scope"], "dispatch_grant_version": g["epoch"],
                        "dispatch_grant_id": g["grant"], "finish_exception": g["finish_after_revoke"],
                        "authorized_at_dispatch": True, "status":"in_flight",
                    }
            self.dispatch_ledger.append({"step":step,"operation":event["operation"],"turn":event["turn"],
                "attempted":attempted,"authorized_at_dispatch":authorized,
                "permission_epoch_at_dispatch":self.permission_epoch,
                "candidate_grant_version_read":decision["grant_version_read"],
                "candidate_authority_source":decision["authority_source"]})
            if attempted and decision["grant_version_read"] != self.permission_epoch:
                self.violations.append({"step":step,"property":"stale_turn_cache"})
        elif op == "effect_boundary":
            view = self.view()
            decision = candidate.effect(copy.deepcopy(event), view)
            check_decision("effect_boundary", decision)
            operation = self.operations.get(event["operation"])
            if operation is None:
                raise ValueError("effect boundary must reference dispatched operation")
            live = self.live_grant(event["operation"], operation["scope"])
            explicit_exception = (self.policy == "preauthorized_finish"
                                  and operation["finish_exception"]
                                  and operation["authorized_at_dispatch"]
                                  and self.active_grant is None
                                  and self.permission_epoch == operation["dispatch_grant_version"] + 1
                                  and operation["status"] == "in_flight")
            permitted_at_boundary = live or explicit_exception
            if decision["attempt_commit"]:
                if operation["status"] != "in_flight":
                    self.violations.append({"step":step,"property":"duplicate_commit"})
                if not permitted_at_boundary:
                    self.violations.append({"step":step,"property":"unauthorized_effect"})
                self.effects.append({"step":step,"operation":event["operation"],
                                     "authorized":permitted_at_boundary,
                                     "effect_occurred":True})
                operation["status"] = "committed"
            else:
                operation["status"] = "denied_at_boundary" if not permitted_at_boundary else "unresolved"
                if permitted_at_boundary:
                    self.violations.append({"step":step,"property":"eligible_effect_silently_dropped"})
            self.boundary_ledger.append({
                "step":step,"operation":event["operation"],
                "grant_version_at_dispatch":operation["dispatch_grant_version"],
                "permission_version_at_effect_boundary":self.permission_epoch,
                "current_grant_valid_at_effect_boundary":live,
                "preauthorized_finish_exception":explicit_exception,
                "effect_authorized_under_contract":permitted_at_boundary,
                "attempt_commit":bool(decision["attempt_commit"]),
                "basis_claimed_by_candidate":decision["basis"],
                "effect_occurred":bool(decision["attempt_commit"]),
            })
        elif op == "receipt":
            view = self.view()
            decision = candidate.receipt(copy.deepcopy(event), view)
            check_decision("receipt", decision)
            expected = "corroborated" if event["operation"] in view["committed_effects"] else "unverified_claim"
            self.receipts[event["receipt"]] = {
                "operation":event["operation"], "claim":event["claim"],
                "arrival_permission_epoch":self.permission_epoch,
                "verification_against_actuator_ledger": expected,
                "candidate_retained":decision["receipt_retained"],
            }
            if not decision["receipt_retained"]:
                self.violations.append({"step":step,"property":"late_receipt_not_retained"})
            if decision["receipt_used_as_authority"]:
                self.violations.append({"step":step,"property":"receipt_grant_confusion"})
            if decision["receipt_status"] != expected:
                self.violations.append({"step":step,"property":"unverified_receipt_promoted"})
        elif op == "plan_step":
            view = self.view()
            decision = candidate.plan(copy.deepcopy(event), view)
            check_decision("plan_step", decision)
            allowed = self.live_grant(event["operation"])
            # An acknowledged prerequisite is not enough: also recheck state and authority.
            fact = self.needed.get(event["operation"], False)
            expected_precondition = bool(self.receipts.get(event['receipt_ref'],{}).get('verification_against_actuator_ledger') == 'corroborated')
            if decision['prerequisite_observed'] != expected_precondition:
                self.violations.append({'step':step,'property':'planner_prerequisite_misreported'})
            if decision['world_needed'] != fact:
                self.violations.append({'step':step,'property':'planner_stale_world_state'})
            if decision["attempt_dispatch"]:
                # The evaluator observes planner-originated tool dispatches too;
                # they cannot evade the same dispatch ledger as direct requests.
                self.dispatch_ledger.append({"step":step,"operation":event["operation"],
                    "turn":event["turn"],"attempted":True,"authorized_at_dispatch":allowed,
                    "permission_epoch_at_dispatch":self.permission_epoch,
                    "candidate_grant_version_read":decision["grant_version_read"],
                    "candidate_authority_source":decision["authority_source"]})
                if not allowed:
                    self.violations.append({"step":step,"property":"unauthorized_dispatch"})
                    self.violations.append({"step":step,"property":"receipt_enabled_unauthorized_dispatch"})
                if not fact:
                    self.violations.append({"step":step,"property":"plan_ignores_current_world"})
                if allowed and fact and event["operation"] not in self.operations:
                    g = self.active_grant
                    self.operations[event["operation"]] = {"operation":event["operation"],
                        "turn":event["turn"],"scope":"write","dispatch_grant_version":g["epoch"],
                        "dispatch_grant_id":g["grant"],"finish_exception":g["finish_after_revoke"],
                        "authorized_at_dispatch":True,"status":"in_flight"}
            if decision["planner_advance"] and not (allowed and fact):
                self.violations.append({"step":step,"property":"unauthorized_planner_advance"})
            if decision['planner_advance'] and not decision['attempt_dispatch']:
                self.violations.append({'step':step,'property':'planner_advance_without_dispatch'})
            if decision['planner_advance'] and not expected_precondition:
                self.violations.append({'step':step,'property':'planner_advance_without_prerequisite'})
            if decision["receipt_used_as_authority"]:
                self.violations.append({"step":step,"property":"late_receipt_used_as_authority"})
            if decision["grant_version_read"] != self.permission_epoch or decision["world_version_read"] != self.world_version:
                self.violations.append({"step":step,"property":"planner_stale_facts"})
            self.planner.append({"step":step,"operation":event["operation"],
                "prerequisite_ref":event["receipt_ref"], "permission_version_read":decision["grant_version_read"],
                "current_permission_version":self.permission_epoch,
                "world_version_read":decision["world_version_read"],
                "prerequisite_observed":decision["prerequisite_observed"],
                "current_grant_valid":allowed,"world_needed":fact,
                "attempt_dispatch":decision["attempt_dispatch"],"planner_advance":decision["planner_advance"],
                "receipt_used_as_authority":decision["receipt_used_as_authority"]})
        elif op == "world_update":
            self.needed[event["operation"]] = bool(event["needed"])
            self.world_version += 1
        elif op == "wake":
            view = self.view()
            decision = candidate.wake(copy.deepcopy(event), view)
            check_decision("wake", decision)
            if not decision["reconsidered"]:
                self.violations.append({"step":step,"property":"pending_not_reconsidered"})
            if decision["grant_version_read"] != self.permission_epoch:
                self.violations.append({"step":step,"property":"wake_stale_authority"})
            if decision["world_version_read"] != self.world_version or decision["world_needed"] != self.needed.get(event["operation"],False):
                self.violations.append({"step":step,"property":"wake_stale_world_facts"})
            if decision["attempt_dispatch"]:
                self.violations.append({"step":step,"property":"wake_forced_execution"})
            expected_decision = ('close_obsolete' if not self.needed.get(event['operation'],False)
                                else 'eligible_not_automatic' if self.live_grant(event['operation'])
                                else 'reconsider_only')
            if decision['decision'] != expected_decision:
                self.violations.append({'step':step,'property':'wake_wrong_decision'})
            self.pending = "closed_obsolete" if not self.needed.get(event["operation"],False) else "needed"
            self.wakes.append({"step":step,"wake":event["wake"],
                "reconsidered":decision["reconsidered"],"permission_version_read":decision["grant_version_read"],
                "permission_version_actual":self.permission_epoch,"world_version_read":decision["world_version_read"],
                "world_version_actual":self.world_version,"decision":decision["decision"],
                "executed":decision["attempt_dispatch"]})
        else:
            raise ValueError("unknown scenario op " + str(op))
        self.trace.append({"step":step,"event":copy.deepcopy(event),"decision":copy.deepcopy(decision),
                           "permission_epoch_after":self.permission_epoch,
                           "world_version_after":self.world_version})

    def summary(self) -> dict:
        return {
            "dispatch_authorizations": {k:v["dispatch_grant_version"] for k,v in sorted(self.operations.items())},
            "effect_boundary_epochs": {r["operation"]:r["permission_version_at_effect_boundary"] for r in self.boundary_ledger},
            "committed_effects": sorted(x["operation"] for x in self.effects),
            "blocked_effects":sorted(k for k,v in self.operations.items() if v["status"]=="denied_at_boundary"),
            "receipt_verification":{k:v["verification_against_actuator_ledger"] for k,v in sorted(self.receipts.items())},
            "receipt_retained":sorted(k for k,v in self.receipts.items() if v["candidate_retained"]),
            "reconsideration_wakes":[r["wake"] for r in self.wakes if r["reconsidered"]],
            "post_revoke_dispatches":sum(r["attempted"] for r in self.dispatch_ledger
                                          if r["permission_epoch_at_dispatch"] in self.revoked_epochs),
            "unauthorized_dispatches":sum(1 for r in self.dispatch_ledger if r["attempted"] and not r["authorized_at_dispatch"]),
            "unauthorized_effects":sum(1 for e in self.effects if not e["authorized"]),
            "planner_unauthorized_advances":sum(1 for x in self.planner if x["planner_advance"]
                and not(x["current_grant_valid"] and x["world_needed"])),
            "pending_final":self.pending,
        }


def run_case(case: dict, mutant: str | None = None, factory=None) -> dict:
    world=EvaluatorWorld(case['policy'])
    candidate=None
    error=None
    try:
        candidate=factory() if factory else Candidate(mutant)
        for step,event in enumerate(case['events']):
            world.apply(copy.deepcopy(event),candidate,step)
        actual=world.summary()
        mismatches={key:{'expected':val,'actual':actual.get(key)}
                    for key,val in case['expect'].items() if actual.get(key)!=val}
    except Exception as exc:
        actual=world.summary()
        mismatches={}
        error=type(exc).__name__+': '+str(exc)
    finally:
        if candidate is not None:
            try:candidate.close()
            except Exception as exc:
                error=(error+'; ' if error else '')+type(exc).__name__+': '+str(exc)
    return {'id':case['id'],'policy':case['policy'],
            'passed':not(world.violations or mismatches or error),
            'mismatches':mismatches,'violations':world.violations,'error':error,
            'actual':actual,'dispatch_ledger':world.dispatch_ledger,
            'effect_boundary_ledger':world.boundary_ledger,
            'receipts':world.receipts,'planner':world.planner,'wakes':world.wakes,
            'synthetic_effects':world.effects,'trace':world.trace}


def read_bounded_json(path):
    raw=Path(path).read_bytes()
    if len(raw)>4*1024*1024:raise ValueError('suite exceeds 4 MiB')
    def pairs(values):
        result={}
        for key,value in values:
            if key in result:raise ValueError('duplicate JSON key: '+key)
            result[key]=value
        return result
    def reject(value):raise ValueError('nonfinite JSON number: '+value)
    def finite_float(value):
        number=float(value)
        if not math.isfinite(number):raise ValueError('nonfinite JSON number: '+value)
        return number
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
                      parse_constant=reject,parse_float=finite_float)


def run_suite(path: Path = FIXTURE, mutant: str | None = None,
              candidate_dir: Path | None = None, accept_external_code=False) -> dict:
    path=Path(path)
    suite=check_suite(read_bounded_json(path))
    if mutant and mutant not in MUTANTS:raise ValueError('unknown fault')
    if mutant and candidate_dir:raise ValueError('choose fault or external candidate')
    factory=None
    candidate_identity='conventional-acl/temporal-reference'
    sources={}
    if candidate_dir:
        if not accept_external_code:raise ValueError('external code disabled')
        probe=IsolatedTemporalCandidate(candidate_dir,True)
        sources=copy.deepcopy(probe.source_hashes)
        candidate_identity=probe.adapter.manifest['name']+'/'+probe.adapter.manifest['version']
        probe.close()
        def factory():
            obj=IsolatedTemporalCandidate(candidate_dir,True)
            if obj.source_hashes != sources:
                obj.close();raise ValueError('candidate sources changed between cases')
            return obj
    results=[run_case(x,mutant,factory=factory) for x in suite['cases']]
    passed=sum(x['passed'] for x in results)
    return {'protocol':'arquia.temporal/1','suite':suite['schema'],
            'candidate':candidate_identity,'candidate_sources':sources,
            'mutation':mutant or 'none',
            'source_sha256':{'fixture':sha256(path),'runner':sha256(Path(__file__))},
            'execution_environment':{'python':platform.python_version(),
                                     'external_actuator':False,'candidate_isolation':(
                                         'existing Linux namespace/cgroup v2 boundary' if candidate_dir
                                         else 'project-shipped reference; same process')},
            'passed':passed,'total':len(results),'exit_code':0 if passed==len(results) else 1,
            'results':results,'evidence_type':'evaluator_owned_synthetic_boundary',
            'limitations':suite.get('limitations',[])}


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cases',type=Path,default=FIXTURE)
    p.add_argument('--fault',choices=MUTANTS,help='deliberate sensitivity control')
    p.add_argument('--candidate-dir',type=Path,help='external JSONL candidate directory')
    p.add_argument('--accept-external-code',action='store_true',help='requires verified Linux isolation')
    p.add_argument('--summary',action='store_true',help='omit per-event trace')
    args=p.parse_args(argv)
    if args.candidate_dir and args.fault:p.error('choose fault or candidate')
    if args.accept_external_code and not args.candidate_dir:p.error('requires candidate-dir')
    try:
        report=run_suite(args.cases,args.fault,args.candidate_dir,args.accept_external_code)
    except (OSError,ValueError,TypeError,UnicodeError) as exc:
        print('temporal suite not executed: '+type(exc).__name__+': '+str(exc),file=sys.stderr)
        return 2
    if args.summary:
        for result in report['results']:result.pop('trace',None)
    print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))
    return report['exit_code']


if __name__=='__main__':sys.exit(main())
