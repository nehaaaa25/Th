# Progress — CoFail-KG

## Current stage
S3 — BioHopR diagnostics (not started)

## Completed stages
S0
S1
S2 — BioHopR loader. 18/18 tests pass (incl. real-file test); audit found no science/gate problems.
  Question-text field selected: `hop2_question_multi` ("Name all …").
  Protocol §3.1 revision and question field filled in ([FROZEN] at S2); decision-log entry added.
  Post-S2 repo hygiene: requirements.lock (exact versions), requires-python >=3.12 (the lock needs
  it), README Reproduce/Contribute/Data credits. Fresh-clone check: 17 passed + 1 skipped before
  the BioHopR download, 18 passed after; S2 outputs regenerate identically.

## Latest commit
253af63 (README: Reproduce, Contribute and Data credits sections)

## Numbers to remember (filled as you go)
- BioHopR revision (S2): 08f06692c3900347e7405ba55ff6a6d330f55ddb (BioHopR.json SHA256 1adda2f23d305c394537e7b56d3e972b2d8f4141ae716ede54e0d08876eb527d)
- 2-hop row count (S2): 7,633 (matches paper). 1-hop and 2-hop questions share one record; every record is a 2-hop record. 12 relation-type counts match protocol §3.1 exactly.
- S2 diagnostics:
  - Question-field candidates: hop2_question_multi (selected; 7,633 distinct texts), hop2_question, prompt.
  - 135 rows: hop2 value ends in " (disease)" but question texts drop it (e.g. "acne (disease)" → "…disease acne ."). Relevant at S5/S12.
  - hop1 text inside hop2_question_multi: 61 case-sensitive substring · 126 case-insensitive substring · 81 case-insensitive whole word · 76 whole word with hop1 ≥ 4 chars (results/diagnostics/biohopr/hop1_in_question.csv).
  - Answer list length range 1–890.
- Answer size median / p90 / p99 (S3):
- Duplicate question texts with >1 bridge (S3):
- PrimeKG release, download date, row count (S4):
- Troglitazone side-effect count (S4 check, paper says 202):
- D1 outcome (S6):
- N_P and D2 outcome (S9):
- Max prompt tokens in screening (S20):
- Frozen models and digests (S21):
- Pilot commit hash (S26):

## Known issues
S2 engineering observations (none can change a result as things stand):
- Loader checks file SHA256 against metadata.json but not metadata revision against configs/frozen_hashes.yaml (natural check at S26).
- scripts/02_download_biohopr.py and inspection helpers have no unit tests (verified by real runs only).
- write_once (frozen_hashes.yaml) is not atomic; matters more as the file grows.
- BioHopR README.md has no Hub SHA256 to verify against (not LFS); its SHA256 is recorded in metadata.json.
- Loader default raw dir is relative to the working directory; scripts pass absolute paths.
- Venv editable install was repointed (pip install -e .) after the project moved from OneDrive.
## Fix at stage (deferred from the S1 audits)
- S13: how OUT_OF_MEMORY is detected (engineering; decided in code and documented).
- S29: final freeze of protocol §21 (mechanism list, control tie-break), using pilot results.
- Every stage: Claude Code lists its engineering choices at the end; record any that matter here.

## Next action
Start S3 in docs/pipeline_runbook.md
