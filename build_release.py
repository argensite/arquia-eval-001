"""Regenerate author-side reports and a deterministic ZIP. No network operations."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent


def run_report(args, dest, expected_exit):
    r = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != expected_exit:
        raise RuntimeError(f"Unexpected exit {r.returncode}: {args}\n{r.stderr}")
    report = json.loads(r.stdout)
    dest.write_text(r.stdout, encoding="utf-8")
    return dict(exit_code=r.returncode, passed=report["passed"], total=report["total"],
                report=str(dest.relative_to(ROOT)))


def main():
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    summary = dict(evidence="project-side execution, not independent evaluation",
                   operator="Native Qwen executing authentic ChatGPT advice for Jose Maria Garbini", version=(ROOT / "VERSION").read_text().strip())
    summary["original_reference"] = run_report(["original/runner.py"], out / "original-reference.json", 0)
    summary["original_negative_control"] = run_report(["original/runner.py", "--negative-control"], out / "original-negative.json", 1)
    summary["reference"] = run_report(["runner.py", "--evaluator", "project-side-native-Qwen-ChatGPT"], out / "reference.json", 0)
    from runner import MUTANTS
    summary["negative_controls"] = {}
    for name in MUTANTS:
        summary["negative_controls"][name] = run_report(["runner.py", "--negative-control", name,
            "--evaluator", "project-side-native-Qwen-ChatGPT"], out / (name + ".json"), 1)
    spec = importlib.util.spec_from_file_location("original_gate_for_audit", ROOT / "original/engine.py")
    original = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = original
    spec.loader.exec_module(original)
    counterexamples = []
    for case in json.loads((ROOT / "cases.json").read_text()):
        if case["id"].split("-")[0] not in {"C14", "C15", "C16", "C23", "C25", "C28"}:
            continue
        obj = original.Gate()
        for event in case["events"]:
            obj.step(event)
        got = obj.snapshot()
        compared = {k:v for k,v in case["expect"].items() if k != "execution_order"}
        mismatch = {k:dict(expected=v, actual=got.get(k)) for k,v in compared.items() if got.get(k) != v}
        counterexamples.append(dict(case=case["id"], expected=compared, actual=got, mismatches=mismatch))
    (out / "original-added-counterexamples.json").write_text(json.dumps(counterexamples, indent=2) + "\n")
    summary["original_added_counterexamples"] = sum(bool(x["mismatches"]) for x in counterexamples)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    files = sorted(p for p in ROOT.rglob("*") if p.is_file()
        and not any(part in {".git", "__pycache__", "dist"} for part in p.relative_to(ROOT).parts)
        and p.name not in {"CHECKSUMS.sha256", "independent_result.json", "negative_result.json"}
        and p.suffix not in {".pyc", ".pyo"})
    manifest = ROOT / "CHECKSUMS.sha256"
    manifest.write_text("".join(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.relative_to(ROOT).as_posix() + "\n" for p in files))
    files.append(manifest)
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / ("ARQUIA-EVAL-001-v" + (ROOT / "VERSION").read_text().strip() + ".zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):
            info = zipfile.ZipInfo(("ARQUIA-EVAL-001-v" + (ROOT / "VERSION").read_text().strip() + "/") + p.relative_to(ROOT).as_posix(), (2026,11,5,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, p.read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dist / (archive.name + ".sha256")).write_text(digest + "  " + archive.name + "\n")
    print(json.dumps(dict(summary=summary, archive=str(archive), sha256=digest, files=len(files)), indent=2))


if __name__ == "__main__":
    main()
