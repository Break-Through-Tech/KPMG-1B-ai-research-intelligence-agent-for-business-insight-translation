# Business Insight Prompt Engineering

## Goal

Task #4 focuses on translating technical AI research findings into clear business-friendly insights for KPMG stakeholders while keeping every answer grounded in the retrieved research.

## Prompt Strategy

The generation system instruction was updated to require each finding to contain:

1. A short research finding stated in plain language.
2. A second sentence beginning with **"Business implication:"** that explains what the research could mean for a business decision or use case.
3. Citations to the retrieved research papers.

The prompt also instructs the model to avoid unsupported claims such as invented ROI, financial savings, legal requirements, market claims, or implementation results.

When supported by the research, business implications may discuss areas such as cost, efficiency, capability, workflow, risk, scalability, and adoption.

## Validation

All existing unit tests continued to pass after the prompt update:

- 22/22 tests passed.

### Test 1: AI Model Routing

Question:

"How can a company choose between cheaper and more capable AI models while controlling cost?"

The system correctly explained model routing and value estimation and translated the findings into business implications related to model-selection costs and operational efficiency.

### Test 2: Workflow Knowledge

Question:

"How can organizations turn recorded computer activity into reusable workflow knowledge?"

The system correctly explained task-model induction and translated the research into business implications related to reusable workflow knowledge and handling employees switching between tasks.

## Result

The updated prompt produces clearer business-oriented answers while preserving research grounding and citations. No retrieval or citation-validation logic was changed.
