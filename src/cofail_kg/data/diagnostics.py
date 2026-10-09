"""BioHopR 2-hop dataset diagnostics (runbook S3; protocol §0.4, §3.1).

Descriptive only: no threshold is chosen here and PrimeKG is not used. Input is the list of row
dicts returned by `cofail_kg.data.biohopr_loader.load_biohopr`.

Fields used:
- `hop2_question_multi` — the 2-hop question text given to agents (protocol §3.1, [FROZEN] at S2).
- `relation_hop2` — the relation type (protocol §0.4); `hop2_type`, `hop1_type`, `target_type` are
  the dataset's other type fields, reported alongside.
- `hop1` — called "bridge" in the S3 prompt. Field roles are [TBD@S5] (protocol §3.1); this module
  does not interpret them.
- `answer` — the answer list. Answer lists are compared as sets of exact strings (protocol §0.4:
  order and repeated names ignored).

Engineering choices (not protocol): percentiles use `numpy.percentile` with its default
("linear") method; answer size is reported both as raw list length and as set size; question texts
are grouped by exact string equality; ties are broken by `row_id` or question text ascending.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np

QUESTION_FIELD = "hop2_question_multi"
RELATION_FIELD = "relation_hop2"
TYPE_FIELDS = ("hop2_type", "hop1_type", "target_type")
BRIDGE_FIELD = "hop1"
ANSWER_FIELD = "answer"
PERCENTILE_METHOD = "linear"
STAT_NAMES = ("n", "min", "p25", "median", "mean", "p75", "p90", "p95", "p99", "max")
ALL = "ALL"
LARGEST_K = 20

Row = dict[str, Any]


# --- answer sizes -----------------------------------------------------------------------------

def answer_set(row: Row) -> frozenset[str]:
    """The row's answer list as a set of exact strings (protocol §0.4)."""
    return frozenset(row[ANSWER_FIELD])


def list_length(row: Row) -> int:
    return len(row[ANSWER_FIELD])


def set_size(row: Row) -> int:
    return len(answer_set(row))


def size_stats(sizes: Iterable[int]) -> dict[str, float | int]:
    """n, min, p25, median, mean, p75, p90, p95, p99, max of a non-empty list of sizes."""
    arr = np.asarray(list(sizes), dtype=float)
    if arr.size == 0:
        raise ValueError("size_stats needs at least one value")
    pct = {k: float(np.percentile(arr, q, method=PERCENTILE_METHOD))
           for k, q in (("p25", 25), ("median", 50), ("p75", 75),
                        ("p90", 90), ("p95", 95), ("p99", 99))}
    return {
        "n": int(arr.size),
        "min": int(arr.min()),
        "p25": pct["p25"],
        "median": pct["median"],
        "mean": float(arr.mean()),
        "p75": pct["p75"],
        "p90": pct["p90"],
        "p95": pct["p95"],
        "p99": pct["p99"],
        "max": int(arr.max()),
    }


def answer_size_table(rows: list[Row]) -> list[dict[str, Any]]:
    """One record per (group, measure): group ALL first, then each relation type sorted by name."""
    groups: dict[str, list[Row]] = defaultdict(list)
    for r in rows:
        groups[r[RELATION_FIELD]].append(r)
    out = []
    for group, members in [(ALL, rows)] + sorted(groups.items()):
        for measure, fn in (("list_length", list_length), ("set_size", set_size)):
            out.append({"group": group, "measure": measure,
                        **size_stats(fn(r) for r in members)})
    return out


# --- relation types ---------------------------------------------------------------------------

def relation_type_counts(rows: list[Row]) -> list[dict[str, Any]]:
    """Row counts per (relation_hop2, hop2_type, hop1_type, target_type); largest first."""
    c = Counter((r[RELATION_FIELD], *(r[f] for f in TYPE_FIELDS)) for r in rows)
    return [{RELATION_FIELD: k[0], **dict(zip(TYPE_FIELDS, k[1:])), "n_rows": n}
            for k, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))]


