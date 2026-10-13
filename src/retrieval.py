import argparse
import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


DATA_PATH = Path("data/processed/study_chunks.jsonl")
CHROMA_PATH = "data/processed/chroma_db"
COLLECTION_NAME = "assigned_studies"


def load_chunks(dataset="studies"):
    chunks = []
    if dataset not in ("studies", "arxiv"):
        raise ValueError("dataset must be 'studies' or 'arxiv'")

    data_path = DATA_PATH
    if dataset == "arxiv":
        data_path = Path("data/processed/arxiv_chunks.jsonl")

    with data_path.open("r", encoding="utf-8") as file:
        for line in file:
            chunks.append(json.loads(line))

    return chunks


def build_vector_store(chunks, dataset="studies"):
    if dataset not in ("studies", "arxiv"):
        raise ValueError("dataset must be 'studies' or 'arxiv'")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Separate collections prevent exploration papers from entering the five-study demo.
    collection_name = COLLECTION_NAME if dataset == "studies" else "arxiv_research"
    collection = client.get_or_create_collection(name=collection_name)

    # Rebuild only the selected collection so old passages are not left in it.
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True
    ).tolist()

    ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        ids.append(f"chunk-{i}")

        metadatas.append(
            {
                "paper_id": chunk["paper_id"],
                "title": chunk["title"],
                "published": chunk["published"],
                "categories": ", ".join(chunk["categories"]),
                "pdf_url": chunk["pdf_url"],
                "chunk_id": chunk["chunk_id"],
            }
        )

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return collection, model


def search(query, collection, model, top_k=3):
    """Return the best matching passage from each of the top papers."""
    if top_k < 1:
        raise ValueError("top_k must be positive")

    paper_results = {
        "ids": [[]],
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }

    chunk_count = collection.count()
    if chunk_count == 0:
        return paper_results

    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        # These small exploration datasets can be searched before removing duplicates.
        n_results=chunk_count,
    )

    seen_papers = set()

    for index, metadata in enumerate(results["metadatas"][0]):
        paper_id = metadata["paper_id"]

        # Results are ranked, so the first match is the paper's best passage.
        if paper_id in seen_papers:
            continue

        seen_papers.add(paper_id)
        for key in paper_results:
            paper_results[key][0].append(results[key][0][index])

        if len(seen_papers) == top_k:
            break

    return paper_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve papers from the selected dataset.")
    parser.add_argument("--dataset", choices=["studies", "arxiv"], default="studies")
    args = parser.parse_args()

    chunks = load_chunks(args.dataset)

    print(f"Loaded {len(chunks)} chunks")

    collection, model = build_vector_store(chunks, args.dataset)

    query = "How can language models reduce computational cost?"

    results = search(query, collection, model)

    print(f"\nQuestion: {query}\n")

    for i in range(len(results["documents"][0])):
        metadata = results["metadatas"][0][i]

        print(f"Result {i + 1}")
        print("Title:", metadata["title"])
        print("Categories:", metadata["categories"])
        print("PDF:", metadata["pdf_url"])
        print("Text:", results["documents"][0][i][:300])
        print("-" * 80)
