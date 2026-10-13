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

        # Keep the PDF title and source ID so retrieved passages remain traceable.
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


def fetch_arxiv_papers(query="cat:cs.AI", max_results=100):
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    client = arxiv.Client()
    papers = []

    for paper in client.results(search):
        papers.append(
            {
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
        )

    return papers


if __name__ == "__main__":
    papers = load_local_papers()

    print(f"Loaded {len(papers)} supplied studies")

    for paper in papers[:3]:
        print("\nTitle:", paper["title"])
        print("PDF:", paper["pdf_url"])