def type_field_mismatches(rows: list[Row]) -> list[str]:
    """row_ids whose relation_hop2 differs from "hop2_type:hop1_type:target_type"."""
    return [r["row_id"] for r in rows
            if r[RELATION_FIELD] != ":".join(r[f] for f in TYPE_FIELDS)]


# --- largest answer lists ---------------------------------------------------------------------

def _by_size_desc(rows: list[Row]) -> list[Row]:
    return sorted(rows, key=lambda r: (-list_length(r), r["row_id"]))


def largest_answers(rows: list[Row], k: int = LARGEST_K) -> list[dict[str, Any]]:
    """The k rows with the longest answer lists (ties: row_id ascending)."""
    return [{"rank": i + 1, "row_id": r["row_id"], RELATION_FIELD: r[RELATION_FIELD],
             "hop2": r["hop2"], BRIDGE_FIELD: r[BRIDGE_FIELD],
             "list_length": list_length(r), "set_size": set_size(r),
             QUESTION_FIELD: r[QUESTION_FIELD]}
            for i, r in enumerate(_by_size_desc(rows)[:k])]


def ties_beyond_cutoff(rows: list[Row], k: int = LARGEST_K) -> int:
    """Rows outside the top k whose list length equals the k-th row's (0 if there are ≤ k rows)."""
    ordered = _by_size_desc(rows)
    if len(ordered) <= k:
        return 0
    cutoff = list_length(ordered[k - 1])
    return sum(1 for r in ordered[k:] if list_length(r) == cutoff)


# --- duplicate question texts -----------------------------------------------------------------

def duplicate_question_groups(rows: list[Row]) -> list[dict[str, Any]]:
    """Groups of rows sharing an identical (exact-string) 2-hop question text, size > 1.

    For each group: number of rows, distinct hop1 values, distinct answer sets (protocol §0.4), and
    the sorted row_ids. Sorted by n_rows descending, then question text.
    """
    groups: dict[str, list[Row]] = defaultdict(list)
    for r in rows:
        groups[r[QUESTION_FIELD]].append(r)
    out = []
    for text, members in groups.items():
        if len(members) < 2:
            continue
        out.append({
            QUESTION_FIELD: text,
            "n_rows": len(members),
            "n_distinct_bridges": len({r[BRIDGE_FIELD] for r in members}),
            "n_distinct_answer_sets": len({answer_set(r) for r in members}),
            "row_ids": ";".join(sorted(r["row_id"] for r in members)),
        })
    out.sort(key=lambda g: (-g["n_rows"], g[QUESTION_FIELD]))
    return out


# --- repeated answer names --------------------------------------------------------------------

def repeated_answer_rows(rows: list[Row]) -> list[dict[str, Any]]:
    """Rows whose answer list contains the same exact name more than once, in row_id order."""
    out = []
    for r in sorted(rows, key=lambda r: r["row_id"]):
        c = Counter(r[ANSWER_FIELD])
        reps = sorted(name for name, n in c.items() if n > 1)
        if reps:
            out.append({"row_id": r["row_id"], RELATION_FIELD: r[RELATION_FIELD],
                        "list_length": list_length(r), "set_size": len(c),
                        "repeated_names": json.dumps(reps, ensure_ascii=False)})
    return out


# --- summary ----------------------------------------------------------------------------------

