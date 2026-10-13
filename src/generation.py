"""
Grounded summarization with citations.

Takes the papers retrieved for a question and asks Gemini to summarize what
they say, citing the arXiv ID behind every finding. Every citation is checked
against the papers that were actually retrieved. A finding with no valid
citation is dropped, and when the papers don't answer the question the summary
says so instead of guessing.

Run from the repo root, after preprocessing has written the chunks:

    python src/generation.py "How can language models reduce computational cost?"
    python src/generation.py "..." --top-k 8 --json

Needs GEMINI_API_KEY in .env (a free key from Google AI Studio).
GEMINI_MODEL picks the model, and defaults to a free-tier Flash model.
"""

import argparse
import json
import os
import re
import sys
import time

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
NOT_ANSWERED = "The retrieved papers don't answer this question."
RETRYABLE = {429, 500, 503}  # rate limited or temporarily unavailable

SYSTEM_INSTRUCTION = """You summarize AI research papers for KPMG analysts.

Rules you must follow.
1. Use only the sources provided. Do not use outside knowledge, even if you know more about the topic.
2. Every finding must cite at least one source ID from the sources list, exactly as written (for example "2608.20316").
3. Only cite a source for a finding it actually supports.
4. If the sources do not contain information that answers the question, set "answerable" to false and leave "findings" empty. Do not stretch loosely related sources to fit.
5. If the sources answer only part of the question, answer that part and describe what is missing in "gaps".
6. Write each finding as one or two plain sentences. State results the way the paper does, and say so when a result is preliminary or limited to one setting.
7. Do not put source IDs inside the finding text itself. Put them in "citations"."""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "answerable": {
            "type": "boolean",
            "description": "True only if the sources contain information that answers the question.",
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "statement": {"type": "string"},
                    "citations": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["statement", "citations"],
            },
        },
        "gaps": {
            "type": "string",
            "description": "What the question asks that the sources do not cover. Empty if nothing is missing.",
        },
    },
    "required": ["answerable", "findings", "gaps"],
}


# ---------------------------------------------------------------- sources

def arxiv_id(paper_id):
    """'http://arxiv.org/abs/2608.20316v1' becomes '2608.20316'."""
    tail = str(paper_id).strip().rstrip("/").split("/abs/")[-1]
    tail = re.sub(r"^arxiv:", "", tail, flags=re.IGNORECASE)
    return re.sub(r"v\d+$", "", tail)


def collect_sources(results):
    """
    Turn the raw ChromaDB results from retrieval.search() into one entry per
    paper, in rank order. Chunks from the same paper are merged, so a paper that
    matched twice is still cited once.
    """
    if not results or not results.get("documents") or not results["documents"][0]:
        return []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = (results.get("distances") or [[None] * len(documents)])[0]

    sources = {}
    for text, meta, distance in zip(documents, metadatas, distances):
        sid = arxiv_id(meta["paper_id"])
        if sid not in sources:
            sources[sid] = {
                "id": sid,
                "title": meta.get("title", ""),
                "published": (meta.get("published") or "")[:10],
                "url": f"https://arxiv.org/abs/{sid}",
                "rank": len(sources) + 1,
                "distance": distance,
                "texts": [],
            }
        if text not in sources[sid]["texts"]:
            sources[sid]["texts"].append(text)
    return list(sources.values())


def build_prompt(question, sources):
    blocks = []
    for s in sources:
        body = " ".join(s["texts"])
        blocks.append(f"[{s['id']}] {s['title']} (published {s['published']})\n{body}")
    return (
        f"Question: {question}\n\n"
        f"Sources ({len(sources)} papers):\n\n" + "\n\n".join(blocks) + "\n\n"
        "Summarize what these sources say that answers the question, following the rules."
    )


# ---------------------------------------------------------------- the model

