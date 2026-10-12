import csv
import os
import re

def load_connections(filepath):
    connections = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Company'):  # skip blank/garbage rows
                connections.append(row)
    return connections

def filter_by_company(connections, company_name):
    return [c for c in connections if company_name.lower() in c.get('Company', '').lower()]

def _contains_keyword(title, keyword):
    # word-boundary match, not substring — 'coo' must not match inside
    # 'coordinator', 'vice' must not match inside 'service'. \s+ (not a
    # literal space) joins multi-word phrases so irregular whitespace in
    # real LinkedIn export text doesn't silently break the match.
    pattern = r'\b' + r'\s+'.join(re.escape(tok) for tok in keyword.split()) + r'\b'
    return re.search(pattern, title) is not None

def _contains_any_keyword(title, keywords):
    return any(_contains_keyword(title, kw) for kw in keywords)

def score_connection(c):
    title = c.get('Position', '').lower()
    if _contains_any_keyword(title, ['chief', 'ceo', 'cfo', 'coo', 'president']) and not _contains_keyword(title, 'vice'):
        return 5
    if _contains_any_keyword(title, ['evp', 'executive vice president']):
        return 4
    if _contains_any_keyword(title, ['svp', 'senior vice president']):
        return 3.5
    if _contains_any_keyword(title, ['founder', 'cofounder']):
        return 4
    if _contains_any_keyword(title, ['group vice president', 'area vice president', 'vp', 'vice president', 'head of']):
        return 3
    if _contains_any_keyword(title, ['senior director', 'sr. director']):
        return 2.5
    if _contains_keyword(title, 'director'):
        return 2
    if _contains_keyword(title, 'manager'):
        return 1
    return 0

if __name__ == "__main__":
    connections = load_connections(os.environ.get("CONNECTIONS_CSV", "data/sample_connections.csv"))
    print(f"Loaded {len(connections)} connections.\n")

    target = input("Enter a target company: ")
    matches = filter_by_company(connections, target)
    ranked = sorted(matches, key=score_connection, reverse=True)

    print(f"\nFound {len(ranked)} connection(s) at {target}, ranked by seniority tier (title-based — not a warmth or referral-priority signal):")
    for c in ranked:
        score = score_connection(c)
        print(f"- [seniority tier {score}] {c['First Name']} {c['Last Name']}, {c['Position']}")