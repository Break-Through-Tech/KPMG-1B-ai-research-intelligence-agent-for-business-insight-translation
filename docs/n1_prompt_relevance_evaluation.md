# Task N1: Prompt, Relevance, and Evaluation Refinement

## Goal

Refine the generation prompt and relevance behavior based on the evaluation results from Milestone 2.

## Changes Made

### Structured Business Implications

The generation response schema now requires each supported finding to contain:

- a research statement,
- a separate business implication,
- at least one valid citation.

This prevents the business implication from being omitted and makes research findings easier to separate from business interpretation.

### More Conservative Business Wording

The generation prompt was updated so that business implications cannot claim improvements in accuracy, capability, efficiency, adoption, cost, or other outcomes unless the cited research directly demonstrates them.

When the research only suggests a possible business use, the model is instructed to use cautious wording such as:

- "may support"
- "could help"
- "could be used to"

### Relevance Review

The existing retrieval behavior was evaluated before making ranking changes.

A hard retrieval-distance threshold was not added because the current workflow successfully:

- ranks the correct paper first for supported questions,
- uses generation-level grounding to determine whether the retrieved papers actually answer the question,
- refuses unsupported questions instead of stretching unrelated sources.

## Evaluation Results

### Test 1: AI Model Routing and Cost

Question:

> How can a company choose between cheaper and more capable AI models while controlling cost?

Top-ranked paper:

`Pandora's AI Model Routing Box: Efficient Allocation with Costly Value Estimation`

Result:

- correct paper ranked #1,
- answer produced successfully,
- separate business implications produced,
- citations grounded in `2608.20316`,
- no invalid citations.

Result: PASS

### Test 2: Unsupported Banking Regulation Question

Question:

> What cybersecurity regulations should a U.S. bank follow when deploying generative AI?

The available research papers do not cover U.S. banking cybersecurity regulations.

The system returned:

- no findings,
- `answered: false`,
- a clear explanation of the missing coverage.

Result: PASS

### Test 3: Workflow Knowledge from Computer Activity

Question:

> How can organizations turn recorded computer activity into reusable workflow knowledge?

Top-ranked paper:

`Inducing Task Models from Computer-Use Traces`

Result:

- correct paper ranked #1,
- grounded finding produced,
- separate business implication produced,
- cautious wording used,
- citation grounded in `2608.20319`.

Result: PASS

## Validation

All automated tests passed:

`22/22 passed`

## Conclusion

The prompt and structured output were improved based on the previous evaluation findings.

The current retrieval ranking was retained because supported questions rank the expected paper first and unsupported questions are correctly rejected by the grounding layer.

No hard relevance threshold was introduced because the current small five-paper dataset does not provide enough evidence to choose a reliable universal distance cutoff.