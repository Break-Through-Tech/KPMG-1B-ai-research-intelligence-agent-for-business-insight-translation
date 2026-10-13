from retrieval import load_chunks, build_vector_store, search


# Three questions per study: one technical and two business-focused.
BENCHMARKS = [
    {
        "query": "How can value-of-information estimates improve routing between AI models?",
        "expected_title": "Pandora's AI Model Routing Box: Efficient Allocation with Costly Value Estimation",
    },
    {
        "query": "How can a company choose between cheaper and more capable AI models while controlling cost?",
        "expected_title": "Pandora's AI Model Routing Box: Efficient Allocation with Costly Value Estimation",
    },
    {
        "query": "When is it worth paying for a more accurate estimate before choosing an AI model?",
        "expected_title": "Pandora's AI Model Routing Box: Efficient Allocation with Costly Value Estimation",
    },
    {
        "query": "How can we benchmark an AI agent's ability to improve model training algorithms?",
        "expected_title": "AI4AI-Bench: Benchmarking LLM Agents in Algorithmic Design for Recursive Self-Improvement",
    },
    {
        "query": "How can an AI research team measure whether coding agents improve training beyond parameter tuning?",
        "expected_title": "AI4AI-Bench: Benchmarking LLM Agents in Algorithmic Design for Recursive Self-Improvement",
    },
    {
        "query": "What evidence should a team examine before investing in AI systems that improve their own training methods?",
        "expected_title": "AI4AI-Bench: Benchmarking LLM Agents in Algorithmic Design for Recursive Self-Improvement",
    },
    {
        "query": "How can interleaved computer-use traces be converted into hierarchical task and procedure models?",
        "expected_title": "Inducing Task Models from Computer-Use Traces",
    },
    {
        "query": "How can an organization turn recorded computer activity into reusable workflow documentation?",
        "expected_title": "Inducing Task Models from Computer-Use Traces",
    },
    {
        "query": "How can a company audit how employees or AI agents carry out several overlapping computer tasks?",
        "expected_title": "Inducing Task Models from Computer-Use Traces",
    },
    {
        "query": "How can conversational surveys and weather context support travel-mode prediction?",
        "expected_title": "An Agentic Approach for Active Data Collection, Travel Behavior Modeling, and Weather-Sensitive Demand Prediction",
    },
    {
        "query": "How can a transport planning team use chatbots to collect commuter preferences and study weather-related demand?",
        "expected_title": "An Agentic Approach for Active Data Collection, Travel Behavior Modeling, and Weather-Sensitive Demand Prediction",
    },
    {
        "query": "What evidence and sample limitations should planners consider before using AI to predict travel choices in bad weather?",
        "expected_title": "An Agentic Approach for Active Data Collection, Travel Behavior Modeling, and Weather-Sensitive Demand Prediction",
    },
    {
        "query": "How can retrieved evidence and weighted checklists improve medical report interpretation?",
        "expected_title": "G-CARL: Grounded Checklist-Aligned Reward Learning for Patient-Oriented Medical Report Interpretation",
    },
    {
        "query": "How can a healthcare organization assess whether AI explanations of medical reports are accurate and understandable to patients?",
        "expected_title": "G-CARL: Grounded Checklist-Aligned Reward Learning for Patient-Oriented Medical Report Interpretation",
    },
    {
        "query": "How can an AI report explanation be checked for factual support and coverage of a patient's questions?",
        "expected_title": "G-CARL: Grounded Checklist-Aligned Reward Learning for Patient-Oriented Medical Report Interpretation",
    },
]


def evaluate_retrieval(collection, model, top_k=3):
    # A benchmark only makes sense when its expected studies are in the index.
    stored_metadata = collection.get(include=["metadatas"])["metadatas"]
    available_titles = {metadata["title"] for metadata in stored_metadata}
    for benchmark in BENCHMARKS:
        if benchmark["expected_title"] not in available_titles:
            raise ValueError(f"Expected study missing: {benchmark['expected_title']}")

    hits = 0
    first_place_hits = 0
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
            if rank == 1:
                first_place_hits += 1
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

    recall_at_k = hits / len(BENCHMARKS)
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)

    print("\n" + "=" * 60)
    print(f"Recall@{top_k}: {recall_at_k:.2f}")
    print(f"Top-1 accuracy: {first_place_hits / len(BENCHMARKS):.2f}")
    print(f"MRR: {mrr:.2f}")
    print(f"Queries passed: {hits}/{len(BENCHMARKS)}")

    return {
        "recall_at_k": recall_at_k,
        "top_1_accuracy": first_place_hits / len(BENCHMARKS),
        "mrr": mrr,
    }


if __name__ == "__main__":
    chunks = load_chunks()

    print(f"Loaded {len(chunks)} chunks")

    collection, model = build_vector_store(chunks)

    evaluate_retrieval(collection, model)
