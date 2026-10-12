"""
Compares Agent 1's title-tier scores against hand-ranked human warmth scores
for evals/hand_rank_sample.csv.

Reports:
- Spearman rank correlation (does the agent's ordering track the human ordering at all?)
- Top-5 by agent vs top-5 by human, and how much they overlap
- Every row sorted by |agent - human| delta, biggest mismatches first
"""
import argparse
import csv
from statistics import mean


def spearman(xs, ys):
    n = len(xs)
    def ranks(vals):
        sorted_idx = sorted(range(n), key=lambda i: vals[i])
        r = [0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[sorted_idx[j + 1]] == vals[sorted_idx[i]]:
                j += 1
            avg_rank = mean(range(i + 1, j + 2))
            for k in range(i, j + 1):
                r[sorted_idx[k]] = avg_rank
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1 - (6 * d2) / (n * (n ** 2 - 1))


def main():
    parser = argparse.ArgumentParser(description="Compare an Agent 1 score column against hand-ranked human warmth scores.")
    parser.add_argument("--csv", default="evals/sample_hand_rank.csv", help="Path to the hand-ranked CSV")
    parser.add_argument("--score-col", default="agent1_score", help="Column to compare against human_score")
    args = parser.parse_args()

    rows = []
    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if args.score_col not in (reader.fieldnames or []):
            raise SystemExit(
                f"Column '{args.score_col}' not found in {args.csv}. "
                f"Available columns: {reader.fieldnames}"
            )
        for r in reader:
            if not r.get("human_score"):
                continue
            r["agent1_score"] = float(r[args.score_col])
            r["human_score"] = float(r["human_score"])
            r["name"] = f"{r['first_name']} {r['last_name']}"
            rows.append(r)

    agent_scores = [r["agent1_score"] for r in rows]
    human_scores = [r["human_score"] for r in rows]
    rho = spearman(agent_scores, human_scores)

    print(f"n = {len(rows)}  (score column: {args.score_col})")
    print(f"Spearman rank correlation ({args.score_col} vs human): {rho:.3f}\n")

    top5_agent = {r["name"] for r in sorted(rows, key=lambda r: r["agent1_score"], reverse=True)[:5]}
    top5_human = {r["name"] for r in sorted(rows, key=lambda r: r["human_score"], reverse=True)[:5]}
    overlap = top5_agent & top5_human
    print(f"Top 5 by agent score:  {sorted(top5_agent)}")
    print(f"Top 5 by human warmth: {sorted(top5_human)}")
    print(f"Overlap: {len(overlap)}/5 -> {sorted(overlap)}\n")

    print("Missed (human top-5, agent ranked them lower):")
    for name in sorted(top5_human - top5_agent):
        r = next(r for r in rows if r["name"] == name)
        print(f"  - {name}: agent={r['agent1_score']}, human={r['human_score']} ({r['position']})")

    print("\nOverranked (agent top-5, human warmth says otherwise):")
    for name in sorted(top5_agent - top5_human):
        r = next(r for r in rows if r["name"] == name)
        print(f"  - {name}: agent={r['agent1_score']}, human={r['human_score']} ({r['position']})")

    print("\nAll rows by |agent - human| delta, biggest mismatch first:")
    for r in sorted(rows, key=lambda r: abs(r["agent1_score"] - r["human_score"]), reverse=True):
        delta = r["human_score"] - r["agent1_score"]
        sign = "+" if delta > 0 else ""
        print(f"  {sign}{delta:>4.1f}  agent={r['agent1_score']:<4} human={r['human_score']:<4} {r['name']:<20} {r['position']}")


if __name__ == "__main__":
    main()
