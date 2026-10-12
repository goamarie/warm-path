# Example Agent 2 output format (illustrative, not a real run)

The company, URLs and findings below are fictional. This shows the *shape* of Agent 2's output so you can see how
citations, confidence labels and model interpretation are kept separate. Real runs vary from run to run.

Company: Northwind Systems | Role: Technical Product Marketing

### 1. Leadership change in marketing
- **cited_fact:** (a sentence taken from the source, not paraphrased into a conclusion)
- **source_url:** https://example.com/news/northwind-names-new-cmo
- **source_type:** press | official | aggregator | social
- **role_match:** exact_title | closely_related | adjacent_department | none
- **date_confidence:** confirmed | uncertain (flagged when the page date and the content disagree)
- **interpretation:** (the model's read of why this might matter; labeled as interpretation, not fact)

Each real run ends with a Sources list, and a one-line caveat that results are live and point-in-time and should be confirmed before outreach.
