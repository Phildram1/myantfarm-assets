# MyAntFarm.ai — Beyond Detection

**Goal:** Reduce the time between “something’s wrong” and “we know what to do.”

Modern ops teams get alerts in seconds, but it can take minutes (or longer) to answer the real questions:
- What actually broke?
- Who is impacted?
- What do we do next?

That delay is what we call **incident comprehension latency** — the time from first signal to a usable, explainable narrative a human can act on. Reducing that delay directly affects revenue, SLA penalties, and customer trust. :contentReference[oaicite:2]{index=2}
This repo provides a *reproducible simulation environment* to measure how fast different AI strategies reach “usable understanding,” and how good their recommendations are.

---

## What this repo contains

### 1. A containerized experiment stack
We use Docker Compose to spin up five cooperating services:

- **llm-backend**  
  Local inference API (Ollama) running a quantized Llama 3.x Instruct model (8B class). No external API calls are required.

- **copilot_sa** (C2 = single agent)  
  A FastAPI service that produces a one-shot incident summary + one recommended action.

- **multiagent** (C3 = multi-agent orchestration)  
  A FastAPI service that simulates multiple role-specialized “agents” (diagnostics, rollback planner, business risk comms, etc.) and merges them into a structured brief and action list. :contentReference[oaicite:3]{index=3}

- **evaluator**  
  A controller that feeds identical incident context into each condition (C1 = manual baseline, C2, C3), captures the time it took to reach a usable answer (**T₂U**) and scores action quality (**DQ**).

- **analyzer**  
  A Python 3.11 container that aggregates all trial runs into CSVs, summary text, and bar charts (matplotlib).

All services share a volume so results persist outside the containers (CSV, JSON, PNG). This makes the experiment deterministic and auditable. :contentReference[oaicite:4]{index=4}

---

## Metrics

We evaluate two core metrics across conditions:

- **Time to Usable Understanding (T₂U):**  
  How long (in seconds) it takes to get from “incident started” to an actionable narrative (“what happened / what to do next”). Lower is better.

- **Decision Quality (DQ):**  
  How specific, relevant, and correct the recommended actions are. Scored in \[0,1]. Higher is better.

We compare:
- **C1:** Manual baseline / dashboard-style reasoning (no AI assist)  
- **C2:** Single-agent copilot  
- **C3:** Multi-agent orchestrator

In our 348-trial simulation (116 trials per condition), **C3 cut comprehension latency by ~58% vs the manual baseline and ~36% vs the single-agent copilot, and improved decision quality by ~48% vs baseline.** :contentReference[oaicite:5]{index=5} :contentReference[oaicite:6]{index=6}

Those are the headline results we report in the paper.

---

## Reproducing the Study

### Prereqs
- Docker Desktop (with ~8GB RAM available)
- Python 3.11+ on your machine if you want to inspect outputs locally (optional)
- Windows WSL2 or Linux / macOS terminal is fine
- At least ~6–8 GB of disk for the quantized model pulled by Ollama

> Note: All data in this repo is **synthetic**. There is no production telemetry or customer data. :contentReference[oaicite:7]{index=7}

---

### 1. Clone the repo
```bash
git clone https://github.com/Phildram1/myantfarm-assets.git
cd myantfarm-assets/sim

### 2. Bring up the core services
```bash
docker compose up --build -d

This will:
build and start llm-backend (Ollama + quantized Llama 3.x),
build and start copilot_sa,
build and start multiagent,
prepare evaluator and analyzer images.

You can confirm the LLM endpoint is live by curling from your host:
```bash
curl http://localhost:11434/api/tags

### 3.Run a single evaluation pass
This runs one incident through all three conditions (C1, C2, C3), waits for each to respond, and writes results:
```bash
docker compose run --rm evaluator python run.py \
  --incidents /data \
  --out /results \
  --conds C1 C2 C3

After it finishes, you should see:

sim/results/results.json
sim/results/results.csv
The JSON includes raw per-condition output (like recommended rollback steps from C3), and the CSV is append-only and is what we later analyze.

### 4. Run multiple trials per condition
To approximate our paper’s numbers, we loop that evaluator call many times and let jitter/randomness accumulate. For example (PowerShell/bash style):
```bash
for i in {1..116}; do
  docker compose run --rm evaluator python run.py \
    --incidents /data \
    --out /results \
    --conds C1 C2 C3
done

Now results.csv will contain ~348 rows (3 rows per loop: one for each condition). That’s your dataset.

Why repeated trials?
Because LLMs are stochastic and we want to see if orchestration is robust, not just lucky once. In our tests, metrics stabilized after ~30–40 trials per condition and stayed consistent through 116.

###5. Generate summary metrics and plots
Once you’ve populated results.csv, run the analyzer container. This will:
read the CSV,
group by condition (C1/C2/C3),
compute mean and stddev for T₂U and DQ,
compute relative improvements,
emit bar charts (PNG),
emit a short narrative summary file for copy/paste into a slide or paper.

```bash
docker compose run --rm analyzer

Expected outputs (written under something like sim/analysis_out/):
metrics_table.txt
t2u_by_condition.png
dq_by_condition.png
paper_narrative.txt
paper_narrative.txt is basically PR/slide-ready text — it summarizes that C3 is ~58% faster than C1 and ~36% faster than C2, and that C3’s Decision Quality is highest.




