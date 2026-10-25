# AI Research Intelligence Agent for Business Insight Translation

**KPMG × Break Through Tech AI Studio | Fall 2026**

AI research moves fast, but turning a technical paper into something useful for a business team takes time. A paper might introduce a new model-routing strategy, agent framework, or optimization technique, but the business question is usually much simpler: **Why does this matter, and how could we use it?**

That is the problem our team worked on.

We built a retrieval-augmented generation (RAG) pipeline that searches relevant AI research, pulls the most useful context, summarizes the findings, and translates them into business-friendly insights with citations back to the original papers.

---

## 👥 Team

| Team Member | GitHub | Main Contributions |
|---|---|---|
| **Mandeep Khatri** | `@Mandeep-Khatri` | Development environment, arXiv exploration, ingestion and preprocessing, baseline RAG retrieval, end-to-end testing, context improvements, and workflow evaluation |
| **Darren Chen** | `@DaruneChen` | Grounded summarization, citation verification, Gemini integration, and generation testing |
| **Owen Huang** | `@0-owen` | Retrieval optimization, study-pipeline improvements, prompt engineering support, and evaluation testing |

We worked on different parts of the pipeline, but the pieces were designed to work together as one end-to-end system.

---

## 🎯 What We Built

Our goal was to make AI research easier to use for people who may not have time to read every paper in detail.

A user can ask a question such as:

> **How can a company choose between cheaper and more capable AI models while controlling cost?**

The system then:

1. Searches the available research.
2. Finds the papers and passages most related to the question.
3. Sends grounded research context to Gemini.
4. Summarizes what the papers actually say.
5. Explains what those findings could mean from a business perspective.
6. Includes citations so the answer can be traced back to the source.
7. Refuses to make up an answer when the available research does not support the question.

The last point became especially important during testing. We wanted the system to be useful, but we also wanted it to know when the evidence was not there.

---

## 💡 Why This Project Matters

There is often a gap between **technical research** and **business decision-making**.

For example, a research paper might discuss model routing, recursive self-improvement, or task induction. A business stakeholder may instead be thinking:

- Can this lower the cost of using AI?
- Could this improve an existing workflow?
- Is this useful outside a research setting?
- What are the risks or limitations?
- Is the evidence strong enough to support a decision?

Our project focuses on that translation step.

The goal is not to replace the original research. It is to make the research easier to understand, explore, and discuss while keeping the answer connected to the source material.

---

## 🏗️ How the System Works

At a high level, the pipeline looks like this:

```text
Research Papers
      ↓
Extract Text
      ↓
Clean and Split into Chunks
      ↓
Create Embeddings
      ↓
Store in ChromaDB
      ↓
User Asks a Question
      ↓
Retrieve Relevant Research
      ↓
Add Nearby Context
      ↓
Send Context to Gemini
      ↓
Research Summary
      ↓
Business Insight + Citations
```

In short:

**Ingestion → Preprocessing → Retrieval → Context Expansion → Generation → Business Insight**

The first half of the pipeline prepares the research so it can be searched efficiently. The second half starts when a user asks a question.

The retriever finds the most relevant research passages, the system adds nearby context when needed, and Gemini produces an answer using only the supplied research.

---

## 🔍 Pipeline Details

### 1. Research Ingestion

The default workflow uses the five research papers supplied for the project.

We extract the full text from the PDFs using `pypdf` and keep metadata such as the paper title and arXiv ID so retrieved passages can be traced back to their source.

We also built an optional arXiv exploration workflow that can retrieve a larger collection of recent AI papers for experimentation.

---

### 2. Preprocessing

The extracted text is cleaned and divided into overlapping chunks.

Current settings:

- **Chunk size:** 200 words
- **Overlap:** 40 words
- **Study papers:** 5
- **Processed chunks:** 335

The processed study data is saved to:

```text
data/processed/study_chunks.jsonl
```

The overlap helps preserve context when an important idea falls near the boundary between two chunks.

---

### 3. Embeddings and Retrieval

We use:

- **Sentence Transformers**
- `all-MiniLM-L6-v2`
- **ChromaDB**

Each research chunk is converted into an embedding and stored in ChromaDB.

When a user asks a question, the question is embedded using the same model and compared with the research collection.

