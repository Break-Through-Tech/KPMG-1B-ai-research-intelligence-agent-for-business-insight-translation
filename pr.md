Adds the generation step so the pipeline produces an answer instead of
stopping at retrieved chunks.

- `src/generation.py` - groups retrieved chunks by paper, prompts Gemini
  for structured JSON, and drops any finding whose citation doesn't match
  a retrieved paper
- `tests/test_generation.py` - 16 tests, LLM stubbed out, no API key needed
- `docs/generation.md`, `.env.example`
- requirements: `google-genai`, `pytest`

Returns "the retrieved papers don't answer this question" rather than
stretching loosely related sources.
