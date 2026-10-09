# CoFail-KG

CoFail-KG is a research project studying co-failure of independent local LLM agents answering multi-hop biomedical questions over a knowledge graph (PrimeKG, with questions from BioHopR). See `docs/` for the frozen protocol, decision rules, pipeline runbook, and progress log.

## Reproduce

### Python

- Tested on **Python 3.14.7** (Windows 11).
- Supported: **Python >= 3.12** (`requires-python` in `pyproject.toml`). The pinned dependencies in
  `requirements.lock` need 3.12 or newer, and networkx 3.7 does not install on Python 3.14.1
  specifically.

### Setup

From the repository root:

```bash
python -m venv venv
# Windows (PowerShell):  venv\Scripts\Activate.ps1
# Linux / macOS:         source venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install -e .
```

`requirements.lock` holds the exact versions the tests were run with. `requirements.txt` lists
the same packages without versions; use it only if you deliberately want newer versions.

### Run the tests

```bash
python -m pytest -q
```

- On a fresh clone, expect **17 passed, 1 skipped**. The skipped test checks the real BioHopR
  file and runs only once that file has been downloaded (next section).
- After downloading BioHopR, expect **18 passed**.

### Get the data

Downloaded data is not in git (`data/raw/` and `data/cache/` are gitignored).

**BioHopR** (needs internet access to the Hugging Face Hub):

```bash
python scripts/02_download_biohopr.py
```

This downloads `BioHopR.json` and the dataset card from `knowlab-research/BioHopR` at the pinned
revision `08f06692c3900347e7405ba55ff6a6d330f55ddb` into `data/raw/biohopr/`. It checks every file
against the Hub's SHA256, writes `data/raw/biohopr/metadata.json`, and refuses to overwrite files
that differ. The pinned revision is also recorded in `configs/frozen_hashes.yaml`.

**PrimeKG**: not used yet. Download instructions will be added with pipeline stage S4.

### Regenerate results

Stages are named S0, S1, … as in `docs/pipeline_runbook.md`; `docs/progress.md` shows which are
complete. Scripts are numbered by stage and run from the repository root.

| Stage | Command | Output |
|---|---|---|
| S2 | `python scripts/02_download_biohopr.py` | `data/raw/biohopr/` (not in git) |
| S2 | `python scripts/02_inspect_biohopr.py` | `results/diagnostics/biohopr/inspection_20.md`, `hop1_in_question.csv` |

The S2 inspection outputs are committed. After running the script, `git diff` should be empty.

## Contribute / extend

- **Code** lives in the `cofail_kg` package under `src/cofail_kg/` (`data/`, `kg/`, `agents/`,
  `evaluation/`, `analysis/`, `utils/`). Stage entry-point scripts go in `scripts/`, named with
  the stage number.
- **Configs** go in `configs/`. `configs/frozen_hashes.yaml` is written by code only, once per
  entry; never edit it by hand.
- **Tests**: every new module needs tests in `tests/`. Unit tests use tiny synthetic fixtures,
  not the full datasets.
- **Rules**: scientific rules come from `docs/frozen_pilot_protocol.md` and gates from
  `docs/decision_rules.md`; code cites protocol section numbers. `CLAUDE.md` lists the working
  rules for this repository (reproducibility, checkpointing, data handling).

## Data credits

- **BioHopR** — multi-hop biomedical question benchmark, Hugging Face dataset
  `knowlab-research/BioHopR`. Its dataset card declares the **MIT** license. This repository does
  not redistribute the dataset, but `results/diagnostics/biohopr/` quotes a sample of its rows.
- **PrimeKG** — the biomedical knowledge graph that BioHopR is built from and that the agents will
  query. Its source and license terms will be recorded when it is added (stage S4).