def summarize(rows: list[Row], biohopr_revision: str | None) -> dict[str, Any]:
    overall = size_stats(list_length(r) for r in rows)
    dups = duplicate_question_groups(rows)
    multi_bridge = [g for g in dups if g["n_distinct_bridges"] > 1]
    multi_ans = [g for g in dups if g["n_distinct_answer_sets"] > 1]
    return {
        "biohopr_revision": biohopr_revision,
        "n_rows": len(rows),
        "percentile_method": f"numpy.percentile method={PERCENTILE_METHOD!r}",
        "answer_list_length": overall,
        "answer_set_size": size_stats(set_size(r) for r in rows),
        "answer_list_length_median": overall["median"],
        "answer_list_length_p90": overall["p90"],
        "answer_list_length_p99": overall["p99"],
        "n_relation_types": len({r[RELATION_FIELD] for r in rows}),
        "n_rows_type_fields_disagree_with_relation_hop2": len(type_field_mismatches(rows)),
        "largest_answers_k": LARGEST_K,
        "largest_answers_ties_beyond_k": ties_beyond_cutoff(rows),
        "n_duplicate_question_groups": len(dups),
        "n_rows_in_duplicate_question_groups": sum(g["n_rows"] for g in dups),
        "n_duplicate_groups_gt1_bridge": len(multi_bridge),
        "n_duplicate_groups_gt1_answer_set": len(multi_ans),
        "n_duplicate_groups_gt1_bridge_and_gt1_answer_set":
            sum(1 for g in multi_bridge if g["n_distinct_answer_sets"] > 1),
        "n_rows_with_repeated_answer_names": len(repeated_answer_rows(rows)),
    }


# --- writers ----------------------------------------------------------------------------------

def write_csv(path: Path, records: list[dict[str, Any]], header: list[str]) -> None:
    """Write records with a fixed header (written even when there are no records)."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="raise")
        w.writeheader()
        w.writerows(records)


def write_answer_size_plot(rows: list[Row], path: Path) -> None:
    """Histograms of answer-list length (log-x): overall, then one panel per relation type.

    No threshold lines are drawn.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    groups: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        groups[r[RELATION_FIELD]].append(list_length(r))
    panels = [(f"{ALL} (n={len(rows)})", [list_length(r) for r in rows])] + [
        (f"{k} (n={len(v)})", v) for k, v in sorted(groups.items())]
    max_len = max(list_length(r) for r in rows)
    bins = np.logspace(0, np.log10(max(max_len, 2)) + 0.05, 30)

    ncols = 4
    nrows = -(-len(panels) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 2.8 * nrows), squeeze=False)
    for ax, (title, sizes) in zip(axes.flat, panels):
        ax.hist(sizes, bins=bins, color="#4C72B0")
        ax.set_xscale("log")
        ax.set_title(title, fontsize=8)
        ax.set_xlabel("answer-list length", fontsize=7)
        ax.set_ylabel("rows", fontsize=7)
        ax.tick_params(labelsize=7)
    for ax in list(axes.flat)[len(panels):]:
        ax.axis("off")
    fig.suptitle("BioHopR 2-hop answer-list length", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=120, metadata={"Software": None})
    plt.close(fig)


OUTPUT_HEADERS = {
    "answer_sizes.csv": ["group", "measure", *STAT_NAMES],
    "relation_types.csv": [RELATION_FIELD, *TYPE_FIELDS, "n_rows"],
    "largest_answers.csv": ["rank", "row_id", RELATION_FIELD, "hop2", BRIDGE_FIELD,
                            "list_length", "set_size", QUESTION_FIELD],
    "duplicate_questions.csv": [QUESTION_FIELD, "n_rows", "n_distinct_bridges",
                                "n_distinct_answer_sets", "row_ids"],
    "repeated_answers.csv": ["row_id", RELATION_FIELD, "list_length", "set_size",
                             "repeated_names"],
}


def write_all(rows: list[Row], out_dir: Path, biohopr_revision: str | None) -> dict[str, Any]:
    """Write every S3 output into out_dir and return the summary."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "answer_sizes.csv": answer_size_table(rows),
        "relation_types.csv": relation_type_counts(rows),
        "largest_answers.csv": largest_answers(rows),
        "duplicate_questions.csv": duplicate_question_groups(rows),
        "repeated_answers.csv": repeated_answer_rows(rows),
    }
    for name, records in tables.items():
        write_csv(out_dir / name, records, OUTPUT_HEADERS[name])
    write_answer_size_plot(rows, out_dir / "answer_sizes.png")
    summary = summarize(rows, biohopr_revision)
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary
