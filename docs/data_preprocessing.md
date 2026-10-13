# Data Preprocessing

## Data Source

The current pipeline uses only the five supplied arXiv PDF studies in `data/`:

- Pandora's AI Model Routing Box (`2608.20316v1`)
- AI4AI-Bench (`2608.20318v1`)
- Inducing Task Models from Computer-Use Traces (`2608.20319v1`)
- An Agentic Approach for Active Data Collection, Travel Behavior Modeling, and Weather-Sensitive Demand Prediction (`2608.20320v1`)
- G-CARL (`2608.20331v1`)

This is the default dataset. An optional `--dataset arxiv` mode downloads up to 100 recent arXiv papers for exploration.

## Data Ingestion

The ingestion pipeline is implemented in `src/ingestion.py`.

The `load_local_papers()` function uses `pypdf` to read each PDF. For each paper, we keep:

- Title
- Authors
- Extracted PDF text
- PDF URL
- arXiv entry ID

Titles and authors come from the PDF metadata. Source IDs come from the filenames. Published dates and categories are left empty because this loader does not fetch arXiv metadata. The optional arXiv mode uses `fetch_arxiv_papers()` and the earlier abstract preprocessing approach.

## Preprocessing

The preprocessing pipeline is implemented in `src/preprocessing.py`.

The main preprocessing steps are:

1. Remove unnecessary whitespace and line breaks from titles and extracted text.
2. Stop if a supplied PDF has no extractable text.
3. Split the extracted text into smaller text chunks.
4. Use overlapping chunks so some context is preserved between sections.
5. Keep the original paper metadata with every chunk.

The current chunk size is 200 words with a 40-word overlap.

## Output

The processed records are saved as:

`data/processed/study_chunks.jsonl`

In the current run, the five supplied studies produced 336 text chunks.

The processed chunks are used for embeddings, retrieval, and summarization. This file is separate from the earlier downloaded abstract dataset.

## Running the Pipeline

```bash
python src/preprocessing.py
```

To explore up to 100 recent papers instead:

```bash
python src/preprocessing.py --dataset arxiv
python src/retrieval.py --dataset arxiv
```

This mode needs internet access to arXiv and saves abstract chunks to `data/processed/arxiv_chunks.jsonl`. It uses a separate `arxiv_research` collection. The five-study data and collection stay separate. Rerunning this download can change the exploration papers.

## Current Limitations

PDF extraction can lose layout, equation, and table information. References and appendix text are included. The pipeline does not use OCR for scanned pages.
