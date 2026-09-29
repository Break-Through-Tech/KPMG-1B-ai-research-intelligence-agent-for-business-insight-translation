import arxiv


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
    papers = fetch_arxiv_papers(max_results=10)

    print(f"Fetched {len(papers)} papers")

    for paper in papers[:3]:
        print("\nTitle:", paper["title"])
        print("Published:", paper["published"])
        print("Categories:", paper["categories"])
