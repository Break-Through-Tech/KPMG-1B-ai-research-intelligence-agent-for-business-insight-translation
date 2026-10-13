import argparse
import json
import re
from pathlib import Path

from ingestion import fetch_arxiv_papers, load_local_papers


def clean_text(text):
    """Remove extra spaces and line breaks."""
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text, chunk_size=200, overlap=40):
    """Split text into overlapping word chunks."""
    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap

    return chunks


def preprocess_papers(papers):
    processed_chunks = []

    for paper in papers:
        title = clean_text(paper["title"])
        # Local studies use PDF text; abstract records still work if supplied.
        text = clean_text(paper.get("text", paper.get("abstract", "")))

        if not text:
            continue

        chunks = chunk_text(text)

        for index, chunk in enumerate(chunks):
            processed_chunks.append(
                {
                    "paper_id": paper["entry_id"],
                    "title": title,
                    "authors": paper["authors"],
                    "published": paper["published"],
                    "categories": paper["categories"],
                    "pdf_url": paper["pdf_url"],
                    "chunk_id": index,
                    "text": chunk,
                }
            )

    return processed_chunks


def save_processed_data(data, output_path="data/processed/study_chunks.jsonl"):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for record in data:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare the selected study dataset.")
    parser.add_argument("--dataset", choices=["studies", "arxiv"], default="studies")
    args = parser.parse_args()

    # Keep the five-study deliverable as the default; arXiv exploration is optional.
    if args.dataset == "arxiv":
        papers = fetch_arxiv_papers(max_results=100)
        output_path = "data/processed/arxiv_chunks.jsonl"
    else:
        papers = load_local_papers()
        output_path = "data/processed/study_chunks.jsonl"

    chunks = preprocess_papers(papers)

    save_processed_data(chunks, output_path)

    print(f"Loaded {len(papers)} papers from {args.dataset}")
    print(f"Created {len(chunks)} chunks")
    print(f"Saved to {output_path}")