def call_gemini(prompt, model=DEFAULT_MODEL, client=None, retries=3, wait_s=5.0):
    """Ask Gemini for a JSON answer that matches RESPONSE_SCHEMA. Retries when rate limited."""
    from google import genai
    from google.genai import errors, types

    if client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Set GEMINI_API_KEY in .env. Get a free key at https://aistudio.google.com/apikey")
        client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_json_schema=RESPONSE_SCHEMA,
        temperature=0.2,
    )
    for attempt in range(retries + 1):
        try:
            return client.models.generate_content(model=model, contents=prompt, config=config).text
        except errors.APIError as err:
            if getattr(err, "code", None) not in RETRYABLE or attempt == retries:
                raise
            delay = wait_s * (2 ** attempt)
            print(f"Gemini returned {err.code}, retrying in {delay:.0f}s", file=sys.stderr)
            time.sleep(delay)


def parse_response(text):
    """The model's JSON, tolerating a stray code fence around it."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip())
    return json.loads(cleaned)


# ---------------------------------------------------------------- checking

def check_citations(answer, sources):
    """
    Keep only citations that point at a retrieved paper, and drop any finding
    left with none. Returns the checked findings and the citations that were
    removed, so nothing unverified reaches a reader.
    """
    valid = {s["id"] for s in sources}
    findings, removed = [], []
    for f in answer.get("findings") or []:
        statement = re.sub(r"\s*\[[^\]]*\]", "", str(f.get("statement", ""))).strip()
        kept = []
        for c in f.get("citations") or []:
            cid = arxiv_id(str(c).strip("[] "))
            if cid in valid and cid not in kept:
                kept.append(cid)
            elif cid not in valid:
                removed.append(str(c))
        if statement and kept:
            findings.append({"statement": statement, "citations": kept})
    return findings, removed


def summarize(question, results, llm=None, model=DEFAULT_MODEL):
    """
    The whole step. Returns a dict with the question, whether it was answered,
    the checked findings, any gaps, the sources, and anything that was removed.
    `llm` is a function from prompt to JSON text, which tests replace with a fake.
    """
    sources = collect_sources(results)
    result = {
        "question": question,
        "model": model,
        "answered": False,
        "findings": [],
        "gaps": "",
        "sources": [{k: v for k, v in s.items() if k != "texts"} for s in sources],
        "removed_citations": [],
        "note": "",
    }
    if not sources:
        result["note"] = "No papers were retrieved for this question."
        return result

    llm = llm or (lambda prompt: call_gemini(prompt, model=model))
    try:
        answer = parse_response(llm(build_prompt(question, sources)))
    except (json.JSONDecodeError, TypeError):
        result["note"] = "The model's response couldn't be read, so no summary was produced."
        return result

    findings, removed = check_citations(answer, sources)
    result["findings"] = findings
    result["removed_citations"] = removed
    result["gaps"] = str(answer.get("gaps") or "").strip()
    result["answered"] = bool(answer.get("answerable")) and bool(findings)
    if answer.get("answerable") and not findings:
        result["note"] = "The model said it could answer, but none of its findings had a valid citation, so they were removed."
    return result


# ---------------------------------------------------------------- output

def to_markdown(result):
    lines = [f"## {result['question']}", ""]
    if result["answered"]:
        for f in result["findings"]:
            cites = ", ".join(f"[{c}]" for c in f["citations"])
            lines.append(f"- {f['statement']} {cites}")
        if result["gaps"]:
            lines += ["", f"**Not covered by these papers.** {result['gaps']}"]
    else:
        lines.append(NOT_ANSWERED)
        if result["gaps"]:
            lines += ["", result["gaps"]]
    if result["note"]:
        lines += ["", f"_{result['note']}_"]

    cited = {c for f in result["findings"] for c in f["citations"]}
    shown = [s for s in result["sources"] if s["id"] in cited] if result["answered"] else result["sources"]
    if shown:
        lines += ["", "**Sources**" if result["answered"] else "**Papers that were retrieved**"]
        for s in shown:
            lines.append(f"- [{s['id']}] {s['title']} ({s['published']}) {s['url']}")
    if result["removed_citations"]:
        lines += ["", f"_Removed {len(result['removed_citations'])} citation(s) that didn't match a retrieved paper._"]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=8, help="chunks to retrieve before grouping by paper")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = parser.parse_args()

    from retrieval import build_vector_store, load_chunks, search

    collection, embedder = build_vector_store(load_chunks())
    result = summarize(args.question, search(args.question, collection, embedder, top_k=args.top_k), model=args.model)
    print(json.dumps(result, indent=2) if args.json else to_markdown(result))
