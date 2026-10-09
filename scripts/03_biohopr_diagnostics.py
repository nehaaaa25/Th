"""S3: BioHopR 2-hop dataset diagnostics (runbook S3; protocol §0.4, §3.1). No PrimeKG.

Outputs (from the repository root), in results/diagnostics/biohopr/:
answer_sizes.csv, answer_sizes.png, relation_types.csv, largest_answers.csv,
duplicate_questions.csv, repeated_answers.csv, summary.json.
See src/cofail_kg/data/diagnostics.py for definitions.

Usage: python scripts/03_biohopr_diagnostics.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cofail_kg.data.biohopr_loader import load_biohopr, read_metadata
from cofail_kg.data.diagnostics import write_all

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/biohopr"
OUT_DIR = ROOT / "results/diagnostics/biohopr"


def main() -> int:
    rows = load_biohopr(RAW_DIR)
    revision = read_metadata(RAW_DIR).get("revision")
    summary = write_all(rows, OUT_DIR, revision)
    print(f"Wrote S3 diagnostics to {OUT_DIR}")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
