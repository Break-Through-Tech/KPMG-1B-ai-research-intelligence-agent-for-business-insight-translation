"""Small checks for the five-study retrieval changes."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

from generation import summarize
from retrieval import search


class Model:
    def encode(self, query, normalize_embeddings):
        return self

    def tolist(self):
        return [1.0, 0.0]


class Collection:
    def __init__(self, paper_ids):
        self.paper_ids = paper_ids

    def count(self):
        return len(self.paper_ids)

    def query(self, query_embeddings, n_results):
        assert n_results == self.count()
        return {
            "ids": [[f"chunk-{i}" for i in range(n_results)]],
            "documents": [[f"Passage {i}" for i in range(n_results)]],
            "metadatas": [[{"paper_id": pid, "title": pid} for pid in self.paper_ids]],
            "distances": [[i / 10 for i in range(n_results)]],
        }

    def get(self, include):
        return {"metadatas": [{"title": pid} for pid in self.paper_ids]}


def test_duplicate_passages_do_not_take_other_papers_slots():
    results = search("question", Collection(["a", "a", "b", "c"]), Model())
    assert [m["paper_id"] for m in results["metadatas"][0]] == ["a", "b", "c"]
    assert results["documents"][0] == ["Passage 0", "Passage 2", "Passage 3"]
    assert results["distances"][0] == [0.0, 0.2, 0.3]


def test_small_and_empty_indexes_return_only_available_papers():
    assert search("question", Collection([]), Model())["documents"] == [[]]
    results = search("question", Collection(["a", "a"]), Model(), top_k=5)
    assert len(results["documents"][0]) == 1
    with pytest.raises(ValueError):
        search("question", Collection(["a"]), Model(), top_k=0)


def test_retrieved_passages_can_be_summarized_with_citations():
    results = search("question", Collection(["a", "a", "b"]), Model())

    def llm(prompt):
        assert "Passage 0" in prompt and "Passage 2" in prompt
        assert "Passage 1" not in prompt
        return json.dumps({
            "answerable": True,
            "findings": [{"statement": "A supported summary.", "citations": ["a"]}],
            "gaps": "",
        })

    assert summarize("question", results, llm=llm)["answered"] is True


def test_evaluation_rejects_expected_studies_missing_from_the_index():
    from evaluation import evaluate_retrieval

    with pytest.raises(ValueError, match="Expected study missing"):
        evaluate_retrieval(Collection(["Unrelated study"]), Model())


def test_dataset_selection_keeps_processed_inputs_separate(tmp_path, monkeypatch):
    from retrieval import load_chunks

    monkeypatch.chdir(tmp_path)
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    (processed / "study_chunks.jsonl").write_text('{"paper_id": "supplied"}\n')
    (processed / "arxiv_chunks.jsonl").write_text('{"paper_id": "exploration"}\n')

    assert load_chunks() == [{"paper_id": "supplied"}]
    assert load_chunks("arxiv") == [{"paper_id": "exploration"}]
    with pytest.raises(ValueError, match="dataset"):
        load_chunks("unknown")


def test_dataset_selection_uses_separate_vector_collections(monkeypatch):
    import retrieval

    names = []

    class Store:
        def get(self):
            return {"ids": []}

        def upsert(self, **kwargs):
            pass

    class Client:
        def get_or_create_collection(self, name):
            names.append(name)
            return Store()

    monkeypatch.setattr(retrieval.chromadb, "PersistentClient", lambda **kwargs: Client())
    monkeypatch.setattr(retrieval, "SentenceTransformer", lambda name: Model())
    chunk = {"paper_id": "a", "text": "Passage", "title": "Study", "published": "",
             "categories": [], "pdf_url": "", "chunk_id": 0}

    retrieval.build_vector_store([chunk])
    retrieval.build_vector_store([chunk], "arxiv")
    assert names == ["assigned_studies", "arxiv_research"]
