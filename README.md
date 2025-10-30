## About the Project

**MyAntFarm.ai** is an experimental framework for evaluating large language model (LLM) multi-agent orchestration in real-time incident comprehension. It replicates results published in:

> Philip Drammeh (2025). *Beyond Detection: Evaluating LLM-Based Multi-Agent Systems for Real-Time Incident Comprehension.*  
> [Executive Summary (PDF)](docs/EXECUTIVE_SUMMARY.pdf) | [Full Paper (PDF)](paper/Beyond_Detection.pdf)

# MyAntFarm.ai — Beyond Detection

**Goal:** Reduce the time between “something’s wrong” and “we know what to do.”

Modern ops teams get alerts in seconds, but it can take minutes (or longer) to answer the real questions:
- What actually broke?
- Who is impacted?
- What do we do next?

That delay is what we call **incident comprehension latency** — the time from first signal to a usable, explainable narrative a human can act on. Reducing that delay directly affects revenue, SLA penalties, and customer trust.
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

All services share a volume so results persist outside the containers (CSV, JSON, PNG). This makes the experiment deterministic and auditable.

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

In our 348-trial simulation (116 trials per condition), **C3 cut comprehension latency by ~58% vs the manual baseline and ~36% vs the single-agent copilot, and improved decision quality by ~48% vs baseline.**

Those are the headline results we report in the paper.

---

## Reproducing the Study

### Prereqs
- Docker Desktop (with ~8GB RAM available)
- Python 3.11+ on your machine if you want to inspect outputs locally (optional)
- Windows WSL2 or Linux / macOS terminal is fine
- At least ~6–8 GB of disk for the quantized model pulled by Ollama

> Note: All data in this repo is **synthetic**. There is no production telemetry or customer data.


