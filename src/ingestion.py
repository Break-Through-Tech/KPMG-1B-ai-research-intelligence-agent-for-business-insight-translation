from pathlib import Path

import arxiv
from pypdf import PdfReader


def load_local_papers(data_path="data"):
    """Read the five supplied studies without downloading more papers."""
    paths = sorted(Path(data_path).glob("*.pdf"))

    if len(paths) != 5:
        raise ValueError("Expected the five supplied PDF studies in data/.")

    papers = []

    for path in paths:
        reader = PdfReader(path)
        metadata = reader.metadata or {}
        paper_id = path.name.split("_", 1)[0]
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        if not text.strip():
            raise ValueError(f"No text could be extracted from {path.name}")

        papers.append(
            {
                "title": metadata.get("/Title") or path.stem,
                "authors": (metadata.get("/Author") or "").split("; "),
                "text": text,
                "published": "",
                "categories": [],
                "pdf_url": f"https://arxiv.org/pdf/{paper_id}",
                "entry_id": f"https://arxiv.org/abs/{paper_id}",
            }
        )

    return papers


def fetch_arxiv_papers(max_results=100, max_results_per_query=25):
    """Fetch recent arXiv papers across business-relevant AI research topics."""

    queries = [
        '"LLM routing" OR "model routing"',
        '"inference cost" OR "inference efficiency"',
        '"AI agents" OR "agentic AI"',
        '"retrieval augmented generation" OR RAG',
        '"AI evaluation" OR "LLM evaluation"',
        '"workflow automation" OR "task automation"',
        '"enterprise AI" OR "business AI"',
    ]

    client = arxiv.Client()
    papers_by_id = {}

    for query in queries:
        search = arxiv.Search(
            query=query,
            max_results=max_results_per_query,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

        for paper in client.results(search):
            paper_id = paper.entry_id

            # Skip duplicate papers returned by multiple searches.
            if paper_id in papers_by_id:
                continue

            papers_by_id[paper_id] = {
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "abstract": paper.summary,
                "published": paper.published.isoformat(),
                "updated": paper.updated.isoformat(),
                "categories": paper.categories,
                "primary_category": paper.primary_category,
                "pdf_url": paper.pdf_url,
                "entry_id": paper.entry_id,
            }

            # Keep compatibility with preprocessing.py's max_results=100.
            if len(papers_by_id) >= max_results:
                return list(papers_by_id.values())

    return list(papers_by_id.values())


if __name__ == "__main__":
    papers = load_local_papers()

    print(f"Loaded {len(papers)} supplied studies")

    for paper in papers[:3]:
        print("\nTitle:", paper["title"])
        print("PDF:", paper["pdf_url"])
