# Warm Path

A small two-agent tool, built on the Anthropic SDK, for researching a target company before reaching out: who in my own network works there, and what hiring signals are public right now. It ships with an **eval harness**, because the first question about any tool like this should be "does it actually work?"

> **Honest framing:** this is a prototype. It was written with Claude's help (AI-assisted). I specified the design, reviewed the code, and built the evals to test it. The most useful part of the repo is the eval write-up below, including what the eval showed was *wrong* with my own approach.

## What it does

| Agent | Job | How |
|---|---|---|
| **Agent 1** (`src/agent1_warmpath.py`) | Filter a LinkedIn connections export by company and sort by seniority tier | Title-keyword matching with word-boundary regex. Deterministic, no LLM call. |
| **Agent 2** (`src/agent2_hiring_signals.py`) | Pull live hiring signals for a company and role (leadership changes, open roles, funding) with cited sources | Claude with the web search tool; each finding carries a source URL, source type, role-match label, date confidence, and a clearly separated model interpretation. |
| **Combined** (`src/combined_warmpath.py`) | Run both against one company | |

## Run it

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your ANTHROPIC_API_KEY (needed for Agent 2 only)

python3 src/agent1_warmpath.py       # runs on data/sample_connections.csv (synthetic)
python3 src/combined_warmpath.py     # Agent 1 + Agent 2
```

To use your own data, export your LinkedIn connections and point at the file:
`CONNECTIONS_CSV=path/to/Connections.csv python3 src/agent1_warmpath.py`.
`data/` and real eval files are gitignored on purpose; see **Privacy** below.

## The eval (the interesting part)

Agent 1 scores seniority from job titles. I wanted to know if that tracks what I actually care about: *who would plausibly make an introduction.*

1. **Measure.** I hand-ranked 20 real connections at one company by actual referral warmth and compared against Agent 1's automated score (`evals/extract_eval_sample.py`, `evals/compare_scores.py`). Spearman rank correlation: **about 0.17**, close to no relationship.
2. **Find the bug.** Building the eval exposed a real defect: the scorer used substring matching, so `coo` matched inside "Coordinator" and scored a coordinator as C-suite; the same flaw hit the VP exclusion (`vice` inside "service"). Fixed with word-boundary regex (`evals/rescore_after_fix.py` re-scores non-destructively).
3. **Re-measure.** Correlation barely moved. So the low score was **not** the bug. It is a limit of the approach: title seniority is a weak proxy for relationship warmth.
4. **Don't overclaim.** I changed the tool's output from implying a "warmth score" to labeling it a **"seniority tier"**, and documented it as a sorting aid, not a prioritization of who to contact.

The 20 real ratings are about real people, so they are not published. `evals/sample_hand_rank.csv` is a **synthetic** stand-in with placeholder scores so the pipeline can be run end to end. Its correlation number means nothing; only the real measurement above does.

## Known limitations

- Seniority tiers collapse some distinct titles ("Group VP" and "VP" both tier 3; "Chief of Staff" scores like a C-suite title). Known, deferred; the eval showed it matters less than the overall weak signal.
- Agent 2 is non-deterministic. It uses live web search, so results vary run to run, and there is no caching.
- Agent 2's "significance" language is the model's interpretation on top of citations, not verified fact. Source dates can mislead even when the citation is real (one run surfaced a 2022 article with a stale 2026 timestamp). Spot-check anything before using it in outreach.
- Agent 2 over-relies on job aggregators because of their search ranking; careers pages are more authoritative but underrepresented.
- No automated tests beyond the eval harness. `docs/example_output_format.md` is illustrative only.

## What a production version would need

Auth and per-user data isolation (this reads a local CSV); rate limiting and cost controls on search calls; logging and tracing of every model call; result caching; a relationship-warmth signal that actually predicts introductions (interaction recency, shared history) instead of title; and a larger, less hand-built eval set.

## Privacy

This tool works on personal network data. Real connection exports and hand-ranked results are excluded from version control (`.gitignore`) and should never be committed. The sample data in this repo is entirely synthetic.