Instead of returning several similar passages from the same paper, the retriever keeps the strongest passage from each of the top distinct papers.

This gives the generation model a more useful mix of sources.

---

### 4. Context Expansion

One of the most useful lessons from our end-to-end testing came from a retrieval failure that was not really a retrieval failure.

For one business question, the system retrieved the correct paper, but the highest-ranked passage did not contain enough surrounding information for Gemini to answer confidently.

To fix that, we added neighboring context around the retrieved passage:

```text
previous chunk
+
retrieved chunk
+
next chunk
```

This keeps the ranking behavior the same while giving Gemini enough local context to understand the research more completely.

After this change, questions that previously produced weak or incomplete answers improved noticeably.

---

### 5. Grounded Generation

The retrieved research is sent to Gemini with strict grounding instructions.

The model is told to:

- use only the supplied sources,
- cite the paper supporting each finding,
- avoid unsupported claims,
- clearly identify missing information,
- and refuse questions that the research cannot answer.

We also validate citations against the papers that were actually retrieved.

This does not completely solve hallucination, but it creates an important guardrail.

---

### 6. Business Insight Translation

A technically correct answer is not always a useful business answer.

We updated the generation prompt so the model does two things:

1. explains the research finding in plain language,
2. explains what that finding could mean for a business decision or use case.

For example:

```text
Research finding:
Routing requests across different language models can reduce cost
while maintaining strong performance.

Business implication:
A company may not need to use its most expensive model for every task.
Model routing could help balance capability and operating cost.
```

The prompt also tells the model not to invent:

- ROI,
- financial savings,
- legal requirements,
- market claims,
- implementation results,
- or evidence that is not present in the paper.

---

## 📊 Results

### Retrieval Evaluation

We evaluated retrieval using 15 questions across the five supplied studies.

| Metric | Result |
|---|---:|
| Recall@3 | **1.00** |
| Top-1 Accuracy | **1.00** |
| Mean Reciprocal Rank (MRR) | **1.00** |
| Queries Passed | **15 / 15** |

These results show that the retriever performed very well on our known five-paper benchmark.

They should not be interpreted as proof that retrieval will perform equally well on a much larger or completely unseen research collection.

---

### Automated Tests

Our current test suite passes:

```text
22 / 22 tests passed
```

The tests cover important parts of the generation workflow, including citation handling, unsupported questions, Gemini response parsing, and API retry behavior.

---

### End-to-End Evaluation

We also evaluated four representative business questions using a simple rubric based on:

- relevance,
- accuracy,
- completeness.

| Evaluation Scenario | Score | Result |
|---|---:|---|
| AI model routing and cost | **9/9** | PASS |
| Workflow knowledge from computer-use traces | **8/9** | PASS |
| Algorithm improvement vs. hardware optimization | **8/9** | PASS |
| Unsupported U.S. banking regulation question | **9/9** | PASS |

The unsupported banking-regulation test was especially useful.

The system retrieved the nearest available papers, but correctly recognized that those papers did not contain U.S. banking cybersecurity guidance. Instead of inventing regulations, it stated that the available sources could not answer the question.

That is the behavior we want from a research-grounded system.

---

## 🧪 Example

A user asks:

```text
How can a company choose between cheaper and more capable AI models while controlling cost?
```

The system retrieves the relevant research and produces an answer similar to:

```text
Research finding:
Companies can route user queries across different language models
to reduce cost while maintaining strong performance.

Business implication:
Organizations can balance model capability and operating expense
instead of automatically sending every request to the most
expensive model.

Source:
[2608.20316]
```

The goal is to give the user something they can understand quickly while still making it possible to return to the original research.

---

## 💻 Setup

### 1. Clone the repository

```bash
git clone https://github.com/Break-Through-Tech/KPMG-1B-ai-research-intelligence-agent-for-business-insight-translation.git

cd KPMG-1B-ai-research-intelligence-agent-for-business-insight-translation
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

For Bash or Zsh:

```bash
source .venv/bin/activate
```

For Fish:

```fish
source .venv/bin/activate.fish
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add a Gemini API key

Create a `.env` file in the repository root:

```text
GEMINI_API_KEY=your_api_key_here
```

You can also optionally set a model:

```text
GEMINI_MODEL=your_preferred_model
```

