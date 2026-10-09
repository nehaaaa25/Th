import csv
import json
from pathlib import Path

import pytest

from cofail_kg.data.diagnostics import (
    OUTPUT_HEADERS,
    answer_size_table,
    duplicate_question_groups,
    largest_answers,
    relation_type_counts,
    repeated_answer_rows,
    size_stats,
    summarize,
    ties_beyond_cutoff,
    type_field_mismatches,
    write_all,
)

REAL_DIR = Path(__file__).resolve().parents[1] / "data/raw/biohopr"

R1 = "drug:gene/protein:disease"
R2 = "disease:drug:effect/phenotype"


def _row(i, rel, hop1, answer, question, types=None):
    t = types or rel.split(":")
    return {
        "row_id": f"BH2_{i:05d}",
        "relation_hop2": rel,
        "hop2_type": t[0], "hop1_type": t[1], "target_type": t[2],
        "hop1": hop1,
        "hop2": f"S{i}",
        "answer": answer,
        "hop2_question_multi": question,
    }


@pytest.fixture
def rows():
    return [
        # Q_A: same text, 2 bridges, 2 answer sets.
        _row(0, R1, "G1", ["a", "b"], "Q_A"),
        _row(1, R1, "G2", ["c"], "Q_A"),
        # Q_B: same text, 1 bridge, answer lists equal as sets (order, repeats ignored).
        _row(2, R1, "G3", ["a", "b"], "Q_B"),
        _row(3, R1, "G3", ["b", "a", "a"], "Q_B"),
        # Q_C: same text, 1 bridge, case differs -> 2 answer sets (exact strings).
        _row(4, R2, "D1", ["x"], "Q_C"),
        _row(5, R2, "D1", ["X"], "Q_C"),
        # Unique texts.
        _row(6, R2, "D2", ["p", "q", "r", "s"], "Q_D"),
        _row(7, R2, "D3", ["p", "q", "r", "s"], "Q_E", types=["disease", "drug", "other"]),
    ]


def test_size_stats_known_values():
    s = size_stats([1, 2, 3, 4])
    assert s["n"] == 4 and s["min"] == 1 and s["max"] == 4
    assert s["median"] == 2.5 and s["mean"] == 2.5
    assert s["p25"] == 1.75 and s["p75"] == 3.25
    assert s["p90"] == pytest.approx(3.7)
    assert size_stats([5])["p99"] == 5.0
    with pytest.raises(ValueError):
        size_stats([])


def test_answer_size_table(rows):
    t = answer_size_table(rows)
    assert [(r["group"], r["measure"]) for r in t] == [
        ("ALL", "list_length"), ("ALL", "set_size"),
        (R2, "list_length"), (R2, "set_size"),
        (R1, "list_length"), (R1, "set_size"),
    ]
    all_len = t[0]
    assert all_len["n"] == 8 and all_len["max"] == 4 and all_len["min"] == 1
    # Row 3 has list length 3 but set size 2.
    r1_len, r1_set = t[4], t[5]
    assert r1_len["max"] == 3 and r1_set["max"] == 2


def test_relation_type_counts_and_mismatch(rows):
    counts = relation_type_counts(rows)
    assert [(c["relation_hop2"], c["target_type"], c["n_rows"]) for c in counts] == [
        (R1, "disease", 4), (R2, "effect/phenotype", 3), (R2, "other", 1)]
    assert sum(c["n_rows"] for c in counts) == len(rows)
    assert type_field_mismatches(rows) == ["BH2_00007"]


def test_largest_answers_tie_break(rows):
    top = largest_answers(rows, k=3)
    assert [r["row_id"] for r in top] == ["BH2_00006", "BH2_00007", "BH2_00003"]
    assert [r["rank"] for r in top] == [1, 2, 3]
    assert top[2]["list_length"] == 3 and top[2]["set_size"] == 2
    # k=1 cuts between two rows of length 4.
    assert ties_beyond_cutoff(rows, k=1) == 1
    assert ties_beyond_cutoff(rows, k=3) == 0
    assert ties_beyond_cutoff(rows, k=20) == 0


def test_duplicate_question_groups(rows):
    groups = {g["hop2_question_multi"]: g for g in duplicate_question_groups(rows)}
    assert set(groups) == {"Q_A", "Q_B", "Q_C"}
    assert (groups["Q_A"]["n_distinct_bridges"], groups["Q_A"]["n_distinct_answer_sets"]) == (2, 2)
    assert (groups["Q_B"]["n_distinct_bridges"], groups["Q_B"]["n_distinct_answer_sets"]) == (1, 1)
    assert (groups["Q_C"]["n_distinct_bridges"], groups["Q_C"]["n_distinct_answer_sets"]) == (1, 2)
    assert groups["Q_A"]["row_ids"] == "BH2_00000;BH2_00001"


def test_repeated_answer_rows(rows):
    reps = repeated_answer_rows(rows)
    assert [r["row_id"] for r in reps] == ["BH2_00003"]
    assert json.loads(reps[0]["repeated_names"]) == ["a"]
    assert (reps[0]["list_length"], reps[0]["set_size"]) == (3, 2)


def test_summary(rows):
    s = summarize(rows, "rev0")
    assert s["n_rows"] == 8
    assert s["biohopr_revision"] == "rev0"
    assert s["n_relation_types"] == 2
    assert s["n_rows_type_fields_disagree_with_relation_hop2"] == 1
    assert s["n_duplicate_question_groups"] == 3
    assert s["n_rows_in_duplicate_question_groups"] == 6
    assert s["n_duplicate_groups_gt1_bridge"] == 1
    assert s["n_duplicate_groups_gt1_answer_set"] == 2
    assert s["n_duplicate_groups_gt1_bridge_and_gt1_answer_set"] == 1
    assert s["n_rows_with_repeated_answer_names"] == 1
    assert s["answer_list_length_median"] == s["answer_list_length"]["median"]


def test_write_all_files_and_rerun_identical(rows, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    write_all(rows, a, "rev0")
    write_all(list(reversed(rows)), b, "rev0")  # input order must not matter
    for name, header in OUTPUT_HEADERS.items():
        with open(a / name, encoding="utf-8", newline="") as f:
            assert next(csv.reader(f)) == header
        assert (a / name).read_bytes() == (b / name).read_bytes(), name
    assert (a / "summary.json").read_bytes() == (b / "summary.json").read_bytes()
    assert (a / "answer_sizes.png").stat().st_size > 0
    summary = json.loads((a / "summary.json").read_text(encoding="utf-8"))
    assert summary["n_rows"] == 8


@pytest.mark.skipif(not (REAL_DIR / "metadata.json").exists(),
                    reason="real BioHopR not downloaded (scripts/02_download_biohopr.py)")
def test_real_file_counts():
    from cofail_kg.data.biohopr_loader import load_biohopr

    real = load_biohopr(REAL_DIR)
    assert len(real) == 7633
    assert sum(c["n_rows"] for c in relation_type_counts(real)) == 7633
    assert summarize(real, None)["n_relation_types"] == 12
