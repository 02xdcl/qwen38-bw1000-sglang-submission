#!/usr/bin/env python3
"""Read-only snapshot of SGLang A1-A13 experiment evidence. Does not run benchmarks.
Only writes to a newly created --out directory, never modifies source files.
Do not confuse a current checkout snapshot with source that was loaded in historical runs.
"""
import argparse, csv, datetime, difflib, hashlib, json, os, pathlib, re, shutil, subprocess, sys
P=pathlib.Path
BASE=P('/public/home/zzu_dcf/qwen38_dcu_competition')
SG=P('/public/home/zzu_dcf/sglang')
DIRS=['experiments/A2_gdn_reorder','experiments/A3_gdn_tuning','experiments/A6_gemm_backend',
'experiments/A7_aiter_gemm','experiments/a8_gemm_opt','experiments/A9_schedule_ab',
'experiments/A10_schedule_tuning','experiments/A11_prefill_tuning','experiments/A12_max_prefill_tuning',
'experiments/A13_decode_tuning','experiments/sharegpt_retest','results/a3_sharegpt_ab_914874',
'results/sglang_bf16_sharegpt_893107','results/sharegpt_retest_20261016_011410',
'results/final_retest_20261016_232148','results/final_retest_20261017_002438',
'results/a4_profile_920552']
SUFFIXES={'.log','.jsonl','.json','.sh','.py','.md','.csv','.txt','.yaml','.yml','.diff','.patch'}
METRICS={
 'successful':'Successful requests',
 'duration_s':'Benchmark duration',
 'input_tokens':'Total input tokens',
 'output_tokens':'Total generated tokens',
 'output_tps':'Output token throughput',
 'total_tps':'Total token throughput',
 'p99_e2e_ms':'P99 E2E Latency',
 'mean_e2e_ms':'Mean E2E Latency',
 'mean_ttft_ms':'Mean TTFT',
 'mean_tpot_ms':'Mean TPOT'}

