"""Extract score-only evidence from the archived GSM8K HTML report."""

import csv
import hashlib
import re
import sys
from pathlib import Path


raw = Path(sys.argv[1]).read_bytes()
scores = re.findall(rb"<p>Score: ([01]\.0)</p>", raw)
if len(scores) != 1314:
    raise SystemExit(f"Expected 1314 scored examples, found {len(scores)}")

writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(("example", "score", "source_html_sha256"))
source_hash = hashlib.sha256(raw).hexdigest()
for number, score in enumerate(scores, 1):
    writer.writerow((number, score.decode("ascii"), source_hash))