The `.env` file should stay local and should not be committed to GitHub.

---

### 5. Add the study PDFs

The default workflow expects the five supplied project PDFs inside:

```text
data/
```

---

### 6. Run preprocessing

```bash
python src/preprocessing.py
```

Expected output:

```text
Loaded 5 papers from studies
Created 335 chunks
Saved to data/processed/study_chunks.jsonl
```

---

### 7. Test retrieval

```bash
python src/retrieval.py
```

---

### 8. Run the retrieval evaluation

```bash
python src/evaluation.py
```

---

### 9. Ask a question

```bash
python src/generation.py "How can a company choose between cheaper and more capable AI models while controlling cost?" --model gemini-3.5-flash-lite
```

For JSON output:

```bash
python src/generation.py "Your question here" --json
```

---

### 10. Run the tests

```bash
pytest -q
```

---

## 📁 Repository Structure

```text
.
├── data/
│   ├── processed/
│   │   ├── study_chunks.jsonl
│   │   └── chroma_db/
│   └── [supplied research PDFs]
│
├── docs/
│   ├── business_insight_prompting.md
│   ├── end_to_end_evaluation.md
│   └── evaluation_rubric.md
│
├── notebooks/
│   └── 01_arxiv_data_exploration.ipynb
│
├── src/
│   ├── ingestion.py
│   ├── preprocessing.py
│   ├── retrieval.py
│   ├── generation.py
│   └── evaluation.py
│
├── tests/
├── requirements.txt
└── README.md
```

---

## 🧰 Tech Stack

| Area | Technology |
|---|---|
| Language | Python |
| PDF processing | pypdf |
| Research exploration | arXiv API |
| Embeddings | Sentence Transformers |
| Embedding model | `all-MiniLM-L6-v2` |
| Vector database | ChromaDB |
| Generation | Google Gemini |
| Environment variables | python-dotenv |
| Testing | pytest |
| Exploration | JupyterLab |
| Version control | Git / GitHub |

---

## 🧪 Evaluation

We use three simple questions when reviewing an answer.

### Relevance

Did the system answer the question the user actually asked?

### Accuracy

Are the claims supported by the retrieved research?

### Completeness

Did the answer include the important information that was available in the retrieved sources?

Each category is scored from **1 to 3**.

More details are available in:

```text
docs/evaluation_rubric.md
```

Full end-to-end results are documented in:

```text
docs/end_to_end_evaluation.md
```

Our prompt-engineering work is documented in:

```text
docs/business_insight_prompting.md
```

---

## ⚠️ What Still Needs Work

This is a working research prototype, not a finished production system.

A few limitations are important to call out:

- Our main evaluation set contains only five research papers.
- The retrieval benchmark uses known papers, so the current scores do not show how the system will behave on a large unseen collection.
- Citation validation confirms that a cited paper was retrieved, but it does not yet prove that every generated sentence is fully supported by that exact passage.
- Some business implications can still stretch slightly beyond what a paper directly demonstrates.
- The response schema does not yet require a separate structured `business_implication` field.
- For unrelated questions, retrieval will still return the closest papers. The generation layer therefore has to decide whether those papers actually support an answer.

We think documenting these limitations is just as important as reporting the successful results.

---

## 🚀 Next Steps

If we continued developing the project, the next areas we would explore are:

- evaluation on a larger set of unseen papers,
- stronger claim-level citation verification,
- a required structured `business_implication` field,
- automatic checks for unsupported business interpretations,
- better detection of questions outside the research collection,
- comparison of different embedding and retrieval approaches,
- a simple user interface for business users,
- and a larger set of realistic business questions for evaluation.

---

## 🙏 Acknowledgements

This project was developed through the **Break Through Tech AI Studio** in collaboration with **KPMG**.

We would like to thank:

- **Chris Jambor** — KPMG Challenge Advisor
- **Abhinav Raghunathan** — Business Owner
- **Alexandra Ladyzhensky** — AI Studio Coach
- **Break Through Tech AI Studio**

Their feedback helped us think beyond whether the pipeline simply worked and focus more on whether the output would actually be useful, understandable, and trustworthy for a business user.

---

## 📝 License

The project license should be confirmed with the Challenge Advisor and repository organization before a public license is added.
