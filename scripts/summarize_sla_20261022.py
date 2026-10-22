"""Verify the 2026-10-22 original runs and emit means by configured concurrency."""

import csv
import json
import re
import statistics
import sys
from pathlib import Path


source = Path(sys.argv[1])
sessions = {
    "sla_full_18583_20261022_030246": ("955149", "a01r3n16"),
    "sla_resume_64k_c32_20261022_131309": ("957082", "a01r4n15"),
}
expected = {("4k", c, r) for c in (1, 8, 16, 32, 64, 128) for r in (1, 2, 3)}
expected |= {("64k", c, r) for c in (1, 8, 16, 32) for r in (1, 2, 3)}
groups = {}
seen = set()
checks = {
    "Successful requests": "completed",
    "Output token throughput (tok/s)": "output_throughput",
    "Mean TTFT (ms)": "mean_ttft_ms",
    "Mean TPOT (ms)": "mean_tpot_ms",
    "P99 E2E Latency (ms)": "p99_e2e_latency_ms",
}
for session, (job, node) in sessions.items():
    folder = source / session
    provenance = (folder / "provenance.txt").read_text(encoding="utf-8")
    assert f"JOB={job}\n" in provenance and f"NODE={node}\n" in provenance
    for path in sorted(folder.glob("*_run*.jsonl")):
        match = re.fullmatch(r"(4k|64k)_c(\d+)_run([123])\.jsonl", path.name)
        assert match, path
        scenario, concurrency, run = match[1], int(match[2]), int(match[3])
        key = scenario, concurrency, run
        assert key in expected and key not in seen, key
        seen.add(key)
        assert (session.startswith("sla_resume")) == (scenario == "64k" and concurrency == 32)
        data = json.loads(path.read_bytes())
        log = path.with_suffix(".log").read_text(encoding="utf-8")
        assert path.with_suffix(".ok").read_text(encoding="utf-8").strip() == "PASS"
        assert data["max_concurrency"] == concurrency
        assert data["random_input_len"] == (4096 if scenario == "4k" else 65536)
        assert data["random_output_len"] == 1024 and data["random_range_ratio"] == 1.0
        assert data["backend"] == "sglang-oai-chat" and data["dataset_name"] == "random"
        prompts = max(8, concurrency * 2)
        assert re.search(rf"num_prompts={prompts}([,)])", log)
        assert data["completed"] == prompts
        assert data["total_output_tokens"] == prompts * 1024
        assert data["total_input_tokens"] == prompts * data["random_input_len"]
        for label, field in checks.items():
            found = re.findall(r"^" + re.escape(label) + r":\s+([\d.]+)", log, re.M)
            assert len(found) == 1 and abs(float(found[0]) - data[field]) <= 0.0051, (path, field)
        server = data["server_info"]
        for field, value in {"tp_size": 2, "dtype": "bfloat16", "port": 18583,
                             "chunked_prefill_size": 8192, "max_prefill_tokens": 16384,
                             "schedule_conservativeness": 0.4, "max_running_requests": 128,
                             "num_continuous_decode_steps": 1}.items():
            assert server[field] == value, (path, field)
        groups.setdefault((scenario, concurrency), []).append(data)

assert seen == expected and len(seen) == 30
rows = []
for (scenario, concurrency), runs in sorted(groups.items(), key=lambda item: (int(item[0][0][:-1]), item[0][1])):
    assert len(runs) == 3
    mean = lambda field: statistics.mean(run[field] for run in runs)
    rows.append({
        "scenario": scenario, "configured_concurrency": concurrency,
        "job_id": "957082" if scenario == "64k" and concurrency == 32 else "955149",
        "completed_runs": len(runs), "requests_per_run": runs[0]["completed"],
        "mean_observed_concurrency": mean("concurrency"),
        "mean_output_tok_s": mean("output_throughput"),
        "mean_output_tok_s_per_card": mean("output_throughput") / 2,
        "mean_ttft_ms": mean("mean_ttft_ms"), "mean_tpot_ms": mean("mean_tpot_ms"),
        "mean_run_p99_e2e_ms": mean("p99_e2e_latency_ms"),
    })
writer = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys(), lineterminator="\n")
writer.writeheader()
writer.writerows(rows)
