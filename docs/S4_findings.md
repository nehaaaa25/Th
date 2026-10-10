# S4 findings — PrimeKG release verification and BioHopR answer construction

Recorded 2026-10-11. Two inspection reports, saved verbatim. No protocol change.
Report 2 corrects report 1's statement that the answer list is always the union over all bridges.

---

## Report 1 — Troglitazone mismatch and release

This is a counting difference, not a release mismatch. Your `kg.csv` is the right file: Troglitazone really has 17 side effects in it, and the paper's "202" is the size of a 2-hop answer list. I changed nothing; everything below comes from read-only queries plus public Dataverse and arXiv lookups.

### 1. Nodes matching "Troglitazone"

There is exactly one, and no other node of any type contains "troglitazon":

| index | id | type |
|---|---|---|
| 14813 | DB00197 | drug |

### 2. Labels touching it

Every row is stored in both directions, so Troglitazone-as-x and Troglitazone-as-y give identical counts (1,178 rows each):

| relation / display label | neighbour type | unique neighbours |
|---|---|---|
| drug_protein / enzyme | gene/protein | 19 |
| drug_protein / target | gene/protein | 9 |
| drug_protein / transporter | gene/protein | 2 |
| drug_drug / synergistic interaction | drug | 1,129 |
| indication / indication | disease | 2 |
| drug_effect / side effect | effect/phenotype | 17 |

Across all labels and both directions, Troglitazone has 17 unique effect/phenotype neighbours. They all come from `drug_effect`.

### 3. Release

