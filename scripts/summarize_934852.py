"""Extract the public metric table from the original Job 934852 JSONL files."""

import csv
import hashlib
import json
import re
import sys
from pathlib import Path


source = Path(sys.argv[1])
files = sorted(source.glob("*k_c*_run*.jsonl"))
expected = {("4k", c, r) for c in (1, 8, 16, 32, 64, 128) for r in (1, 2, 3)}
expected |= {("64k", c, r) for c in (1, 8, 16, 32) for r in (1, 2, 3)}
rows = []

for path in files:
    match = re.fullmatch(r"(4k|64k)_c(\d+)_run([123])\.jsonl", path.name)
    if not match:
        continue
    scenario, concurrency, run = match.group(1), int(match.group(2)), int(match.group(3))
    raw = path.read_bytes()
    data = json.loads(raw)
    if not path.with_suffix(".ok").is_file() or data["completed"] <= 0:
        raise SystemExit(f"Incomplete run: {path.name}")
    rows.append({
        "scenario": scenario,
        "concurrency": concurrency,
        "run": run,
        "completed": data["completed"],
        "output_throughput": data["output_throughput"],
        "mean_ttft_ms": data["mean_ttft_ms"],
        "mean_tpot_ms": data["mean_tpot_ms"],
        "p99_e2e_latency_ms": data["p99_e2e_latency_ms"],
        "source_jsonl": path.name,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
    })

if {(r["scenario"], r["concurrency"], r["run"]) for r in rows} != expected:
    raise SystemExit("Expected exactly 30 formal runs across the ten 4K/64K levels")

writer = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys(), lineterminator="\n")
writer.writeheader()
writer.writerows(sorted(rows, key=lambda r: (r["scenario"], r["concurrency"], r["run"])))
