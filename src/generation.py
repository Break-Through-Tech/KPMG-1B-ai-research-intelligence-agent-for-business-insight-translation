"""
Grounded summarization with citations.

Takes the papers retrieved for a question and asks Gemini to summarize what
they say, citing the arXiv ID behind every finding. Every citation is checked
against the papers that were actually retrieved. A finding with no valid
citation is dropped, and when the papers don't answer the question the summary
says so instead of guessing.

For the study dataset, neighboring chunks around each retrieved passage are
also included so the generation model has enough local context.

Run from the repo root, after preprocessing has written the chunks:

    python src/generation.py "How can language models reduce computational cost?"
    python src/generation.py "..." --top-k 3 --json

Needs GEMINI_API_KEY in .env.
GEMINI_MODEL picks the model.
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
RETRYABLE = {429, 500, 503}


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
                    "citations": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
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
    Turn raw retrieval results into one entry per paper, in rank order.

    Multiple chunks from the same paper are merged into the same source so
    neighboring passages can provide more context without creating duplicate
    citations.
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
    """Build the grounded prompt sent to Gemini."""
    blocks = []

    for source in sources:
        body = " ".join(source["texts"])

        blocks.append(
            f"[{source['id']}] "
            f"{source['title']} "
            f"(published {source['published']})\n"
            f"{body}"
        )

    return (
        f"Question: {question}\n\n"
        f"Sources ({len(sources)} papers):\n\n"
        + "\n\n".join(blocks)
        + "\n\n"
        "Summarize what these sources say that answers the question, "
        "following the rules."
    )


def expand_neighbor_context(results, chunks, window=1):
    """
    Add neighboring chunks around each retrieved passage.

    Retrieval still determines which distinct papers are selected.
    This function only expands the local context around the best passage
    from each selected paper.

    window=1 means:
        previous chunk
        retrieved chunk
        next chunk
    """
    if not results or not results.get("documents") or not results["documents"][0]:
        return results

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = (results.get("distances") or [[None] * len(documents)])[0]

    expanded_documents = []
    expanded_metadatas = []
    expanded_distances = []

    seen = set()

    for index, (document, metadata) in enumerate(zip(documents, metadatas)):
        paper_id = metadata.get("paper_id")
        retrieved_chunk_id = metadata.get("chunk_id")

        distance = (
            distances[index]
            if index < len(distances)
            else None
        )

        try:
            retrieved_chunk_id = int(retrieved_chunk_id)
        except (TypeError, ValueError):
            retrieved_chunk_id = None

        neighbors = []

        if retrieved_chunk_id is not None:
            for chunk in chunks:
                if chunk.get("paper_id") != paper_id:
                    continue

                try:
                    candidate_chunk_id = int(chunk.get("chunk_id"))
                except (TypeError, ValueError):
                    continue

                if abs(candidate_chunk_id - retrieved_chunk_id) <= window:
                    neighbors.append(chunk)

            neighbors.sort(key=lambda chunk: int(chunk["chunk_id"]))

        # If neighboring chunks cannot be found, keep the original result.
        if not neighbors:
            fallback = dict(metadata)
            fallback["text"] = document
            neighbors = [fallback]

        for chunk in neighbors:
            chunk_id = chunk.get("chunk_id")

            key = (paper_id, chunk_id)

            if key in seen:
                continue

            seen.add(key)

            expanded_documents.append(
                chunk.get("text", document)
            )

            expanded_metadatas.append({
                "paper_id": chunk.get(
                    "paper_id",
                    paper_id,
                ),
                "title": chunk.get(
                    "title",
                    metadata.get("title", ""),
                ),
                "published": chunk.get(
                    "published",
                    metadata.get("published", ""),
                ),
                "pdf_url": chunk.get(
                    "pdf_url",
                    metadata.get("pdf_url", ""),
                ),
                "chunk_id": chunk_id,
            })

            expanded_distances.append(distance)

    return {
        "documents": [expanded_documents],
        "metadatas": [expanded_metadatas],
        "distances": [expanded_distances],
    }


# ---------------------------------------------------------------- the model

def call_gemini(
    prompt,
    model=DEFAULT_MODEL,
    client=None,
    retries=3,
    wait_s=5.0,
):
    """Ask Gemini for a JSON answer matching RESPONSE_SCHEMA."""

    from google import genai
    from google.genai import errors, types

    if client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "Set GEMINI_API_KEY in .env. "
                "Get a key at https://aistudio.google.com/apikey"
            )

        client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_json_schema=RESPONSE_SCHEMA,
        temperature=0.2,
    )

    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )

            return response.text

        except errors.APIError as err:
            if (
                getattr(err, "code", None) not in RETRYABLE
                or attempt == retries
            ):
                raise

            delay = wait_s * (2 ** attempt)

            print(
                f"Gemini returned {err.code}, "
                f"retrying in {delay:.0f}s",
                file=sys.stderr,
            )

            time.sleep(delay)


def parse_response(text):
    """Parse Gemini JSON, tolerating a stray Markdown code fence."""
    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        (text or "").strip(),
    )

    return json.loads(cleaned)


# ---------------------------------------------------------------- checking

def check_citations(answer, sources):
    """
    Keep only citations pointing to retrieved papers.

    Findings without at least one valid retrieved-paper citation are dropped.
    """
    valid = {source["id"] for source in sources}

    findings = []
    removed = []

    for finding in answer.get("findings") or []:
        statement = re.sub(
            r"\s*\[[^\]]*\]",
            "",
            str(finding.get("statement", "")),
        ).strip()

        kept = []

        for citation in finding.get("citations") or []:
            citation_id = arxiv_id(
                str(citation).strip("[] ")
            )

            if citation_id in valid and citation_id not in kept:
                kept.append(citation_id)

            elif citation_id not in valid:
                removed.append(str(citation))

        if statement and kept:
            findings.append({
                "statement": statement,
                "citations": kept,
            })

    return findings, removed


def summarize(
    question,
    results,
    llm=None,
    model=DEFAULT_MODEL,
):
    """
    Generate a grounded summary from retrieved research passages.

    Tests can replace `llm` with a fake function.
    """
    sources = collect_sources(results)

    result = {
        "question": question,
        "model": model,
        "answered": False,
        "findings": [],
        "gaps": "",
        "sources": [
            {
                key: value
                for key, value in source.items()
                if key != "texts"
            }
            for source in sources
        ],
        "removed_citations": [],
        "note": "",
    }

    if not sources:
        result["note"] = (
            "No papers were retrieved for this question."
        )
        return result

    llm = llm or (
        lambda prompt: call_gemini(
            prompt,
            model=model,
        )
    )

    try:
        answer = parse_response(
            llm(
                build_prompt(
                    question,
                    sources,
                )
            )
        )

    except (json.JSONDecodeError, TypeError):
        result["note"] = (
            "The model's response couldn't be read, "
            "so no summary was produced."
        )
        return result

    findings, removed = check_citations(
        answer,
        sources,
    )

    result["findings"] = findings
    result["removed_citations"] = removed
    result["gaps"] = str(
        answer.get("gaps") or ""
    ).strip()

    result["answered"] = (
        bool(answer.get("answerable"))
        and bool(findings)
    )

    if answer.get("answerable") and not findings:
        result["note"] = (
            "The model said it could answer, but none "
            "of its findings had a valid citation, "
            "so they were removed."
        )

    return result


# ---------------------------------------------------------------- output

def to_markdown(result):
    """Convert a generated result into readable Markdown."""
    lines = [
        f"## {result['question']}",
        "",
    ]

    if result["answered"]:
        for finding in result["findings"]:
            cites = ", ".join(
                f"[{citation}]"
                for citation in finding["citations"]
            )

            lines.append(
                f"- {finding['statement']} {cites}"
            )

        if result["gaps"]:
            lines += [
                "",
                (
                    "**Not covered by these papers.** "
                    f"{result['gaps']}"
                ),
            ]

    else:
        lines.append(NOT_ANSWERED)

        if result["gaps"]:
            lines += [
                "",
                result["gaps"],
            ]

    if result["note"]:
        lines += [
            "",
            f"_{result['note']}_",
        ]

    cited = {
        citation
        for finding in result["findings"]
        for citation in finding["citations"]
    }

    if result["answered"]:
        shown = [
            source
            for source in result["sources"]
            if source["id"] in cited
        ]
    else:
        shown = result["sources"]

    if shown:
        lines += [
            "",
            (
                "**Sources**"
                if result["answered"]
                else "**Papers that were retrieved**"
            ),
        ]

        for source in shown:
            lines.append(
                f"- [{source['id']}] "
                f"{source['title']} "
                f"({source['published']}) "
                f"{source['url']}"
            )

    if result["removed_citations"]:
        lines += [
            "",
            (
                f"_Removed "
                f"{len(result['removed_citations'])} "
                "citation(s) that didn't match "
                "a retrieved paper._"
            ),
        ]

    return "\n".join(lines)


# ------------------------------------------- CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "question",
    )

    parser.add_argument(
        "--dataset",
        choices=["studies", "arxiv"],
        default="studies",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="distinct papers to retrieve",
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="print the full result as JSON",
    )

    args = parser.parse_args()

    from retrieval import (
        build_vector_store,
        load_chunks,
        search,
    )

    chunks = load_chunks(args.dataset)

    collection, embedder = build_vector_store(
        chunks,
        args.dataset,
    )

    retrieved = search(
        args.question,
        collection,
        embedder,
        top_k=args.top_k,
    )

    context = expand_neighbor_context(
        retrieved,
        chunks,
        window=1,
    )

    result = summarize(
        args.question,
        context,
        model=args.model,
    )

    print(
        json.dumps(result, indent=2)
        if args.json
        else to_markdown(result)
    )
