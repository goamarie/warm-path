"""
Pulls a hand-rankable sample of connections at one target company for the Agent 1 eval.

Stratified, not random: takes ALL of the rare high tiers (3.5+, where the
title-keyword scoring is most likely to collapse distinct seniority levels
into one bucket) plus a random slice of the common tiers, so the 20-person
sample actually exercises the weak spots instead of just reflecting the
overall distribution.

Writes evals/hand_rank_sample.csv with an empty human_score column for
manual fill-in.
"""
import csv
import os
import sys
import random

sys.path.insert(0, "../src")
sys.path.insert(0, "src")
from agent1_warmpath import load_connections, filter_by_company, score_connection

TARGET_COMPANY = os.environ.get("TARGET_COMPANY", "Northwind Systems")
SEED = 42  # fixed so the sample is reproducible across runs

STRATA = [
    (lambda s: s >= 3.5, None),   # take all — rare, and exactly where collapse risk lives
    (lambda s: s == 3, 3),
    (lambda s: s == 2.5, 3),
    (lambda s: s == 2, 3),
    (lambda s: s == 1, 2),
    (lambda s: s == 0, 2),
]


def main():
    connections = load_connections(os.environ.get("CONNECTIONS_CSV", "data/sample_connections.csv"))
    matches = filter_by_company(connections, TARGET_COMPANY)
    scored = [(c, score_connection(c)) for c in matches]

    rng = random.Random(SEED)
    sample = []
    for predicate, n in STRATA:
        bucket = [cs for cs in scored if predicate(cs[1])]
        if n is None:
            sample.extend(bucket)
        else:
            sample.extend(rng.sample(bucket, min(n, len(bucket))))

    sample.sort(key=lambda cs: cs[1], reverse=True)

    out_path = os.environ.get("EVAL_CSV", "evals/sample_hand_rank.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["first_name", "last_name", "position", "agent1_score", "human_score", "notes"])
        for c, score in sample:
            writer.writerow([c.get("First Name", ""), c.get("Last Name", ""), c.get("Position", ""), score, "", ""])

    print(f"Wrote {len(sample)} candidates to {out_path}")
    print("Fill in human_score (1-5, your honest read on warmth/relevance) for each row.")


if __name__ == "__main__":
    main()
