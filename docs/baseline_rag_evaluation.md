# Baseline RAG Retrieval Evaluation

## Retrieval Setup

The Milestone 1 baseline used processed arXiv abstract chunks. The current Task 2 pipeline uses text extracted from the five supplied PDF studies in `data/`.

Each text chunk is converted into an embedding using the `all-MiniLM-L6-v2` Sentence Transformer model. The embeddings are stored and searched using ChromaDB.

For each user query, the system returns the top 3 distinct papers, keeping the best matching passage from each paper. It searches all chunks because the current scope contains only five studies.

The five-study index is stored in a separate `assigned_studies` collection. It is rebuilt from `data/processed/study_chunks.jsonl` so previously downloaded papers are not included.

## Retrieval Improvements

Multiple passages from the same paper no longer take up separate result slots.

The retrieved passages can be passed directly to the existing `src/generation.py` summarizer, which produces findings with source citations. This task uses the existing summarizer rather than introducing a new generation system.

## Evaluation

The benchmark now contains 15 questions: one technical question and two business-focused questions for each of the five supplied studies. Topics include AI cost control, research investment, workflow documentation, transport planning, and patient-facing explanations.

Retrieval is evaluated using:

- Recall@3: whether the expected paper appeared in the top 3 results
- Top-1 accuracy: whether the expected paper was the first result
- Mean Reciprocal Rank (MRR): how highly the expected paper was ranked

Each question has one expected study. Recall@3 therefore measures whether that labeled study was found; it does not measure whether every returned paper is relevant. Top 3 is used because returning all five studies would make Recall@5 uninformative.

The evaluator checks that the expected studies are present before calculating results.

## Results

### Milestone 1 Baseline

These results are retained from the original abstract dataset and five original questions:

- Benchmark queries: 5
- Queries with expected paper in top 5: 5
- Recall@5: 1.00
- MRR: 0.90

Four benchmark questions returned the expected paper at rank 1. One returned the expected paper at rank 2.

### Task 2 Retrieval Check

The current run uses five supplied studies and 336 PDF text chunks:

- Benchmark queries: 15
- Business-focused queries: 10
- Queries with expected paper in top 3: 15
- Recall@3: 1.00
- Top-1 accuracy: 1.00
- MRR: 1.00

All 15 questions returned the expected study at rank 1. These results are not a before/after accuracy comparison with Milestone 1 because the source material and questions changed.

## Running the Pipeline

```bash
python src/preprocessing.py
python src/evaluation.py
python src/generation.py "How can a company choose between cheaper and more capable AI models while controlling cost?"
```

Generation requires `GEMINI_API_KEY` in `.env`. Retrieval evaluation does not require a Gemini API key.

The optional `--dataset arxiv` mode is available in preprocessing, retrieval, and generation for 100-paper exploration. This evaluation script remains specific to the five supplied studies; its benchmark and reported scores do not evaluate the exploration dataset.

```bash
python -m pytest tests -q
```

The summarization tests use a fake model; the retrieval evaluation used the actual embedding model and ChromaDB. Dataset-selection tests check that the supplied studies and arXiv exploration use separate input files and vector collections.

## Current Limitations

The benchmark is larger and includes business-focused wording, but questions are still based on five known studies. The results confirm retrieval within this limited scope, not performance on unfamiliar research or independently collected user questions.

Only the best matching passage from each paper is supplied to the summarizer. Other passages may be needed to answer broader questions fully.

Retrieval always returns the closest papers, even for an unrelated question. The existing summarizer is prompted to report insufficient evidence, but this retrieval check does not test that behavior with real model outputs.

Citation checks confirm that the cited paper was retrieved, not that it supports every generated claim. Summary accuracy, completeness, and business translation remain later tasks.
