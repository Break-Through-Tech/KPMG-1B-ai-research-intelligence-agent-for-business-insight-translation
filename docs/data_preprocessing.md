# Data Preprocessing

## Data Source

The project uses AI research papers from arXiv. Papers are collected from the `cs.AI` category using the Python `arxiv` library.

## Data Ingestion

The ingestion pipeline is implemented in `src/ingestion.py`.

For each paper, we collect:

- Title
- Authors
- Abstract
- Published date
- Updated date
- Categories
- Primary category
- PDF URL
- arXiv entry ID

## Preprocessing

The preprocessing pipeline is implemented in `src/preprocessing.py`.

The main preprocessing steps are:

1. Remove unnecessary whitespace and line breaks from titles and abstracts.
2. Skip papers with empty abstracts.
3. Split abstracts into smaller text chunks.
4. Use overlapping chunks so some context is preserved between sections.
5. Keep the original paper metadata with every chunk.

The current chunk size is 200 words with a 40-word overlap.

## Output

The processed records are saved as:

`data/processed/arxiv_chunks.jsonl`

In the current test, 100 arXiv papers produced 146 text chunks.

The processed chunks will be used later for embeddings and retrieval in the RAG pipeline.
