from retrieval import load_chunks, build_vector_store, search


BENCHMARKS = [
    {
        "query": "How can language models operate under different compute budgets?",
        "expected_title": "Telescopic Language Models",
    },
    {
        "query": "How can we predict token usage during LLM agent execution?",
        "expected_title": "TokenCast: Forecasting Token Consumption During LLM Agent Execution",
    },
    {
        "query": "How can financial research agents be evaluated automatically?",
        "expected_title": "FinAutoRubric: Expert-Guided Automatic Rubric Generation for Evaluating Financial Research Agents",
    },
    {
        "query": "How can tool-using language models report failures more clearly?",
        "expected_title": "Failure-Transparent Agents: Benchmarking Post-Failure Reporting in Tool-Using Language Models",
    },
    {
        "query": "How can generative AI cause information or perspective diversity to decrease?",
        "expected_title": "Narrowing the Horizon: Quantifying Topic Saliency Shifts in Generative Monoculture",
    },
]


def evaluate_retrieval(collection, model, top_k=5):
    hits = 0
    reciprocal_ranks = []

    for benchmark in BENCHMARKS:
        results = search(
            benchmark["query"],
            collection,
            model,
            top_k=top_k,
        )

        titles = [
            metadata["title"]
            for metadata in results["metadatas"][0]
        ]

        rank = None

        for index, title in enumerate(titles, start=1):
            if title == benchmark["expected_title"]:
                rank = index
                break

        if rank is not None:
            hits += 1
            reciprocal_ranks.append(1 / rank)
            status = f"FOUND at rank {rank}"
        else:
            reciprocal_ranks.append(0)
            status = "NOT FOUND"

        print("\nQuestion:", benchmark["query"])
        print("Expected:", benchmark["expected_title"])
        print("Result:", status)

        print("Top results:")
        for index, title in enumerate(titles, start=1):
            print(f"  {index}. {title}")

    recall_at_5 = hits / len(BENCHMARKS)
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)

    print("\n" + "=" * 60)
    print(f"Recall@{top_k}: {recall_at_5:.2f}")
    print(f"MRR: {mrr:.2f}")
    print(f"Queries passed: {hits}/{len(BENCHMARKS)}")


if __name__ == "__main__":
    chunks = load_chunks()

    print(f"Loaded {len(chunks)} chunks")

    collection, model = build_vector_store(chunks)

    evaluate_retrieval(collection, model)