- **Version history on Dataverse:** PrimeKG has three versions: 1.0 (2022-04-25), 2.0 (2022-04-28) and 2.1 (2022-05-02).
- **`kg.csv` matches:** all three versions point to the same `kg.csv` (file 6180620). Your local copy matches it exactly on size (981,751,236 bytes) and MD5 (`aac8191d4fbc5bf09cdf8c3c78b4e75f`). Dataverse publishes only MD5, not SHA256. So your file is the only `kg.csv` that has ever been published there, and the version choice can't matter for it.
- **`nodes.tab`:** it's also the same file in all three versions (6180617). Your copy matches its size, but the MD5 differs (`4924de04…` local vs `7f9ab410…` on Dataverse), as I reported last time.
- **What BioHopR says:** the [paper](https://arxiv.org/html/2505.22240v2) gives no PrimeKG version, download source or file name, and links no code repository, only the dataset on Hugging Face. The dataset README also says only "Built from the comprehensive PrimeKG". Its sentence on Troglitazone is: *"Diabetes-related questions for drug Troglitazone, which has 202 side effects listed from PrimeKG…"*

### 4. Cross-check with BioHopR

Troglitazone appears in 9 BioHopR rows:
- **As hop1 (bridge) in one row:** row 4518, hop2 = type 2 diabetes mellitus, `drug:effect/phenotype` / `disease:drug:effect/phenotype`, with **202 answers**.
- **As an answer in 8 rows:** all `disease:gene/protein:drug` rows, with bridges UGT1A1 (5 rows), CYP19A1, SERPINE1 and PPARG.

Checking row 4518's 202 answers against your `kg.csv`:
- **All 202 are effect/phenotype node names** (exact match).
- **Only 17 are Troglitazone's own side effects,** and those 17 are exactly its full side-effect set in your file.
- **All 202 are reproduced exactly** by taking type 2 diabetes mellitus, following its `indication` edges to 49 drugs, and collecting the `drug_effect` neighbours of all 49.
- **Other edges don't fit:** using `contraindication` instead covers only 122 of the 202, and any label gives 269.

So the paper's "202 side effects" is the 2-hop answer set for "effects of a drug indicated for type 2 diabetes", reached through all 49 drugs. Troglitazone is just the sample bridge stored in that row.

### 5. Three other drugs with large answer lists

These are the drug-as-hop1 rows with the most answers:

| row | hop1 drug | hop2 | BioHopR answers | hop1's effect neighbours in `kg.csv` | answers that are hop1 neighbours | answers reproduced from `kg.csv` |
|---|---|---|---|---|---|---|
| 3947 | Selegiline | endogenous depression | 457 | 199 | 199 | all, via indication → side effect |
| 4167 | Hydrocortisone | lymphosarcoma | 453 | 89 | 89 | all, via indication → side effect |
| 4087 | Fosinopril | hypertensive disorder | 442 | 116 | 116 | all, via indication → side effect |
| 4518 | Troglitazone | type 2 diabetes mellitus | 202 | 17 | 17 | all, via indication → side effect |

Same pattern every time: each drug's own side effects are a subset of the answers, and the full answer list is the 2-hop union.

**Across all 7,633 rows:**
- **7,370 rows** have answer lists reproduced exactly by one pair of first-hop and second-hop labels, taken across all bridges. All 949 `drug:effect/phenotype` rows fit `indication → side effect`.
- **157 rows** are reproduced by no label pair:
  - 63 drug:disease / effect/phenotype:drug:disease
  - 57 drug:disease / gene/protein:drug:disease
  - 32 effect/phenotype:drug
  - 5 effect/phenotype:disease
- **6,840 rows** also equal hop1's own neighbours. That is often just because the two sets coincide.

I matched names exactly, falling back to stripped whitespace for the hop1/hop2 names. I only used labels between the four BioHopR types, and both directions, since every edge is stored both ways.

### Conclusion

**Release:** your `kg.csv` is byte-identical to the only `kg.csv` Dataverse has published (shared by v1.0, v2.0 and v2.1). Almost every BioHopR answer list can be rebuilt from it exactly, so it is consistent with the graph BioHopR was built from.

**Counting difference:** the 202 counts the 2-hop answer set (side effects of all 49 diabetes drugs), not Troglitazone's own side effects (17).

**Recommendations:**
1. **Choose this release** (Dataverse DOI 10.7910/DVN/IXA7BM, `kg.csv` file 6180620, v2.1). Record the evidence in the decision log: the MD5 match and the 7,370 of 7,633 exact reproductions, plus the explanation of the 202.
2. **Replace the release check.** "About 202 on the side-effect label" in runbook S4 and the "(Troglitazone check)" in protocol §3.2 test the wrong number: they would fail on the correct file. Rewording them needs your instruction, because I don't edit the protocol.
3. **Bring forward to S5:**
   - BioHopR's `answer` field holds the 2-hop answer set (combined over all bridges). It is not hop1's 1-hop set, and the dataset has no separate 1-hop answer list.
   - The 157 rows that no label pair reproduces need explaining.
   - Which label pairs BioHopR used (e.g. `indication` only, not `contraindication`) matters for the relation mapping at S6.
4. **Decide about `nodes.tab`.** Either hash it as a raw input with the checksum question noted, or rely only on `kg.csv`, which contains every node.

Sources:
- [BioHopR paper (arXiv 2505.22240v2)](https://arxiv.org/html/2505.22240v2)
- [BioHopR PDF](https://arxiv.org/pdf/2505.22240)
- PrimeKG Dataverse API, `doi:10.7910/DVN/IXA7BM` (version and file metadata)

---

## Report 2 — Answer construction (options A/B/C) and nodes.tab

I need to correct last turn's finding first. Answers are the union over all bridges in only one relation type, `disease:drug:effect/phenotype`. Two other types mostly use the stored bridge's own targets, and nine types only ever have one bridge. Nothing was modified.

**How I ran the simulation:**
- **Label pairs:** I used one label pair per relation type: the pair that matched most rows in my last check. These are not the S6 mapping.
- **Name matching:** the §12 reference policy, plus trimming leading and trailing spaces. Whether §12 trims is still the open S5 decision.
- **Targets:** `s` is excluded from targets, as §6 requires.
- **Queries:** no query has more than one row, so every query has exactly one gold bridge.

### 1. Impact of how BioHopR builds its answer lists

#### What the answer list equals, per row

| relation type (S:B:T) | rows | queries with ≥2 valid bridges | answers = stored bridge's targets = union | answers = stored bridge's targets only | answers = union only | neither | name not resolved |
|---|---|---|---|---|---|---|---|
| drug:gene/protein:disease | 3029 | 0 | 3029 | 0 | 0 | 0 | 0 |
| disease:gene/protein:drug | 899 | 0 | 899 | 0 | 0 | 0 | 0 |
| gene/protein:disease:drug | 577 | 0 | 577 | 0 | 0 | 0 | 0 |
| drug:disease:gene/protein | 321 | 0 | 321 | 0 | 0 | 0 | 0 |
| drug:disease:effect/phenotype | 213 | 0 | 213 | 0 | 0 | 0 | 0 |
| disease:drug:gene/protein | 381 | 0 | 381 | 0 | 0 | 0 | 0 |
| gene/protein:drug:disease | 462 | 0 | 405 | 0 | 0 | 1 | 56 |
| **disease:drug:effect/phenotype** | 949 | 619 | 338 | 0 | **611** | 0 | 0 |
| **effect/phenotype:disease:drug** | 546 | 85 | 474 | **60** | 12 | 0 | 0 |
| **effect/phenotype:drug:disease** | 215 | 63 | 93 | **46** | 13 | 4 | 59 |
| disease:effect/phenotype:drug | 36 | 0 | 4 | 0 | 0 | 32 | 0 |
| drug:effect/phenotype:disease | 5 | 0 | 0 | 0 | 0 | 5 | 0 |
| **Total** | 7633 | 767 | 6734 | 106 | 636 | 42 | 115 |

- **Nine types always have exactly one bridge.** In those types every query entity has exactly one neighbour under the hop-1 label. BioHopR appears to have picked them that way, so for these types the two constructions give the same answer list.
- **Only one type uses the union.** That is `disease:drug:effect/phenotype` (611 rows; Troglitazone is one of them).
- **The two `effect/phenotype` start types are mixed.** Where the two constructions differ, they mostly follow the stored bridge only.
- **Unresolved names:** all 115 are answer names that match no node of the target type.

#### §5.1 hop-2 score, as written (30-row validation sample, every candidate label set)

| type | hop-2 score as written | if scored against the union | D1 needs 90% |
|---|---|---|---|
| disease:drug:effect/phenotype | 0.50 | 1.00 | fails as written; passes under union |
| effect/phenotype:disease:drug | 0.93 | 0.87 | passes as written; fails under union |
| effect/phenotype:drug:disease | 0.73 | 0.53 | fails both ways |
| gene/protein:drug:disease | 0.80 | 0.80 | fails both ways (unresolved answer names, not bridges) |
| disease:effect/phenotype:drug | 0.10 | 0.10 | fails |
| drug:effect/phenotype:disease | 0.00 | 0.00 | fails |
| the other 6 types | 1.00 | 1.00 | pass |

- **Selection isn't affected:** the winning label set is the same either way. Only the score changes.
- **As written:** the 7 passing types cover 78.2% of rows, so there's no global STOP.
- **Scored against the union:** the 7 passing types cover 83.4%.

#### §7.1 condition 5 (A\*_q = T_q^{B\*}), as written

**About 6,840 queries are CONSISTENT** (before checking for leaky questions, saturation and the gates).

**Failures:**
- 636 queries fail because their answers equal the union over all bridges (`GOLD_MISSING_FROM_KG`). 611 of these are `disease:drug:effect/phenotype`, which is 64% of that type.
- 42 fail for other reasons.
- 115 fail conditions 1–4.

**Multi-bridge shortfall:** only **128 CONSISTENT queries have two or more valid bridges** (8, 47 and 73 from the three types above). §8 needs 15 + 3 + 75 + 300 = 393 multi-bridge queries. The §8 shortfall rule fills the gap with single-bridge queries.

**If the wording were A\*_q = T_q instead:**
- 7,370 queries would satisfy it.
- The multi-bridge pool would be 658, of which 619 come from one relation type.

#### §13 Label A, as written

**Where ALT_VALID can occur:**
- In every single-bridge query, T_q = T_q^{B\*} = A\*_q, so `ALT_VALID` is impossible and Label A reduces to `GOLD` or `OFF_QUESTION`.
- Among CONSISTENT queries, `ALT_VALID` targets exist only in the two `effect/phenotype` start types, with up to 119 and 103 targets per query.

**In `disease:drug:effect/phenotype`:** its multi-bridge queries are INCONSISTENT and never sampled, so it contributes no `ALT_VALID`.

**Under union wording:** `ALT_VALID` would be empty for every primary query. The benchmark P/R/F1 in §15 would then equal the question-valid metrics.

#### Protocol sections that conflict with this finding

- **§6 Source note** ("Departure from BioHopR's single-bridge answers"): its premise is false for one type.
- **§5.1 hop-2 score**, combined with the D1 90% threshold.
- **§7.1 condition 5** and the `GOLD_MISSING_FROM_KG` code.
- **§13 Label A:** the GOLD vs ALT_VALID distinction assumes answers are per-bridge.
- **§3.1 field-role rule (S5):** in a 5-row sample of `disease:drug:effect/phenotype`, about 64% of rows have answers that are not neighbours of hop1. The type will likely miss the 95% bar, so S5 would stop.
- **§8 single/multi quotas (75% multi-bridge) and D2:** both assume a multi-bridge pool that doesn't exist under the current wording.
- **§3.2 / runbook S4 Troglitazone check:** it tests the wrong number, as reported last time.

#### Possible wording changes (not choosing)

**A. Keep per-bridge gold as written.**
- `disease:drug:effect/phenotype` fails D1, or 64% of it is INCONSISTENT.
- The multi-bridge pool is about 73 queries, mostly from one type, so most quota shortfall moves to single-bridge queries.
- `ALT_VALID` stays meaningful only where multi-bridge queries remain.
- No protocol edit is needed, but the pilot would test multi-bridge co-failure on very few queries.

**B. Compare against the union over all valid bridges.** Condition 5 becomes A\*_q = T_q, and the hop-2 score compares to the union.
- `disease:drug:effect/phenotype` passes, but `effect/phenotype:disease:drug` drops to 0.87 and fails D1.
- The multi-bridge pool is 619, almost entirely one type.
- `ALT_VALID` disappears and Label A collapses to two values.
- The §15 benchmark metrics become redundant.

**C. Decide the construction per relation type at S6.** Score both constructions and accept one that reaches 90%; condition 5 then uses T_q^{B\*} or T_q accordingly.
- More types pass, and the multi-bridge pool is about 700 across three types.
- It adds a free choice made from gold data only, which §5.1 already allows for label sets.
- `GOLD` means different things in different types, so results must be reported split by construction.
- Rows that follow neither construction (42) still fail.

### 2. `nodes.tab` vs `kg.csv`

- **Same nodes:** `nodes.tab` has no node that is missing from `kg.csv`. All 129,375 indices appear in edges, so there are no isolated nodes.
- **Same per-type counts:** the counts are identical (from the merge in my first inspection; full table there): anatomy 14,035 · biological_process 28,642 · cellular_component 4,176 · disease 17,080 · drug 7,957 · effect/phenotype 15,311 · exposure 818 · gene/protein 27,671 · molecular_function 11,169 · pathway 2,516.
- **Same fields:** ID, type and source agree for every node. Names agree except index 98266, which is a quoting difference (`\"` vs `""`).
- **Effect on the protocol:** using `kg.csv` alone changes neither the §7.1 saturation denominator nor the §15 degree percentile. Degree comes from edges either way, and the per-type node counts are the same. The only effect would be on name resolution for node 98266, and only if `nodes.tab` were parsed without the backslash escape.

**Caveats:**
- The label pairs in 1a and 1c are mine; only 1b ran the §5.1 selection.
- The 115 unresolved answer names need S5 investigation.
- Every number above depends on the S5 decision about trimming spaces in names.
