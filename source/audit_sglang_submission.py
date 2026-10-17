#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only SGLang competition evidence auditor.

Inventories files, calculates SHA256, creates unified diffs for available
Kernel files, extracts Benchmark metrics from raw logs, and searches for
schedule-conservativeness occurrences. Does not edit source files, launch or
stop services, or execute Benchmark tests.

Run on the HPC host:
  python audit_sglang_submission.py --root /public/home/zzu_dcf/qwen38_dcu_competition \
      --out /public/home/zzu_dcf/qwen38_dcu_competition/results/submission_audit_YYYYMMDD_HHMMSS

If the actual latest test-time Kernel is stored separately, pass it with
--latest-kernel /absolute/path/to/test-time/fused_recurrent.py.
"""
import argparse
import csv
import difflib
import hashlib
import json
import os
import re
import socket
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_ROOT = Path('/public/home/zzu_dcf/qwen38_dcu_competition')
DEFAULT_INSTALLED_KERNEL = Path(
    '/public/home/zzu_dcf/sglang/lib/python3.10/site-packages/'
    'sglang/srt/layers/attention/fla/fused_recurrent.py'
)
METRICS = {
    'successful_requests': r'Successful requests:\s*([\d,]+)',
    'benchmark_duration_s': r'Benchmark duration\s*\(s\):\s*([\d.]+)',
    'total_input_tokens': r'Total input tokens:\s*([\d,]+)',
    'total_generated_tokens': r'Total generated tokens:\s*([\d,]+)',
    'total_generated_tokens_retokenized': r'Total generated tokens\s*\(retokenized\):\s*([\d,]+)',
    'output_token_throughput_tok_s': r'Output token throughput\s*\(tok/s\):\s*([\d.]+)',
    'p99_e2e_latency_ms': r'P99 E2E Latency\s*\(ms\):\s*([\d.]+)',
    'mean_ttft_ms': r'Mean TTFT\s*\(ms\):\s*([\d.]+)',
    'mean_tpot_ms': r'Mean TPOT\s*\(ms\):\s*([\d.]+)',
    'max_request_concurrency': r'Max request concurrency:\s*([\d.]+)',
    'num_prompts': r'num_prompts\s*=\s*([\d,]+)',
}
TS_RE = re.compile(r'(20\d{2}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)')
SCHEDULE_RE = re.compile(r'--schedule-conservativeness|schedule_conservativeness', re.I)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def text(path):
    return path.read_text(encoding='utf-8', errors='replace')


def file_record(path, label):
    path = Path(path)
    rec = {'label': label, 'path': str(path), 'exists': path.is_file(),
           'size_bytes': '', 'mtime_local': '', 'sha256': ''}
    if path.is_file():
        st = path.stat()
        rec.update(size_bytes=st.st_size,
                   mtime_local=datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(),
                   sha256=sha256(path))
    return rec


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def list_logs(directory):
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.rglob('*')
                  if p.is_file() and p.suffix.lower() in {'.log', '.out'})


def list_jsonl(directory):
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.rglob('*.jsonl') if p.is_file())


def parse_log(path, group):
    body = text(path)
    stamps = TS_RE.findall(body)
    row = {'group': group, 'log_path': str(path), 'filename': path.name,
           'file_size_bytes': path.stat().st_size,
           'first_timestamp_in_log': stamps[0] if stamps else '',
           'last_timestamp_in_log': stamps[-1] if stamps else '',
           'timestamp_span_seconds': ''}
    if len(stamps) >= 2:
        try:
            a = datetime.fromisoformat(stamps[0].replace(' ', 'T'))
            b = datetime.fromisoformat(stamps[-1].replace(' ', 'T'))
            row['timestamp_span_seconds'] = round((b - a).total_seconds(), 3)
        except ValueError:
            pass
    for name, pattern in METRICS.items():
        found = re.findall(pattern, body, re.I)
        row[name] = found[-1].replace(',', '') if found else ''
    for name, pattern in {
        'dataset_name': r"dataset_name=['\"]([^'\"]+)['\"]",
        'dataset_path': r"dataset_path=['\"]([^'\"]+)['\"]",
        'model_path_or_name': r"(?:model|model_path)=['\"]([^'\"]+)['\"]",
        'served_model_name': r"served_model_name=['\"]([^'\"]+)['\"]",
        'output_file': r"output_file=['\"]([^'\"]+)['\"]",
        'schedule_conservativeness': r"(?:--schedule-conservativeness\s+|schedule_conservativeness[=:]\s*)([0-9.]+)",
    }.items():
        found = re.findall(pattern, body, re.I)
        row[name] = found[-1] if found else ''
    # Timestamp span is only the span visible in the log, not assumed to be
    # the formal benchmark start/end; duration is parsed separately.
    row['formal_start_time'] = ''
    row['formal_end_time'] = ''
    return row


def make_diff(src, dst, output):
    src, dst = Path(src), Path(dst)
    rec = {'from': str(src), 'to': str(dst), 'diff_path': str(output)}
    if not src.is_file() or not dst.is_file():
        missing = [str(p) for p in (src, dst) if not p.is_file()]
        output.write_text('DIFF NOT GENERATED: missing input file(s):\n' + '\n'.join(missing) + '\n', encoding='utf-8')
        rec.update(status='MISSING_INPUT', missing=missing)
        return rec
    diff = list(difflib.unified_diff(text(src).splitlines(True), text(dst).splitlines(True),
                                    fromfile=str(src), tofile=str(dst), n=4))
    output.write_text(''.join(diff) if diff else 'NO CONTENT DIFFERENCE\n', encoding='utf-8')
    changed = sum(1 for line in diff if (line.startswith('+') or line.startswith('-'))
                  and not line.startswith('+++') and not line.startswith('---'))
    rec.update(status='DIFF_GENERATED', has_content_difference=bool(diff),
               changed_lines_count=changed, sha256_from=sha256(src), sha256_to=sha256(dst))
    return rec


def search_lines(directories):
    patterns = {
        'schedule_conservativeness': r'--schedule-conservativeness|schedule_conservativeness',
        'num_warps': r'num_warps\s*=',
        'model_dtype_tp': r'--model-path|--model\b|--dtype|--tp-size|served_model_name',
        'num_prompts': r'--num-prompts|num_prompts\s*=',
    }
    matches = []
    for directory in directories:
        directory = Path(directory) if directory else None
        if not directory or not directory.exists():
            continue
        candidates = [directory] if directory.is_file() else directory.rglob('*')
        for path in candidates:
            if not path.is_file() or path.suffix.lower() not in {'.sh', '.log', '.out', '.txt', '.py', '.json'}:
                continue
            try:
                lines = text(path).splitlines()
            except OSError:
                continue
            for n, line in enumerate(lines, 1):
                for name, pat in patterns.items():
                    if re.search(pat, line, re.I):
                        matches.append({'file': str(path), 'line': n, 'match_type': name,
                                        'text': line.strip()[:1000]})
    return matches


def main():
    ap = argparse.ArgumentParser(description='Read-only SGLang submission audit')
    ap.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    ap.add_argument('--out', type=Path, default=None)
    ap.add_argument('--installed-kernel', type=Path, default=DEFAULT_INSTALLED_KERNEL)
    ap.add_argument('--original-kernel', type=Path, default=None)
    ap.add_argument('--a3-original-kernel', type=Path, default=None)
    ap.add_argument('--a3-warp2-kernel', type=Path, default=None)
    ap.add_argument('--latest-kernel', type=Path, default=None,
                    help='Exact test-time Kernel snapshot if available; do not substitute a current file unless proven identical.')
    ap.add_argument('--latest-launch', type=Path, default=None)
    ap.add_argument('--original-launch', type=Path, default=None,
                    help='Pass only when the actual original launch script path is known.')
    ap.add_argument('--baseline-dir', type=Path, default=None)
    ap.add_argument('--retest-dir', type=Path, default=None)
    ap.add_argument('--a3-results-dir', type=Path, default=None)
    args = ap.parse_args()

    root = args.root
    out = args.out or root / 'results' / ('submission_audit_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True, exist_ok=True)
    original = args.original_kernel or root / 'experiments/A2_gdn_reorder/fused_recurrent_baseline.py'
    a3_dir = root / 'experiments/A3_gdn_tuning'
    a3_original = args.a3_original_kernel or a3_dir / 'fused_recurrent_original.py'
    a3_warp2 = args.a3_warp2_kernel or a3_dir / 'fused_recurrent_bv32_w2.py'
    baseline = args.baseline_dir or root / 'results/sglang_bf16_sharegpt_893107'
    retest = args.retest_dir or root / 'results/sharegpt_retest_20261016_011410'
    a3_results = args.a3_results_dir or root / 'results/a3_sharegpt_ab_914874'
    latest_launch = args.latest_launch or root / 'experiments/sharegpt_retest/run.sh'
    latest_kernel = args.latest_kernel or args.installed_kernel

    warnings = []
    if args.latest_kernel is None:
        warnings.append('LATEST_KERNEL_NOT_PROVEN: installed Kernel is only a current candidate, not proven to be the test-time snapshot.')
    if args.original_launch is None:
        warnings.append('ORIGINAL_LAUNCH_NOT_SPECIFIED: no confirmed original ShareGPT launch script was supplied.')

    kernels = [
        file_record(original, 'A2 original backup candidate'),
        file_record(args.installed_kernel, 'current installed Kernel'),
        file_record(a3_original, 'A3 Warp1 source candidate'),
        file_record(a3_warp2, 'A3 Warp2 source candidate'),
        file_record(latest_kernel, 'latest test-time Kernel candidate unless exact snapshot explicitly supplied'),
    ]
    write_csv(out / 'file_hashes.csv', kernels,
              ['label', 'path', 'exists', 'size_bytes', 'mtime_local', 'sha256'])

    diffs = [make_diff(original, args.installed_kernel, out / 'installed_vs_a2_backup.diff'),
             make_diff(a3_original, a3_warp2, out / 'a3_warp1_vs_warp2.diff')]
    if Path(latest_kernel).resolve() != Path(args.installed_kernel).resolve():
        diffs.append(make_diff(original, latest_kernel, out / 'latest_candidate_vs_a2_backup.diff'))
    else:
        diffs.append({'from': str(original), 'to': str(latest_kernel), 'status': 'NOT_SEPARATE_SNAPSHOT',
                      'note': 'No independent test-time snapshot was supplied.'})

    groups = [('baseline', baseline), ('latest_retest', retest), ('A3_AB', a3_results)]
    metrics, log_inventory, jsonl_inventory = [], [], []
    for group, directory in groups:
        logs = list_logs(directory)
        if not logs:
            warnings.append(f'NO_LOG_FILES_FOUND: {group} directory missing or contains no .log/.out files: {directory}')
        for log in logs:
            metrics.append(parse_log(log, group))
            log_inventory.append(file_record(log, group))
        for data in list_jsonl(directory):
            rec = file_record(data, group)
            try:
                with data.open('r', encoding='utf-8', errors='replace') as f:
                    rec['line_count'] = sum(1 for line in f if line.strip())
            except OSError as exc:
                rec['line_count'] = ''
                rec['read_error'] = str(exc)
            jsonl_inventory.append(rec)

    metric_fields = ['group', 'log_path', 'filename', 'file_size_bytes', 'first_timestamp_in_log',
        'last_timestamp_in_log', 'timestamp_span_seconds', 'successful_requests', 'benchmark_duration_s',
        'total_input_tokens', 'total_generated_tokens', 'total_generated_tokens_retokenized',
        'output_token_throughput_tok_s', 'p99_e2e_latency_ms', 'mean_ttft_ms', 'mean_tpot_ms',
        'max_request_concurrency', 'num_prompts', 'dataset_name', 'dataset_path', 'model_path_or_name',
        'served_model_name', 'output_file', 'schedule_conservativeness', 'formal_start_time', 'formal_end_time']
    write_csv(out / 'metrics.csv', metrics, metric_fields)
    inv_fields = ['label', 'path', 'exists', 'size_bytes', 'mtime_local', 'sha256']
    write_csv(out / 'log_inventory.csv', log_inventory, inv_fields)
    write_csv(out / 'jsonl_inventory.csv', jsonl_inventory, inv_fields + ['line_count', 'read_error'])

    search_dirs = [root / 'experiments', baseline, retest, a3_results, a3_dir, latest_launch, args.original_launch]
    matches = search_lines(search_dirs)
    (out / 'parameter_matches.json').write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding='utf-8')
    schedule = [f"{m['file']}:{m['line']}: {m['text']}" for m in matches if m['match_type'] == 'schedule_conservativeness']
    (out / 'schedule_parameter_matches.txt').write_text('\n'.join(schedule) + ('\n' if schedule else 'NO MATCH FOUND IN SEARCHED EXISTING FILES\n'), encoding='utf-8')

    launchers = []
    exp = root / 'experiments'
    if exp.is_dir():
        for p in sorted(exp.rglob('*.sh')):
            try:
                body = text(p)
            except OSError:
                continue
            if re.search(r'sharegpt|sglang|bench_serving|num-prompts', body, re.I):
                launchers.append({'path': str(p), 'sha256': sha256(p),
                                  'has_schedule_conservativeness': bool(SCHEDULE_RE.search(body)),
                                  'has_num_warps': bool(re.search(r'num_warps\s*=', body, re.I))})
    (out / 'launcher_candidates.json').write_text(json.dumps(launchers, ensure_ascii=False, indent=2), encoding='utf-8')

    env = {'captured_at_local': datetime.now().astimezone().isoformat(), 'hostname': socket.gethostname(),
           'python_executable': sys.executable, 'python_version': sys.version, 'cwd': os.getcwd(),
           'SLURM_JOB_ID': os.environ.get('SLURM_JOB_ID', ''),
           'SLURM_JOB_NODELIST': os.environ.get('SLURM_JOB_NODELIST', ''),
           'HIP_VISIBLE_DEVICES': os.environ.get('HIP_VISIBLE_DEVICES', ''),
           'ROCR_VISIBLE_DEVICES': os.environ.get('ROCR_VISIBLE_DEVICES', ''),
           'CUDA_VISIBLE_DEVICES': os.environ.get('CUDA_VISIBLE_DEVICES', ''),
           'SGLANG_USE_AITER_LINEAR_ATTN': os.environ.get('SGLANG_USE_AITER_LINEAR_ATTN', ''),
           'note': 'Current execution environment only; not proof of historical benchmark environment.'}
    (out / 'current_environment.json').write_text(json.dumps(env, ensure_ascii=False, indent=2), encoding='utf-8')

    summary = {'audit_time_local': datetime.now().astimezone().isoformat(), 'root': str(root), 'output_dir': str(out),
               'kernel_files': kernels, 'diffs': diffs, 'log_files_found': len(metrics),
               'jsonl_files_found': len(jsonl_inventory),
               'schedule_parameter_matches': len(schedule), 'launcher_candidates_found': len(launchers),
               'warnings': warnings,
               'limits': ['Current file hash does not prove test-time file hash.',
                          'File modification time does not prove when a running process loaded the file.',
                          'Visible log timestamp span is not assumed to equal formal Benchmark duration.',
                          'Missing metrics are not imputed from charts or another experiment.']}
    (out / 'audit.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'warnings.txt').write_text('\n'.join(warnings) + ('\n' if warnings else 'No warnings recorded.\n'), encoding='utf-8')

    print('SGLang audit finished (read-only).')
    print('Output directory:', out)
    print('Kernel hashes:', out / 'file_hashes.csv')
    print('Metrics:', out / 'metrics.csv')
    print('Log inventory:', out / 'log_inventory.csv')
    print('JSONL inventory:', out / 'jsonl_inventory.csv')
    print('Diffs:', out / 'installed_vs_a2_backup.diff', out / 'a3_warp1_vs_warp2.diff')
    print('Warnings:', out / 'warnings.txt')
    print('Read warnings.txt carefully: missing files are not evidence of no differences.')

if __name__ == '__main__':
    main()