def sha256(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()

def record_cmd(label,argv,loc,timeout=25):
 try:
  r=subprocess.run(argv,capture_output=True,text=True,timeout=timeout,check=False)
  loc.append('===== '+label+' =====\n'+r.stdout[:30000]+r.stderr[:10000]+'\nEXIT: '+str(r.returncode)+'\n')
 except Exception as e:loc.append('===== '+label+' =====\nERROR: '+str(e)+'\n')

def metrics(p):
 try:text=p.read_text(errors='replace')
 except Exception:return {}
 d={}
 for key,label in METRICS.items():
  pat=re.compile(r'^\s*'+re.escape(label)+r'(?:\s*\([^\n:)]*\))?\s*:\s*([-+]?[0-9.]+)', re.I|re.M)
  m=pat.search(text)
  if m:d[key]=float(m.group(1))
 return d

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--root',default=str(BASE))
 ap.add_argument('--sglang',default=str(SG))
 ap.add_argument('--out',required=True,help='New, nonexisting directory for evidence; must not be project source path')
 ap.add_argument('--max-file-mib',type=int,default=48)
 a=ap.parse_args();root=P(a.root).resolve();sg=P(a.sglang).resolve();out=P(a.out).resolve()
 if out.exists():raise SystemExit('STOP: --out must not exist, to avoid modifying previously collected evidence')
 if out == root or out == sg:raise SystemExit('STOP: invalid output path')
 out.mkdir(parents=True)
 files=[];missing=[];skipped=[];copied=set()
 def copy_one(f):
  if not f.is_file() or f.is_symlink():return
  real=f.resolve()
  if real in copied:return
  copied.add(real)
  try:rel=real.relative_to(root);dest=out/'original_files'/rel
  except ValueError:
   try:rel=real.relative_to(sg);dest=out/'installed_sglang'/rel
   except ValueError:return
  try:
   size=real.stat().st_size
   if size>a.max_file_mib*1024*1024:
    skipped.append(f'{real}\t{size} bytes too large');return
   dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(real,dest)
   h=sha256(dest)
   files.append({'original_path':str(real),'copied_path':str(dest.relative_to(out)),
                 'bytes':size,'mtime':datetime.datetime.fromtimestamp(real.stat().st_mtime,datetime.timezone.utc).isoformat(),
                 'sha256':h})
  except Exception as e:skipped.append(str(real)+' '+str(e))
 for dname in DIRS:
  d=root/dname
  if not d.is_dir():missing.append(str(d));continue
  for f in sorted(d.rglob('*')):
   if len(f.relative_to(d).parts)>4:continue
   if f.suffix.lower() in SUFFIXES and f.is_file():copy_one(f)
 # Preserve the actual current import target and historical A2 backup as separate references.
 live=sg/'lib/python3.10/site-packages/sglang/srt/layers/attention/fla/fused_recurrent.py'
 orig=root/'experiments/A2_gdn_reorder/fused_recurrent_baseline.py'
 for f in [live,orig]:
  if f.is_file():copy_one(f)
  else:missing.append(str(f))
 (out/'file_manifest.json').write_text(json.dumps(files,indent=2,ensure_ascii=False)+'\n')
 (out/'sha256.txt').write_text(''.join(x['sha256']+'  '+x['copied_path']+'\n' for x in files))
 (out/'missing_paths.txt').write_text('\n'.join(missing)+'\n')
 (out/'skipped.txt').write_text('\n'.join(skipped)+'\n')
 runtime=[]
 runtime.append('CURRENT OBSERVATION: not proof of Oct 15-16 historical runtime.\n')
 runtime.append('UTC='+datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n')
 runtime.append('SLURM_JOB_ID='+os.environ.get('SLURM_JOB_ID','(not set)')+'\n')
 for name,argv in [('hostname',['hostname']),('rocm-smi',['rocm-smi','-i']),
                   ('SGLang/Torch/Triton',['/public/home/zzu_dcf/sglang/bin/python','-m','pip','show','sglang','torch','triton']),
                   ('hipcc',['hipcc','--version']),('project HEAD',['git','-C',str(root),'rev-parse','HEAD']),
                   ('sglang HEAD',['git','-C',str(sg),'rev-parse','HEAD']),
                   ('project status',['git','-C',str(root),'status','--short']),
                   ('sglang status',['git','-C',str(sg),'status','--short']),
                   ('slurm job 926667',['sacct','-j','926667','--format=JobID,JobName,NodeList,Start,End,Elapsed,State,AllocTRES'])]:
  record_cmd(name,argv,runtime)
 # No remote URLs or full environment dump: may contain access tokens.
 (out/'current_runtime_only.txt').write_text('\n'.join(runtime))
 if orig.exists() and live.exists():
  before=orig.read_text(errors='replace').splitlines(keepends=True)
  after=live.read_text(errors='replace').splitlines(keepends=True)
  diff=list(difflib.unified_diff(before,after,fromfile=str(orig)+' (historical backup candidate)',
                                 tofile=str(live)+' (CURRENT INSTALLED, NOT HISTORICAL PROOF)'))
  (out/'current_baseline_vs_live.diff').write_text(''.join(diff) if diff else 'IDENTICAL FILE CONTENT CURRENTLY\n')
 else:(out/'current_baseline_vs_live.diff').write_text('UNAVAILABLE: missing original or live code.\n')
 # Automatically derive raw-log metrics only; never substitute screenshot/history values.
 rows=[]
 for dname in DIRS:
  d=root/dname
  if not d.is_dir():continue
  for p in sorted(d.rglob('*.log')):
   if len(p.relative_to(d).parts)>4 or p.stat().st_size>30*1024*1024:continue
   m=metrics(p)
   if m:
    rows.append({'path':str(p),**m})
 with (out/'parsed_log_metrics.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['path',*METRICS]);writer.writeheader();writer.writerows(rows)
 checks=[]
 for c in (1,4,16,32,64):
  for typ,dname in [('historical_baseline','results/sglang_bf16_sharegpt_893107'),
                    ('sharegpt_retest','results/sharegpt_retest_20261016_011410')]:
   f=root/dname/f'c{c}_run1.log';r={'case':typ,'concurrency':c,'path':str(f)}
   if f.is_file():r.update(metrics(f));r['sha256']=sha256(f)
   else:r['status']='MISSING'
   checks.append(r)
 for steps in (1,2,4):
  f=root/f'experiments/A13_decode_tuning/bench_decode_{steps}.log';r={'case':'A13_decode','decode_steps':steps,'path':str(f)}
  if f.is_file():r.update(metrics(f));r['sha256']=sha256(f)
  else:r['status']='MISSING'
  checks.append(r)
 (out/'target_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
 print('Evidence snapshot created:',out)
 print('Original files copied:',len(files),' Missing paths:',len(missing),' Skipped:',len(skipped))
 print('IMPORTANT: no conclusion about historical deployed kernel or git commit without run-time provenance.')
if __name__=='__main__':main()
