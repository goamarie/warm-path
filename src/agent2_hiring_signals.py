import re
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()


def _sanitize_company_domain(company_domain):
    if not company_domain:
        return None
    domain = company_domain.strip().lower()
    match = re.match(r'^(?:https?://)?(?:www\.)?([^/]+)', domain)
    domain = match.group(1) if match else domain
    return domain or None


def _infer_company_domain(company_name):
    """Infer a likely company domain from a company name.

    Uses a simple heuristic when the user does not provide a domain.
    """
    cleaned = company_name.strip().lower()
    if cleaned.endswith(".com") or cleaned.endswith(".io") or cleaned.endswith(".co") or cleaned.endswith(".ai"):
        return cleaned
    cleaned = cleaned.replace("&", "and").replace(" ", "").replace("-", "").replace("'", "")
    cleaned = ''.join(ch for ch in cleaned if ch.isalnum())
    return f"{cleaned}.com" if cleaned else None


def get_hiring_signals(company_name, role, company_domain=None):
    """
    Disclaimer notes for Agent 2 output (hiring signals):

    1. Non-determinism: results are pulled via live web search with no caching.
       Re-running against the same target company can surface different results
       on different days — do not imply consistent or repeatable output in a demo.

    2. Inference vs. fact: "significance" language (e.g. "strategic shift,"
       "highly significant") is Claude's interpretation layered on top of cited
       sources — it is not itself a verified claim. Treat it as analysis, not data.

    3. Source reliability: dates on cited articles can be misleading even when
       the citation itself is real (e.g. a stale "last updated" timestamp on an
       old article). Always spot-check personnel/leadership claims and dates
       before using them in outreach — this is not automated in v1.

    4. Source bias: results skew toward high-SEO job aggregator sites
       (e.g. ZipRecruiter) over more authoritative but lower-ranked sources like
       company careers pages, unless explicitly prioritized in the prompt.
    """
    inferred_domain = False
    company_domain = _sanitize_company_domain(company_domain)
    if company_domain is None:
        company_domain = _infer_company_domain(company_name)
        inferred_domain = True
    domain_hint = f" (try site:{company_domain}/careers or site:{company_domain}/news)" if company_domain else ""

    prompt = (
        f"What recent hiring, funding, or leadership signals exist for {company_name} "
        f"relevant to {role} roles?\n\n"
        f"Include exact title matches as well as closely related titles that a "
        f"reasonable recruiter would consider equivalent or adjacent (e.g. if the "
        f"target is 'Product Marketing Manager', also surface 'Senior PMM', 'Head of "
        f"Product Marketing', or 'Growth Marketing Lead' if genuinely relevant — use "
        f"judgment, don't force a stretch match). Focus on news from the last 3 months.\n\n"
        f"Run at least two searches: one general search on {company_name} hiring/leadership "
        f"news related to {role}, and one scoped specifically to the company's own "
        f"site{domain_hint} to surface official sources that general search may miss.\n\n"
        f"When searching for open roles, prioritize the company's own careers page over "
        f"third-party aggregators like ZipRecruiter or Indeed — use aggregators only if no "
        f"better source exists, and flag it when you do.\n\n"
        f"For EACH finding, return it in this exact structure:\n"
        f"- cited_fact: the specific claim, stated plainly, no interpretation\n"
        f"- source_url: the URL\n"
        f"- source_type: one of [official, press, employee_post, aggregator, other]\n"
        f"- role_match: how closely this relates to {role} — one of "
        f"[exact_title, closely_related, adjacent_department, not_role_specific]\n"
        f"- date_confidence: [confirmed, uncertain, mismatch_detected] — flag if the "
        f"article's actual content (names, quotes, context) seems inconsistent with its "
        f"claimed publish date, e.g. republished or stale content\n"
        f"- claude_interpretation: your read on why this matters, clearly separated from "
        f"the cited_fact above\n\n"
        f"Return findings as a numbered list using this structure."
    )

    try:
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5
            }]
        )
        stop_reason = getattr(response, "stop_reason", None)
    except Exception as exc:
        return (
            f"Error fetching hiring signals: {exc}\n"
            "Please check network connectivity, API credentials, or rate limits and retry."
        )

    summary = ""
    sources = []

    for block in response.content:
        if block.type == "text":
            summary += block.text
            if hasattr(block, "citations") and block.citations:
                for c in block.citations:
                    sources.append(f"{c.title} — {c.url}")

    output = ""
    if inferred_domain and company_domain:
        output += f"Inferred domain: {company_domain}\n"
    elif inferred_domain:
        output += "Could not infer a domain — searching without a site-scoped hint.\n"
    elif company_domain:
        output += f"Using supplied domain: {company_domain}\n"
    output += (
        "⚠️ Hiring signals are live, point-in-time web search results — re-runs may vary. "
        "\"Significance\" framing is Claude's interpretation, not verified fact. "
        "Confirm personnel/dates before outreach.\n\n"
    )

    output += summary
    if sources:
        output += "\n\nSources:\n" + "\n".join(set(sources))
    else:
        output += "\n\n⚠️ No sources returned — treat this summary as unverified."

    if stop_reason == "max_tokens":
        output += "\n\n⚠️ Response truncated: max_tokens reached. Increase max_tokens to avoid incomplete results."

    return output

if __name__ == "__main__":
    company = input("Enter a target company: ")
    role = input("Enter target role (e.g. 'Product Marketing Manager'): ")
    domain = input("Enter company domain (optional, e.g. acme.com): ").strip() or None

    print(f"\nSearching hiring signals for {company} ({role})...\n")
    signals = get_hiring_signals(company, role, domain)
    print(signals)