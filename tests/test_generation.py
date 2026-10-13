"""
Tests for src/generation.py. They use a fake model, so they run offline with
no API key. Run from the repo root with: python -m pytest tests
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import generation  # noqa: E402
from generation import NOT_ANSWERED, arxiv_id, build_prompt, call_gemini, check_citations, collect_sources, summarize, to_markdown  # noqa: E402


def chroma_results(rows):
    """The shape retrieval.search() returns: lists wrapped in an outer list."""
    return {
        "documents": [[r[1] for r in rows]],
        "metadatas": [[{"paper_id": f"http://arxiv.org/abs/{r[0]}", "title": r[2], "published": "2026-09-01T10:00:00+00:00"} for r in rows]],
        "distances": [[0.1 * i for i in range(len(rows))]],
    }


RESULTS = chroma_results([
    ("2608.20316v1", "Routing queries to cheaper models cuts cost by 40 percent with little loss in accuracy.", "Pandora's AI Model Routing Box"),
    ("2608.20318v2", "Agents improved algorithm design scores on AI4AI-Bench.", "AI4AI-Bench"),
    ("2608.20316v1", "The router estimates the value of calling a larger model before paying for it.", "Pandora's AI Model Routing Box"),
])


def fake_llm(answer):
    calls = []

    def llm(prompt):
        calls.append(prompt)
        return json.dumps(answer) if isinstance(answer, dict) else answer

    llm.calls = calls
    return llm


# ---------------------------------------------------------------- sources

def test_arxiv_id_handles_urls_versions_and_prefixes():
    assert arxiv_id("http://arxiv.org/abs/2608.20316v1") == "2608.20316"
    assert arxiv_id("arXiv:2608.20316v12") == "2608.20316"
    assert arxiv_id("2608.20316") == "2608.20316"


def test_collect_sources_merges_chunks_from_the_same_paper():
    sources = collect_sources(RESULTS)
    assert [s["id"] for s in sources] == ["2608.20316", "2608.20318"]
    assert sources[0]["rank"] == 1 and len(sources[0]["texts"]) == 2
    assert sources[0]["url"] == "https://arxiv.org/abs/2608.20316"
    assert sources[0]["published"] == "2026-09-01"


def test_collect_sources_with_no_results():
    assert collect_sources({"documents": [[]], "metadatas": [[]]}) == []
    assert collect_sources(None) == []


def test_prompt_lists_every_source_with_its_id():
    prompt = build_prompt("How can we cut LLM costs?", collect_sources(RESULTS))
    assert "Question: How can we cut LLM costs?" in prompt
    assert "[2608.20316] Pandora's AI Model Routing Box" in prompt
    assert "[2608.20318] AI4AI-Bench" in prompt
    assert "Sources (2 papers)" in prompt


# ---------------------------------------------------------------- citations

def test_valid_answer_keeps_findings_and_cites_sources():
    llm = fake_llm({"answerable": True, "gaps": "", "findings": [
        {"statement": "Routing queries to cheaper models cut cost by about 40 percent.", "citations": ["2608.20316"]},
    ]})
    result = summarize("How can we cut LLM costs?", RESULTS, llm=llm)
    assert result["answered"] is True
    assert result["findings"] == [{"statement": "Routing queries to cheaper models cut cost by about 40 percent.", "citations": ["2608.20316"]}]
    md = to_markdown(result)
    assert "cut cost by about 40 percent. [2608.20316]" in md
    assert "**Sources**" in md and "https://arxiv.org/abs/2608.20316" in md
    assert "AI4AI-Bench" not in md  # only cited papers are listed as sources


def test_made_up_citations_are_removed():
    llm = fake_llm({"answerable": True, "gaps": "", "findings": [
        {"statement": "Routing cuts cost.", "citations": ["2608.20316", "9999.99999"]},
        {"statement": "A claim with nothing behind it.", "citations": ["1234.56789"]},
    ]})
    result = summarize("How can we cut LLM costs?", RESULTS, llm=llm)
    assert [f["statement"] for f in result["findings"]] == ["Routing cuts cost."]
    assert result["findings"][0]["citations"] == ["2608.20316"]
    assert sorted(result["removed_citations"]) == ["1234.56789", "9999.99999"]
    assert "Removed 2 citation(s)" in to_markdown(result)


def test_citation_formats_are_normalized():
    findings, removed = check_citations(
        {"findings": [{"statement": "x", "citations": ["[2608.20316v1]", "arXiv:2608.20318", "2608.20316"]}]},
        collect_sources(RESULTS),
    )
    assert findings[0]["citations"] == ["2608.20316", "2608.20318"] and removed == []


def test_ids_written_into_the_statement_are_stripped():
    findings, _ = check_citations({"findings": [{"statement": "Routing cuts cost [2608.20316].", "citations": ["2608.20316"]}]}, collect_sources(RESULTS))
    assert findings[0]["statement"] == "Routing cuts cost."


# ---------------------------------------------------------------- not answerable

def test_model_says_sources_dont_answer():
    llm = fake_llm({"answerable": False, "findings": [], "gaps": "None of the papers discuss healthcare billing."})
    result = summarize("How is AI used in healthcare billing?", RESULTS, llm=llm)
    assert result["answered"] is False
    md = to_markdown(result)
    assert md.splitlines()[2] == NOT_ANSWERED
    assert "healthcare billing" in md and "**Papers that were retrieved**" in md


def test_answerable_but_no_valid_citations_counts_as_not_answered():
    llm = fake_llm({"answerable": True, "gaps": "", "findings": [{"statement": "Something.", "citations": ["0000.00000"]}]})
    result = summarize("q", RESULTS, llm=llm)
    assert result["answered"] is False and "none of its findings had a valid citation" in result["note"]
    assert NOT_ANSWERED in to_markdown(result)


def test_no_retrieved_papers_skips_the_model():
    llm = fake_llm({"answerable": True, "findings": [], "gaps": ""})
    result = summarize("q", {"documents": [[]], "metadatas": [[]]}, llm=llm)
    assert llm.calls == [] and result["answered"] is False
    assert "No papers were retrieved" in result["note"]


def test_unreadable_model_output_is_handled():
    result = summarize("q", RESULTS, llm=fake_llm("this is not json"))
    assert result["answered"] is False and "couldn't be read" in result["note"]


def test_code_fenced_json_is_accepted():
    fenced = '```json\n{"answerable": true, "gaps": "", "findings": [{"statement": "Routing cuts cost.", "citations": ["2608.20316"]}]}\n```'
    assert summarize("q", RESULTS, llm=fake_llm(fenced))["answered"] is True


# ---------------------------------------------------------------- the Gemini call



def test_call_gemini_retries_when_rate_limited(monkeypatch):
    from google.genai import errors

    class Models:
        def __init__(self):
            self.calls = 0

        def generate_content(self, model, contents, config):
            self.calls += 1
            if self.calls == 1:
                raise errors.APIError(429, {"error": {"message": "rate limited", "status": "RESOURCE_EXHAUSTED"}})
            assert config.response_mime_type == "application/json"
            assert config.response_json_schema == generation.RESPONSE_SCHEMA
            return type("R", (), {"text": '{"answerable": false, "findings": [], "gaps": ""}'})()

    client = type("C", (), {"models": Models()})()
    monkeypatch.setattr(generation.time, "sleep", lambda s: None)
    assert json.loads(call_gemini("prompt", client=client))["answerable"] is False
    assert client.models.calls == 2


def test_call_gemini_does_not_retry_bad_requests(monkeypatch):
    from google.genai import errors

    class Models:
        calls = 0

        def generate_content(self, model, contents, config):
            Models.calls += 1
            raise errors.APIError(400, {"error": {"message": "bad request", "status": "INVALID_ARGUMENT"}})

    client = type("C", (), {"models": Models()})()
    with pytest.raises(errors.APIError):
        call_gemini("prompt", client=client)
    assert Models.calls == 1


def test_call_gemini_explains_a_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        call_gemini("prompt")
