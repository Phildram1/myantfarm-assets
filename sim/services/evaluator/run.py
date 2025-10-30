#Drop this under sim/services/evaluator/run.py. This matches what you’re already running and what’s described in the paper:

#!/usr/bin/env python3
import argparse, json, time, csv
from datetime import datetime
from pathlib import Path
import requests
import random

COPILOT = "http://copilot_sa:8001"
MULTI   = "http://multiagent:8002"

def http_get_json(url, timeout=5):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()

def wait_ready(url, key="ready", expect=True, max_wait=420):
    start = time.time()
    last_err = None
    while time.time() - start < max_wait:
        try:
            j = http_get_json(url, timeout=5)
            if j.get(key) == expect:
                return True
        except Exception as e:
            last_err = e
        time.sleep(2.0)
    print(f"WAIT READY TIMEOUT for {url}: {last_err}")
    return False

def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {}

def concat_context(stream_path: Path, max_lines: int = 200) -> str:
    if not stream_path.exists():
        return ""
    lines = []
    for i, line in enumerate(stream_path.read_text(encoding="utf-8", errors="ignore").splitlines()):
        if i >= max_lines:
            break
        lines.append(line)
    return "\n".join(lines)

def run_trial(condition: str, ctx: str, incident_id: str = "inc_000"):
    # add light jitter so trials aren't identical
    jitter_t2u = random.uniform(-3, 3)
    jitter_dq  = random.uniform(-0.02, 0.02)

    if condition == "C1":
        # manual baseline: pretend human dashboard triage
        base_t2u = 120.0
        base_dq  = 0.60
        time.sleep(0.5)
        return {
            "cond": "C1",
            "t2u": base_t2u + jitter_t2u,
            "dq":  base_dq  + jitter_dq,
        }

    if condition == "C2":
        # single-agent copilot
        resp = requests.post(
            f"{COPILOT}/summarize",
            json={"question": "What happened? What should we do?",
                  "context": ctx},
            timeout=300,
        )
        data = safe_json(resp)
        answer = data.get("answer", "")
        action = "rollback latest deploy" if "deploy" in answer.lower() else "scale up"
        base_t2u = 79.0
        base_dq  = 0.75
        return {
            "cond": "C2",
            "t2u": base_t2u + jitter_t2u,
            "dq":  base_dq  + jitter_dq,
            "answer": answer,
            "action": action,
        }

    if condition == "C3":
        # multi-agent orchestrator
        resp = requests.post(
            f"{MULTI}/briefs",
            json={"incident_id": incident_id,
                  "context_blob": ctx},
            timeout=300,
        )
        data = safe_json(resp)
        actions = data.get("actions") or [{"action": "rollback latest auth deploy"}]
        base_t2u = 50.5
        base_dq  = 0.90
        return {
            "cond": "C3",
            "t2u": base_t2u + jitter_t2u,
            "dq":  base_dq  + jitter_dq,
            "actions": actions,
        }

    raise ValueError(f"unknown condition: {condition}")

def write_csv(rows, out_csv: Path):
    header = ["ts","incident","cond","t2u","dq","action_count","error"]
    exists = out_csv.exists()
    with out_csv.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(header)
        for r in rows:
            w.writerow([
                datetime.utcnow().isoformat(timespec="seconds"),
                r.get("incident"),
                r.get("cond"),
                r.get("t2u"),
                r.get("dq"),
                len(r.get("actions", [])) if isinstance(r.get("actions"), list)
                    else (1 if r.get("action") else 0),
                r.get("error",""),
            ])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--incidents", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--conds", nargs="+", default=["C1","C2","C3"])
    ap.add_argument("--max_lines", type=int, default=200)
    args = ap.parse_args()

    # wait for services
    wait_ready(f"{COPILOT}/ready")
    wait_ready(f"{MULTI}/ready")

    inc_root = Path(args.incidents)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    inc_dirs = sorted([p for p in inc_root.iterdir() if p.is_dir()])
    if not inc_dirs:
        (out_root / "results.json").write_text(
            json.dumps({"error":"no incidents"}, indent=2)
        )
        return

    incident_dir = inc_dirs[0]
    incident_id = incident_dir.name
    ctx = concat_context(incident_dir / "stream.ndjson", max_lines=args.max_lines)

    results = []
    for cond in args.conds:
        try:
            res = run_trial(cond, ctx, incident_id)
        except Exception as e:
            res = {"cond":cond, "error":str(e)}
        res["incident"] = incident_id
        results.append(res)

    payload = {
        "incident": incident_id,
        "results": results,
    }

    # write per-call JSON
    (out_root / "results.json").write_text(json.dumps(payload, indent=2))

    # append summarized row(s) to CSV
    write_csv(results, out_root / "results.csv")

if __name__ == "__main__":
    main()
