# Baseline RAG Retrieval Evaluation

## Retrieval Setup

The baseline retrieval pipeline uses processed arXiv abstract chunks from the preprocessing pipeline.

Each text chunk is converted into an embedding using the `all-MiniLM-L6-v2` Sentence Transformer model. The embeddings are stored and searched using ChromaDB.

For each user query, the system retrieves the top 5 most similar chunks.

## Evaluation

Five benchmark questions were created with an expected relevant research paper for each query.

The baseline was evaluated using:

- Recall@5: whether the expected paper appeared in the top 5 results
- Mean Reciprocal Rank (MRR): how highly the expected paper was ranked

## Results

- Benchmark queries: 5
- Queries with expected paper in top 5: 5
- Recall@5: 1.00
- MRR: 0.90

Four benchmark questions returned the expected paper at rank 1. One returned the expected paper at rank 2.

## Current Limitations

The benchmark set is small and was created using papers already known to be in the dataset, so the results mainly confirm that the baseline retrieval pipeline is working correctly.

The system currently retrieves individual chunks, so multiple chunks from the same paper may appear in the top results.

Future evaluation should include more diverse and business-focused queries.
