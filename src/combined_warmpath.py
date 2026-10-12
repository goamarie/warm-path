import os
from agent1_warmpath import load_connections, filter_by_company, score_connection
from agent2_hiring_signals import get_hiring_signals

if __name__ == "__main__":
    connections = load_connections(os.environ.get("CONNECTIONS_CSV", "data/sample_connections.csv"))
    print(f"Loaded {len(connections)} connections.\n")

    target = input("Enter a target company: ")
    role = input("Enter target role (e.g. 'Product Marketing Manager'): ")
    domain = input("Enter company domain (optional, e.g. acme.com): ").strip() or None

    # Agent 1: ranked warm paths
    matches = filter_by_company(connections, target)
    ranked = sorted(matches, key=score_connection, reverse=True)

    print(f"\n=== WARM PATHS AT {target.upper()} ===")
    print(f"Found {len(ranked)} connection(s), ranked by seniority tier (title-based — not a warmth or referral-priority signal):\n")
    for c in ranked:
        score = score_connection(c)
        print(f"- [seniority tier {score}] {c['First Name']} {c['Last Name']}, {c['Position']}")

    # Agent 2: hiring signals
    print(f"\n=== HIRING SIGNALS AT {target.upper()} ===")
    print(f"Searching...\n")
    signals = get_hiring_signals(target, role, domain)
    print(signals)