# End-to-End Retrieval and Summarization Evaluation

## Overview

This evaluation tests the full research intelligence workflow from preprocessing and retrieval through live Gemini generation.

The goal was to verify that the system can:

- retrieve relevant research papers,
- generate grounded answers,
- cite the correct sources,
- provide enough context for generation,
- and refuse questions that are not supported by the available papers.

## Environment

Branch:

`testing/end-to-end-rag`

Live generation model used:

`gemini-3.5-flash-lite`

The default Gemini model returned temporary 503 service-unavailable errors during testing, so Flash Lite was used for the live evaluation.

## Baseline Validation

### Unit Tests

All existing tests passed:

`22/22 passed`

### Preprocessing

The preprocessing pipeline:

- loaded 5 supplied research papers,
- created 335 chunks,
- saved the processed data to `data/processed/study_chunks.jsonl`.

### Retrieval Evaluation

The existing 15-question retrieval benchmark produced:

- Recall@3: 1.00
- Top-1 accuracy: 1.00
- MRR: 1.00
- Queries passed: 15/15

These results are based on the known five-paper study dataset and do not represent general retrieval accuracy on unseen papers.

## End-to-End Testing

### Test 1: Model Cost and Capability

Question:

> How can a company choose between cheaper and more capable AI models while controlling cost?

The retriever correctly ranked:

`Pandora's AI Model Routing Box: Efficient Allocation with Costly Value Estimation`

as the top result.

During the first test, the system selected one passage from the correct paper, but Gemini returned that the papers did not answer the question.

Inspection showed that the retrieved paper was correct, but important supporting information was distributed across neighboring chunks.

The generation workflow was updated to include the previous and next chunk around each retrieved passage.

After the change, the normal end-to-end pipeline produced a grounded answer explaining how routing can reduce cost while maintaining accuracy and how value-of-information reasoning can manage the cost-performance tradeoff.

Citation:

`[2608.20316]`

Result: PASS after neighboring-context improvement.

### Test 2: Workflow Documentation

Question:

> How can an organization turn recorded computer activity into reusable workflow documentation?

The system retrieved:

`Inducing Task Models from Computer-Use Traces`

The generated answer explained how recorded screenshots and input events can be converted into semantic actions and hierarchical task models that can be reused as documentation.

Citation:

`[2608.20319]`

Result: PASS.

### Test 3: Algorithm Improvement vs. Hardware Optimization

Question:

> How could AI agents help a company improve algorithms instead of only optimizing hardware performance?

The system retrieved:

`AI4AI-Bench: Benchmarking LLM Agents in Algorithmic Design for Recursive Self-Improvement`

Before the neighboring-context improvement, the generated answer blurred the difference between data engineering and changes to the learning procedure.

After providing neighboring context, Gemini correctly distinguished hardware/system tuning from improvements to the learning procedure.

The model also clearly stated that the retrieved sources did not provide specific algorithmic improvements beyond this distinction.

Citation:

`[2608.20318]`

Result: PASS after neighboring-context improvement.

### Test 4: Unsupported Question

Question:

> What cybersecurity regulations should a U.S. bank follow when deploying generative AI?

The supplied research papers do not cover U.S. banking cybersecurity regulations.

The system correctly responded that the retrieved papers did not answer the question instead of generating unsupported regulatory guidance.

Result: PASS.

## Improvement Made

During end-to-end testing, a weakness was found in the generation context.

Retrieval correctly selected the relevant paper, but only the highest-ranked passage from each paper was originally passed to Gemini.

This could remove nearby information needed to answer a business-style question.

The generation pipeline was updated so that retrieval still selects the top distinct papers, but generation receives the retrieved passage together with its neighboring chunks.

For example:

`previous chunk + retrieved chunk + next chunk`

This preserves the existing paper-ranking behavior while providing more local context for grounded generation.

## Final Results

- Unit tests: PASS
- Preprocessing: PASS
- Retrieval benchmark: PASS
- Relevant business questions: PASS
- Grounded citations: PASS
- Unsupported-question refusal: PASS
- Neighboring-context generation improvement: PASS

## Remaining Limitations

Citation validation currently confirms that a cited paper was retrieved, but it does not independently verify that every generated claim is semantically entailed by the cited passage.

The current benchmark also uses a small known collection of five research papers, so future evaluation should include unseen papers and additional business-focused questions.
