"""Author-side bounded model. No network, real effects, or cryptographic witness."""
import copy
import hashlib
import json


def request_hash(effect, request):
    """Logical request binding, independent of a transport's receipt identifier."""
    raw = json.dumps([effect, request], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


class Gate:
    def __init__(self):
        self.grants = {}
        self.effects = {}
        self.receipts = {}
        self.accepted_bindings = set()
        self.incidents = set()
        self.seq = 0
        self.dispatches = self.completions = self.blocks = 0
        self.duplicate_receipts = self.orphan_receipts = self.unverified_receipts = 0
        self.conflicting_receipts = 0

    def step(self, item):
        self.seq += 1
        op = item["op"]
        if op == "grant":
            gid, eid = item["grant"], item["effect"]
            if gid in self.grants or any(g["effect"] == eid for g in self.grants.values()):
                raise ValueError("Grants and logical effect IDs must be unique in this fixture")
            request = item.get("request", "synthetic-request")
            self.grants[gid] = dict(effect=eid, version=item.get("version", 1), active=True,
                finish_after_revoke=item.get("finish_after_revoke", False), revoked_at=None,
                request=request, request_hash=request_hash(eid, request))
        elif op in ("dispatch", "start"):
            self._dispatch(item, op)
        elif op == "revoke":
            g = self.grants[item["grant"]]
            g["active"] = False
            if g["revoked_at"] is None:
                g["revoked_at"] = self.seq
        elif op == "external_commit":
            self._external_commit(item)
        elif op == "complete":
            self._complete(item)
        elif op == "receipt":
            self._receipt(item)
        elif op in ("timeout", "recover", "clear_client_cache"):
            # Transport uncertainty never initiates a write. Runner performs reconstruction.
            pass
        else:
            raise ValueError("Unknown operation: " + op)

    def _dispatch(self, item, phase):
        gid, eid = item["grant"], item["effect"]
        g = self.grants.get(gid)
        if (g is None or not g["active"] or g["effect"] != eid or
            item.get("request", g["request"]) != g["request"]):
            self.blocks += 1
            return
        if eid in self.effects:
            return
        self.dispatches += 1
        self.effects[eid] = dict(grant=gid, phase=phase, committed=False, commit_at=None,
            outcome="unknown", execution_order="undetermined", request_hash=g["request_hash"])

    def _external_commit(self, item):
        e = self.effects[item["effect"]]
        if e["committed"]:
            return
        e["committed"] = True
        e["commit_at"] = self.seq
        g = self.grants[e["grant"]]
        order = item.get("ordering", "simulator_sequence")
        if order not in ("simulator_sequence", "undetermined"):
            raise ValueError("Unsupported ordering witness")
        if order == "undetermined":
            e["execution_order"] = "undetermined"
            self.incidents.add("execution_order_undetermined")
        elif g["revoked_at"] is None:
            e["execution_order"] = "before_revocation"
        else:
            e["execution_order"] = "after_revocation"
            if not (e["phase"] == "start" and g["finish_after_revoke"]):
                self.incidents.add("escaped_effect_after_revocation")

    def _complete(self, item):
        gid, eid = item["grant"], item["effect"]
        g, e = self.grants.get(gid), self.effects.get(eid)
        if (g is None or e is None or g["effect"] != eid or e["grant"] != gid or
            e["phase"] != "start" or e["committed"] or
            not (g["active"] or g["finish_after_revoke"])):
            self.blocks += 1
            return
        self.completions += 1
        e["committed"] = True
        e["commit_at"] = self.seq
        e["execution_order"] = "before_revocation" if g["revoked_at"] is None else "after_revocation"
        e["outcome"] = "confirmed_by_local_sandbox"

    def _receipt(self, item):
        gid, eid = item["grant"], item["effect"]
        e, g = self.effects.get(eid), self.grants.get(gid)
        if (e is None or g is None or e["grant"] != gid or g["effect"] != eid or
            g["version"] != item.get("version", 1) or
            item.get("request_hash") != g["request_hash"]):
            self.orphan_receipts += 1
            return
        # These labels represent synthetic test actors, never real authentication.
        if item.get("source") != "independent_observer":
            self.unverified_receipts += 1
            if not e["outcome"].startswith("confirmed_"):
                e["outcome"] = "unverified_claim"
            return
        binding = (gid, eid, g["version"], g["request_hash"])
        rid = item["receipt_id"]
        if rid in self.receipts and self.receipts[rid] != binding:
            self.conflicting_receipts += 1
            self.incidents.add("receipt_id_conflict")
            return
        if binding in self.accepted_bindings:
            self.receipts[rid] = binding
            self.duplicate_receipts += 1
            return
        if not e["committed"]:
            # Failed evidence cannot poison the future valid observation's key.
            self.incidents.add("receipt_without_observed_effect")
            return
        self.receipts[rid] = binding
        self.accepted_bindings.add(binding)
        e["outcome"] = "confirmed_by_sandbox_observer"

    def snapshot(self):
        return dict(active_grants=sorted(k for k, g in self.grants.items() if g["active"]),
            dispatches=self.dispatches, completions=self.completions, blocks=self.blocks,
            duplicate_receipts=self.duplicate_receipts, orphan_receipts=self.orphan_receipts,
            unverified_receipts=self.unverified_receipts, conflicting_receipts=self.conflicting_receipts,
            committed_effects=sorted(k for k, e in self.effects.items() if e["committed"]),
            pending_effects=sorted(k for k, e in self.effects.items() if not e["committed"]),
            outcomes={k: e["outcome"] for k, e in sorted(self.effects.items())},
            execution_order={k: e["execution_order"] for k, e in sorted(self.effects.items())},
            incidents=sorted(self.incidents))

    def export_state(self):
        state = copy.deepcopy(self.__dict__)
        state["incidents"] = sorted(self.incidents)
        state["accepted_bindings"] = sorted(self.accepted_bindings)
        return dict(schema=1, state=state)

    @classmethod
    def from_state(cls, data):
        if data.get("schema") != 1:
            raise ValueError("Unknown checkpoint schema")
        obj = cls()
        obj.__dict__.update(copy.deepcopy(data["state"]))
        obj.incidents = set(obj.incidents)
        obj.accepted_bindings = {tuple(x) for x in obj.accepted_bindings}
        obj.receipts = {k: tuple(v) for k, v in obj.receipts.items()}
        return obj


class ReceiptRenewal(Gate):
    """Negative control: renews a revoked grant upon receipt."""
    def _receipt(self, item):
        super()._receipt(item)
        if item["grant"] in self.grants:
            self.grants[item["grant"]]["active"] = True


class BlindRecovery(Gate):
    """Negative control: retries every unresolved attempt after recovery."""
    def step(self, item):
        super().step(item)
        if item["op"] == "recover":
            self.dispatches += sum(not e["committed"] for e in self.effects.values())


class CompletionBypass(Gate):
    """Negative control: completes under a revoked hard-stop grant."""
    def _complete(self, item):
        g = self.grants.get(item["grant"])
        old = g["active"] if g else False
        if g:
            g["active"] = True
        super()._complete(item)
        if g:
            g["active"] = old


class HideEscape(Gate):
    """Negative control: erases the incident after an escaped external effect."""
    def _external_commit(self, item):
        super()._external_commit(item)
        self.incidents.discard("escaped_effect_after_revocation")


class RecoveryLosesRevocation(Gate):
    """Negative control: reloads cached authorization as active."""
    @classmethod
    def from_state(cls, data):
        obj = super().from_state(data)
        for g in obj.grants.values():
            g["active"] = True
        return obj
