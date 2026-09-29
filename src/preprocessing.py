import json
import re
from pathlib import Path

from ingestion import fetch_arxiv_papers


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
        abstract = clean_text(paper["abstract"])

        if not abstract:
            continue

        chunks = chunk_text(abstract)

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


def save_processed_data(data, output_path="data/processed/arxiv_chunks.jsonl"):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for record in data:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    papers = fetch_arxiv_papers(max_results=100)

    chunks = preprocess_papers(papers)

    save_processed_data(chunks)

    print(f"Fetched {len(papers)} papers")
    print(f"Created {len(chunks)} chunks")
    print("Saved to data/processed/arxiv_chunks.jsonl")
