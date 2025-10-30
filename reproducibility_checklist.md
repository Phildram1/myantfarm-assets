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



