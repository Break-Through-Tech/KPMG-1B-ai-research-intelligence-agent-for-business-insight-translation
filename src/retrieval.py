import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


DATA_PATH = Path("data/processed/arxiv_chunks.jsonl")
CHROMA_PATH = "data/processed/chroma_db"
COLLECTION_NAME = "arxiv_research"


def load_chunks():
    chunks = []

    with DATA_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            chunks.append(json.loads(line))

    return chunks


def build_vector_store(chunks):
    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

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


def search(query, collection, model, top_k=5):
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    return results


if __name__ == "__main__":
    chunks = load_chunks()

    print(f"Loaded {len(chunks)} chunks")

    collection, model = build_vector_store(chunks)

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
