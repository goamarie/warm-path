"""
Recomputes each row's Agent 1 score using the fixed score_connection()
against the EXISTING evals/hand_rank_sample.csv, writing the result into a
new `agent1_score_after` column in that same file.

Does NOT touch human_score or notes (or any other existing column) — those
are hand-collected and must not be regenerated. Never calls
extract_eval_sample.py's sampling logic and never re-derives rows from
data/connections_real.csv; only reads each row's own `position` field back
out of hand_rank_sample.csv and rescores that row in place. No cross-row
matching, so duplicate titles across rows are not ambiguous.

Safe to re-run: a one-time backup of the pre-fix file is kept at
evals/hand_rank_sample.csv.bak (only created if it doesn't already exist),
and the write itself is atomic (temp file + os.replace).

Run from the repo root: python3 evals/rescore_after_fix.py
"""
import csv
import os
import shutil
import sys

sys.path.insert(0, "../src")
sys.path.insert(0, "src")
from agent1_warmpath import score_connection

CSV_PATH = os.environ.get("EVAL_CSV", "evals/sample_hand_rank.csv")
BACKUP_PATH = CSV_PATH + ".bak"
NEW_COLUMN = "agent1_score_after"


def main():
    if not os.path.exists(BACKUP_PATH):
        shutil.copy2(CSV_PATH, BACKUP_PATH)
        print(f"Backed up original file to {BACKUP_PATH}")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    if NEW_COLUMN not in fieldnames:
        fieldnames.append(NEW_COLUMN)

    changed = []
    for row in rows:
        before = row.get("agent1_score")
        after = score_connection({"Position": row["position"]})
        row[NEW_COLUMN] = after
        if before not in (None, "") and float(before) != float(after):
            changed.append((row["first_name"], row["last_name"], before, after))

    tmp_path = CSV_PATH + ".tmp"
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp_path, CSV_PATH)

    print(f"Rescored {len(rows)} rows -> wrote '{NEW_COLUMN}' column in {CSV_PATH}")
    print(f"Rows where the score changed vs the original agent1_score ({len(changed)}):")
    for first, last, before, after in changed:
        print(f"  {first} {last}: {before} -> {after}")


if __name__ == "__main__":
    main()
