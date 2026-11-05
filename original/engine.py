"""ARQUIA-EVAL-001 bounded simulation only; NOT an ARQUIA implementation."""
from dataclasses import dataclass

@dataclass
class Grant:
    effect: str
    version: int
    active: bool = True
    finish_after_revoke: bool = False
    revoked_at: int | None = None

class Gate:
    def __init__(self):
        self.grants={}
        self.effects={}
        self.receipts=set()
        self.seq=0
        self.dispatches=0
        self.completions=0
        self.blocks=0
        self.duplicate_receipts=0
        self.orphan_receipts=0
        self.unverified_receipts=0
        self.incidents=set()

    def step(self, item):
        self.seq+=1
        op=item["op"]
        if op=="grant":
            gid,eid=item["grant"],item["effect"]
            if gid in self.grants or any(g.effect==eid for g in self.grants.values()):
                raise ValueError("Fixture requires unique grant and effect IDs")
            self.grants[gid]=Grant(eid,item.get("version",1),
                finish_after_revoke=item.get("finish_after_revoke",False))
        elif op in ("dispatch","start"):
            self._dispatch(item["grant"],item["effect"],op)
        elif op=="revoke":
            g=self.grants[item["grant"]]
            g.active=False
            g.revoked_at=self.seq
        elif op=="timeout":
            # Missing acknowledgement is NOT proof that the write failed.
            pass
        elif op=="external_commit":
            self._external_commit(item["effect"])
        elif op=="complete":
            self._complete(item["grant"],item["effect"])
        elif op=="receipt":
            self._receipt(item)
        elif op in ("recover","clear_client_cache"):
            # Recovery never triggers another write.
            pass
        else:
            raise ValueError(f"Unknown operation: {op}")

    def _dispatch(self, gid, eid, phase):
        grant=self.grants[gid]
        if not grant.active or grant.effect!=eid:
            self.blocks+=1
            return
        if eid in self.effects:
            return   # idempotence: same logical operation, no second dispatch
        self.dispatches+=1
        self.effects[eid]={"grant":gid,"phase":phase,"committed":False,
                           "outcome":"unknown","commit_at":None}

    def _external_commit(self,eid):
        e=self.effects[eid]
        if e["committed"]: return
        e["committed"]=True
        e["commit_at"]=self.seq
        grant=self.grants[e["grant"]]
        if grant.revoked_at is not None and self.seq>grant.revoked_at:
            self.incidents.add("escaped_effect_after_revocation")

    def _complete(self,gid,eid):
        g=self.grants[gid]
        e=self.effects.get(eid)
        if (g.effect!=eid or e is None or e["grant"]!=gid or
            e["phase"]!="start" or e["committed"] or
            not (g.active or g.finish_after_revoke)):
            self.blocks+=1
            return
        self.completions+=1
        e["committed"]=True
        e["commit_at"]=self.seq
        e["outcome"]="confirmed_by_local_sandbox"

    def _receipt(self,item):
        rid=item["receipt_id"]
        if rid in self.receipts:
            self.duplicate_receipts+=1
            return
        self.receipts.add(rid)
        gid,eid=item["grant"],item["effect"]
        e=self.effects.get(eid)
        g=self.grants.get(gid)
        if (e is None or g is None or e["grant"]!=gid or g.effect!=eid
            or g.version!=item.get("version",1)):
            self.orphan_receipts+=1
            return
        if item.get("source")!="independent_observer":
            self.unverified_receipts+=1
            e["outcome"]="unverified_claim"
            return
        if e["committed"]:
            e["outcome"]="confirmed_by_sandbox_observer"
        else:
            self.incidents.add("receipt_without_observed_effect")
            e["outcome"]="unknown"
        # Invariant: the receipt never modifies g.active or dispatches.

    def snapshot(self):
        return {
            "active_grants":sorted(k for k,g in self.grants.items() if g.active),
            "dispatches":self.dispatches,
            "completions":self.completions,
            "blocks":self.blocks,
            "duplicate_receipts":self.duplicate_receipts,
            "orphan_receipts":self.orphan_receipts,
            "unverified_receipts":self.unverified_receipts,
            "committed_effects":sorted(k for k,e in self.effects.items() if e["committed"]),
            "pending_effects":sorted(k for k,e in self.effects.items() if not e["committed"]),
            "outcomes":{k:e["outcome"] for k,e in sorted(self.effects.items())},
            "incidents":sorted(self.incidents)
        }

class KnownBadGate(Gate):
    """Deliberately flawed negative control: receipts resurrect revoked grants."""
    def _receipt(self,item):
        super()._receipt(item)
        grant=self.grants.get(item["grant"])
        if grant is not None and grant.effect==item["effect"]:
            grant.active=True  # Known bug; must cause suite failure
