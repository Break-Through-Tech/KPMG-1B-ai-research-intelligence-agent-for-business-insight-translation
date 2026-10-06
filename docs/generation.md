# Grounded Summarization with Citations

## What it does

`src/generation.py` takes the papers retrieved for a question and has Gemini summarize what they say, citing the arXiv ID behind every finding. When the retrieved papers don't answer the question, it says so instead of guessing.

## How it works

1. **Group the retrieved chunks by paper.** `retrieval.search()` returns chunks, and several can come from the same paper. They're merged so each paper appears once, in rank order, with its arXiv ID, title, date and link.
2. **Ask Gemini for a structured answer.** The prompt lists each paper with its ID, and the system instruction tells the model to use only those papers, cite an ID for every finding, and set `answerable` to false when the papers don't cover the question. Gemini's JSON mode makes it return `answerable`, a list of `findings` (each a statement with its citations), and `gaps` (what the papers don't cover).
3. **Check every citation.** Each cited ID is compared against the papers that were actually retrieved. Citations that don't match are removed, and a finding left with no valid citation is dropped, so nothing unsupported reaches a reader. The number of removed citations is reported.
4. **Fall back honestly.** If the model says the papers don't answer the question, or none of its findings survive the citation check, the output says "The retrieved papers don't answer this question." and lists the papers that were retrieved.

## Running it

Get a free API key from Google AI Studio (https://aistudio.google.com/apikey) and add it to `.env` as `GEMINI_API_KEY`. Then, from the repo root, after running preprocessing:

```bash
pip install -r requirements.txt
python src/generation.py "How can language models reduce computational cost?"
python src/generation.py "How can language models reduce computational cost?" --json
```

`--top-k` sets how many chunks to retrieve (default 8, which usually becomes 5 to 8 papers). `--model` or `GEMINI_MODEL` in `.env` picks the Gemini model. The free tier has per-minute limits, so the code waits and retries when Gemini reports a rate limit.

## Output format

```markdown
## <the question>

- <finding> [<arXiv ID>]
- <finding> [<arXiv ID>, <arXiv ID>]

**Not covered by these papers.** <gaps, if any>

**Sources**
- [<arXiv ID>] <title> (<date>) https://arxiv.org/abs/<arXiv ID>
```

`--json` returns the same result as a dictionary, which the business translation step (October, week 7) can build on directly.

## Tests

```bash
python -m pytest tests
```

The tests use a fake model, so they run offline without an API key. They cover grouping chunks by paper, the prompt, keeping valid citations and removing made-up ones, the "doesn't answer" cases, unreadable model output, and retrying when Gemini is rate limited.

## Limitations and next steps

- The citation check confirms that a cited paper was retrieved, not that it supports the specific finding. Checking that, for example with RAGAS faithfulness or a second model call, belongs in the October evaluation work.
- The corpus is currently abstracts only, so findings are limited to what abstracts say.
- The next step is the business translation prompt, which turns these findings into implications for KPMG clients.
