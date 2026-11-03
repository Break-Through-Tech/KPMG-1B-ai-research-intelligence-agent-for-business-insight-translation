# Integrated Workflow Evaluation Rubric

## Goal

Evaluate the end-to-end research intelligence workflow for relevance, accuracy, and completeness, and document improvement opportunities.

## Scoring Scale

Each category is scored from 1 to 3.

### Relevance

- **3 - Strong:** The answer directly addresses the user's question using relevant retrieved research.
- **2 - Partial:** The answer is related to the question but includes unnecessary or weakly relevant information.
- **1 - Poor:** The answer does not meaningfully address the question.

### Accuracy

- **3 - Strong:** Claims are supported by the retrieved research and citations are appropriate.
- **2 - Partial:** Most claims are supported, but some wording stretches beyond what the source clearly states.
- **1 - Poor:** The answer contains unsupported, misleading, or incorrect claims.

### Completeness

- **3 - Strong:** The answer covers the important parts of the question that are supported by the retrieved papers.
- **2 - Partial:** The answer addresses the main idea but misses useful supported details.
- **1 - Poor:** Important supported information is missing.

## Evaluation Questions

1. How can a company choose between cheaper and more capable AI models while controlling cost?
2. How can organizations turn recorded computer activity into reusable workflow knowledge?
3. How could AI agents help a company improve algorithms instead of only optimizing hardware performance?
4. What cybersecurity regulations should a U.S. bank follow when deploying generative AI?

## Evaluation Method

For each question:

1. Run the full retrieval and generation pipeline.
2. Review the retrieved papers and generated answer.
3. Score relevance, accuracy, and completeness from 1 to 3.
4. Record whether citations support the claims.
5. Record any failure, limitation, or improvement opportunity.

## Success Criteria

A successful answer should:

- score at least 2 in each category,
- remain grounded in retrieved research,
- use valid citations,
- clearly state when the retrieved papers do not answer the question,
- provide understandable business implications when supported by the research.
