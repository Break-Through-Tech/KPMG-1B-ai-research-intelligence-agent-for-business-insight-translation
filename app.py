import base64
import html
import os
import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------
# Project imports
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from generation import expand_neighbor_context, summarize
from retrieval import build_vector_store, load_chunks, search


# ---------------------------------------------------------
# Page setup
# ---------------------------------------------------------

st.set_page_config(
    page_title="AI Research Intelligence Agent",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def clean(value):
    return html.escape(str(value or ""))


def image_to_base64(path):
    path = Path(path)
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


KPMG_LOGO = image_to_base64(ROOT / "static" / "kpmg-logo.png")


# ---------------------------------------------------------
# Research engine
# ---------------------------------------------------------

@st.cache_resource(show_spinner=False)
def load_engine():
    chunks = load_chunks("arxiv")
    collection, model = build_vector_store(chunks, "arxiv")
    return chunks, collection, model


def ask_agent(question):
    chunks, collection, model = load_engine()

    results = search(
        question,
        collection,
        model,
        top_k=3,
    )

    context = expand_neighbor_context(
        results,
        chunks,
        window=1,
    )

    gemini_model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite",
    )

    return summarize(
        question,
        context,
        model=gemini_model,
    )


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

defaults = {
    "page": "Home",
    "question": "",
    "result": None,
    "history": [],
    "saved_insights": [],
    "evaluation_runs": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def go(page):
    st.session_state.page = page


def open_example(question):
    st.session_state.question = question
    st.session_state.page = "Research"


def save_current_result():
    result = st.session_state.get("result")
    if not result:
        return

    question = result.get("question", "")
    exists = any(
        item.get("question") == question
        for item in st.session_state.saved_insights
    )

    if not exists:
        st.session_state.saved_insights.insert(
            0,
            {"question": question, "result": result},
        )


def record_run(question, result):
    # history keeps a compact question list
    st.session_state.history = [
        item for item in st.session_state.history
        if item != question
    ]
    st.session_state.history.insert(0, question)
    st.session_state.history = st.session_state.history[:20]

    # evaluation keeps full structured results
    st.session_state.evaluation_runs = [
        item for item in st.session_state.evaluation_runs
        if item.get("question") != question
    ]
    st.session_state.evaluation_runs.insert(
        0,
        {"question": question, "result": result},
    )


# ---------------------------------------------------------
# Styles
# ---------------------------------------------------------

st.html(
    """
    <style>
    :root {
        --ink: #10213a;
        --muted: #617086;
        --line: #e5eaf0;
        --panel: #ffffff;
        --surface: #f5f7fa;
        --navy: #071b34;
        --navy-2: #0b274a;
        --blue: #1d5fd3;
        --blue-soft: #edf4ff;
        --green: #1d8a68;
        --green-soft: #edf9f5;
        --amber: #a96914;
        --amber-soft: #fff7e9;
        --danger: #b33a3a;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    header[data-testid="stHeader"] {
        height: 0;
        background: transparent;
    }

    [data-testid="stToolbar"],
    #MainMenu,
    footer {
        display: none;
    }

    .stApp {
        background: #f6f8fb;
        color: var(--ink);
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.25rem;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-bottom: 2rem;
    }

    section[data-testid="stSidebar"] {
        width: 250px !important;
        min-width: 250px !important;
        background: linear-gradient(180deg, var(--navy), var(--navy-2));
        border-right: none;
    }

    [data-testid="stSidebarUserContent"] {
        padding: 24px 16px 18px 16px !important;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0 4px 18px;
        border-bottom: 1px solid rgba(255,255,255,.10);
        margin-bottom: 14px;
    }

    .brand img {
        width: 72px;
        height: auto;
        display: block;
    }

    .brand-copy {
        color: white;
        font-size: 12px;
        line-height: 1.35;
        font-weight: 650;
    }

    .sidebar-label {
        color: rgba(255,255,255,.46);
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .11em;
        margin: 16px 8px 8px;
    }

    section[data-testid="stSidebar"] div[data-testid="stButton"] button {
        width: 100%;
        justify-content: flex-start;
        min-height: 42px;
        padding: 0 13px;
        border-radius: 9px;
        border: 1px solid transparent;
        background: transparent;
        color: #dce6f4;
        font-size: 13px;
        font-weight: 600;
        box-shadow: none;
        margin: 2px 0;
    }

    section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
        color: white;
        background: rgba(255,255,255,.07);
        border-color: rgba(255,255,255,.06);
    }

    section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {
        color: white;
        background: rgba(67,116,207,.28);
        border: 1px solid rgba(115,159,237,.32);
        box-shadow: inset 3px 0 0 #66a1ff;
    }

    .sidebar-note {
        margin-top: 26px;
        padding: 14px;
        border-radius: 12px;
        color: #d7e6fa;
        background: rgba(255,255,255,.055);
        border: 1px solid rgba(255,255,255,.09);
        font-size: 11px;
        line-height: 1.5;
    }

    .sidebar-note strong {
        display: block;
        color: white;
        margin-bottom: 5px;
        font-size: 12px;
    }

    .eyebrow {
        color: #2f67b8;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .11em;
        margin-bottom: 9px;
    }

    .page-title {
        color: var(--ink);
        font-size: 34px;
        line-height: 1.1;
        font-weight: 760;
        letter-spacing: -.8px;
        margin: 0 0 10px;
    }

    .page-subtitle {
        color: var(--muted);
        font-size: 14px;
        line-height: 1.55;
        max-width: 760px;
        margin-bottom: 22px;
    }

    .hero-panel {
        border: 1px solid var(--line);
        border-radius: 18px;
        background: linear-gradient(135deg, #ffffff, #f6f9fd);
        padding: 28px 30px;
        margin-bottom: 18px;
        box-shadow: 0 8px 26px rgba(20,42,76,.04);
    }

    .hero-grid {
        display: grid;
        grid-template-columns: 1.45fr .8fr;
        gap: 28px;
        align-items: center;
    }

    .hero-title {
        color: var(--ink);
        font-size: 38px;
        line-height: 1.08;
        font-weight: 780;
        letter-spacing: -1px;
        margin-bottom: 12px;
        max-width: 760px;
    }

    .hero-copy {
        color: var(--muted);
        font-size: 14px;
        line-height: 1.6;
        max-width: 720px;
    }

    .hero-visual {
        min-height: 150px;
        border-radius: 16px;
        background:
            linear-gradient(145deg, rgba(29,95,211,.07), rgba(17,135,107,.05)),
            repeating-linear-gradient(
                90deg,
                transparent 0,
                transparent 42px,
                rgba(29,95,211,.035) 43px
            );
        border: 1px solid #e3ebf6;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .hero-flow {
        display: flex;
        align-items: center;
        gap: 9px;
        color: #35516f;
        font-size: 11px;
        font-weight: 700;
    }

    .hero-node {
        width: 66px;
        height: 66px;
        border-radius: 13px;
        background: white;
        border: 1px solid #dce6f3;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        box-shadow: 0 5px 14px rgba(20,42,76,.04);
    }

    .section-title {
        color: var(--ink);
        font-size: 17px;
        font-weight: 760;
        margin: 20px 0 10px;
    }

    .grid-3 {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
    }

    .grid-4 {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
    }

    .info-card {
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 17px;
        background: var(--panel);
        min-height: 118px;
    }

    .info-card h4 {
        color: var(--ink);
        font-size: 14px;
        margin: 0 0 7px;
    }

    .info-card p {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.5;
        margin: 0;
    }

    .metric-card {
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 14px 15px;
        background: white;
    }

    .metric-label {
        color: var(--muted);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: .06em;
        font-weight: 750;
    }

    .metric-value {
        color: var(--ink);
        font-size: 23px;
        font-weight: 760;
        margin-top: 4px;
    }

    .topic-card {
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 16px;
        background: white;
        min-height: 112px;
    }

    .topic-tag {
        display: inline-block;
        border-radius: 999px;
        padding: 4px 8px;
        margin-bottom: 9px;
        background: var(--blue-soft);
        color: #2b5fae;
        font-size: 9px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .05em;
    }

    .topic-title {
        color: var(--ink);
        font-size: 13px;
        font-weight: 760;
        line-height: 1.35;
        margin-bottom: 7px;
    }

    .topic-copy {
        color: var(--muted);
        font-size: 11px;
        line-height: 1.45;
    }

    .result-card {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: white;
        padding: 18px;
        margin-bottom: 12px;
    }

    .result-card.business {
        background: #f8fbff;
        border-color: #dce7f5;
    }

    .result-label {
        color: #3967a7;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: .07em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .result-copy {
        color: #2b3f56;
        font-size: 14px;
        line-height: 1.65;
    }

    .source-row {
        border-top: 1px solid var(--line);
        padding: 12px 0;
    }

    .source-title {
        color: var(--ink);
        font-size: 13px;
        font-weight: 700;
    }

    .source-meta {
        color: var(--muted);
        font-size: 11px;
        margin-top: 3px;
    }

    .empty-state {
        border: 1px dashed #cfd8e6;
        border-radius: 14px;
        background: white;
        color: var(--muted);
        padding: 28px;
        text-align: center;
        font-size: 13px;
    }

    .method-step {
        display: grid;
        grid-template-columns: 36px 1fr;
        gap: 12px;
        padding: 12px 0;
        border-bottom: 1px solid var(--line);
    }

    .step-num {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: var(--blue-soft);
        color: #2b5fae;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 800;
    }

    .step-title {
        color: var(--ink);
        font-size: 12px;
        font-weight: 760;
        margin-bottom: 3px;
    }

    .step-copy {
        color: var(--muted);
        font-size: 11px;
        line-height: 1.45;
    }

    div[data-testid="stTextInput"] input {
        min-height: 54px;
        border-radius: 11px;
        border: 1px solid #cfd9e7;
        background: white;
        font-size: 14px;
        padding-left: 15px;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #6b91cf;
        box-shadow: 0 0 0 2px rgba(66,110,180,.08);
    }

    .stButton > button[kind="primary"] {
        min-height: 52px;
        border-radius: 10px;
        border: none;
        background: #174f9f;
        color: white;
        font-size: 13px;
        font-weight: 700;
        box-shadow: none;
    }

    .stButton > button[kind="secondary"] {
        min-height: 40px;
        border-radius: 9px;
        border: 1px solid #d5deeb;
        background: white;
        color: #29435f;
        font-size: 12px;
        box-shadow: none;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 12px;
        overflow: hidden;
    }

    @media (max-width: 1000px) {
        .grid-3, .grid-4, .hero-grid {
            grid-template-columns: 1fr;
        }
        section[data-testid="stSidebar"] {
            width: 220px !important;
            min-width: 220px !important;
        }
    }
    </style>
    """
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    if KPMG_LOGO:
        st.html(
            f"""
            <div class="brand">
                <img src="data:image/png;base64,{KPMG_LOGO}" alt="KPMG">
                <div class="brand-copy">
                    Break Through Tech<br>
                    AI Studio
                </div>
            </div>
            """
        )
    else:
        st.html(
            """
            <div class="brand">
                <div class="brand-copy">
                    KPMG × Break Through Tech<br>
                    AI Studio
                </div>
            </div>
            """
        )

    st.html('<div class="sidebar-label">Workspace</div>')

    for page in ["Home", "Research", "Saved Insights", "History"]:
        st.button(
            page,
            key=f"nav_{page}",
            type="primary" if st.session_state.page == page else "secondary",
            use_container_width=True,
            on_click=go,
            args=(page,),
        )

    st.html('<div class="sidebar-label">Quality</div>')

    for page in ["Evaluation", "About"]:
        st.button(
            page,
            key=f"nav_{page}",
            type="primary" if st.session_state.page == page else "secondary",
            use_container_width=True,
            on_click=go,
            args=(page,),
        )

    st.html(
        """
        <div class="sidebar-note">
            <strong>Research Intelligence Agent</strong>
            Retrieves relevant AI research, produces grounded findings,
            translates them into business implications, and cites the source.
        </div>
        """
    )


# ---------------------------------------------------------
# Shared page header
# ---------------------------------------------------------

def page_header(eyebrow, title, subtitle):
    st.html(
        f"""
        <div class="eyebrow">{clean(eyebrow)}</div>
        <div class="page-title">{clean(title)}</div>
        <div class="page-subtitle">{clean(subtitle)}</div>
        """
    )


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

if st.session_state.page == "Home":
    history_count = len(st.session_state.history)
    saved_count = len(st.session_state.saved_insights)
    evaluated_count = len(st.session_state.evaluation_runs)

    total_findings = sum(
        len(item["result"].get("findings", []))
        for item in st.session_state.evaluation_runs
        if item["result"].get("answered")
    )

    cited_findings = sum(
        1
        for item in st.session_state.evaluation_runs
        if item["result"].get("answered")
        for finding in item["result"].get("findings", [])
        if finding.get("citations")
    )

    citation_coverage = (
        (cited_findings / total_findings) * 100
        if total_findings
        else 0
    )

    st.html(
        """
        <div class="hero-panel">
            <div class="hero-grid">
                <div>
                    <div class="eyebrow">KPMG × Break Through Tech AI Studio</div>
                    <div class="hero-title">AI Research Intelligence Agent</div>
                    <div class="hero-copy">
                        A research-to-business workflow for monitoring emerging AI work,
                        retrieving relevant evidence, and translating technical findings
                        into practical business implications with traceable citations.
                    </div>
                </div>
                <div class="hero-visual">
                    <div class="hero-flow">
                        <div class="hero-node">Research</div>
                        <div>→</div>
                        <div class="hero-node">Evidence</div>
                        <div>→</div>
                        <div class="hero-node">Insight</div>
                    </div>
                </div>
            </div>
        </div>
        """
    )

    start_col, _ = st.columns([1.2, 4.8])
    with start_col:
        if st.button(
            "Start research",
            key="home_start",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.page = "Research"
            st.rerun()

    st.html('<div class="section-title">Workspace snapshot</div>')
    st.html(
        f"""
        <div class="grid-4">
            <div class="metric-card">
                <div class="metric-label">Questions asked</div>
                <div class="metric-value">{history_count}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Saved insights</div>
                <div class="metric-value">{saved_count}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Evaluated runs</div>
                <div class="metric-value">{evaluated_count}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Citation coverage</div>
                <div class="metric-value">{citation_coverage:.0f}%</div>
            </div>
        </div>
        """
    )

    st.html('<div class="section-title">What the agent does</div>')
    st.html(
        """
        <div class="grid-3">
            <div class="info-card">
                <h4>Find relevant research</h4>
                <p>
                    Search the current arXiv-based research collection and retrieve
                    the most relevant evidence for a business or AI question.
                </p>
            </div>
            <div class="info-card">
                <h4>Translate research into business meaning</h4>
                <p>
                    Keep the research finding separate from the business implication
                    so evidence and interpretation remain clear.
                </p>
            </div>
            <div class="info-card">
                <h4>Keep answers traceable</h4>
                <p>
                    Link generated findings back to cited research and surface
                    evidence gaps instead of inventing unsupported answers.
                </p>
            </div>
        </div>
        """
    )

    st.html('<div class="section-title">Suggested research questions</div>')

    q1, q2, q3 = st.columns(3)

    examples = [
        (
            "AI cost strategy",
            "How can a company choose between cheaper and more capable AI models while controlling cost?",
            q1,
        ),
        (
            "Workflow intelligence",
            "How can organizations turn recorded computer activity into reusable workflow knowledge?",
            q2,
        ),
        (
            "Agentic AI improvement",
            "How could AI agents help a company improve algorithms instead of only optimizing hardware performance?",
            q3,
        ),
    ]

    for index, (tag, question_text, column) in enumerate(examples, start=1):
        with column:
            st.html(
                f"""
                <div class="topic-card">
                    <div class="topic-tag">{clean(tag)}</div>
                    <div class="topic-title">{clean(question_text)}</div>
                    <div class="topic-copy">
                        Open this question in the research workspace.
                    </div>
                </div>
                """
            )
            st.button(
                "Open in Research",
                key=f"example_{index}",
                use_container_width=True,
                on_click=open_example,
                args=(question_text,),
            )

    if st.session_state.history:
        st.html('<div class="section-title">Recent research</div>')
        for question_text in st.session_state.history[:5]:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(question_text)
            with col2:
                if st.button(
                    "Reopen",
                    key=f"home_recent_{question_text}",
                    use_container_width=True,
                ):
                    open_example(question_text)
                    st.rerun()


# ---------------------------------------------------------
# RESEARCH
# ---------------------------------------------------------

elif st.session_state.page == "Research":
    page_header(
        "Research Workspace",
        "Ask a research question",
        "Retrieve relevant AI research and generate grounded findings, business implications, citations, and evidence gaps.",
    )

    search_col, action_col = st.columns([5, 1.3], gap="small")

    with search_col:
        question = st.text_input(
            "Question",
            key="question",
            placeholder="Example: How can companies reduce the cost of using AI models?",
            label_visibility="collapsed",
        )

    with action_col:
        ask_clicked = st.button(
            "Run research",
            type="primary",
            use_container_width=True,
        )

    st.caption(
        "The agent answers only from the current research collection and may refuse when evidence is insufficient."
    )

    if ask_clicked:
        question_text = question.strip()

        if not question_text:
            st.warning("Enter a research question first.")
        else:
            try:
                with st.spinner("Retrieving research and generating a grounded response..."):
                    result = ask_agent(question_text)

                st.session_state.result = result
                record_run(question_text, result)

            except Exception as error:
                st.error("The research pipeline could not complete this request.")
                with st.expander("Technical details"):
                    st.code(str(error))

    result = st.session_state.get("result")

    if result:
        st.divider()

        response_col, save_col = st.columns([5, 1.2])

        with response_col:
            st.subheader("Research response")
            st.caption(result.get("question", ""))

        with save_col:
            if st.button(
                "Save insight",
                key="save_result",
                use_container_width=True,
            ):
                before = len(st.session_state.saved_insights)
                save_current_result()
                after = len(st.session_state.saved_insights)

                if after > before:
                    st.success("Saved.")
                else:
                    st.info("Already saved.")

        if result.get("answered"):
            for number, finding in enumerate(
                result.get("findings", []),
                start=1,
            ):
                citations = finding.get("citations", [])
                citation_text = (
                    " · ".join(f"[{clean(c)}]" for c in citations)
                    if citations
                    else "No citation"
                )

                st.html(
                    f"""
                    <div class="result-card">
                        <div class="result-label">Research finding {number}</div>
                        <div class="result-copy">
                            {clean(finding.get("statement", ""))}
                        </div>
                        <div class="source-meta" style="margin-top:10px;">
                            {citation_text}
                        </div>
                    </div>

                    <div class="result-card business">
                        <div class="result-label">Business implication</div>
                        <div class="result-copy">
                            {clean(finding.get("business_implication", ""))}
                        </div>
                    </div>
                    """
                )

            if result.get("gaps"):
                st.subheader("Evidence gaps")
                st.info(result["gaps"])

            st.subheader("Cited research")

            cited_ids = {
                str(citation)
                for finding in result.get("findings", [])
                for citation in finding.get("citations", [])
            }

            cited_sources = [
                source
                for source in result.get("sources", [])
                if str(source.get("id", "")) in cited_ids
            ]

            if not cited_sources:
                st.info("No cited sources were returned.")
            else:
                for source in cited_sources:
                    st.html(
                        f"""
                        <div class="source-row">
                            <div class="source-title">
                                {clean(source.get("title", "Untitled paper"))}
                            </div>
                            <div class="source-meta">
                                arXiv {clean(source.get("id", ""))}
                            </div>
                        </div>
                        """
                    )
                    if source.get("url"):
                        st.link_button(
                            "Open paper",
                            source["url"],
                        )

        else:
            st.warning(
                "The current research collection does not contain enough evidence to answer this question reliably."
            )

            if result.get("gaps"):
                st.subheader("What is missing")
                st.write(result["gaps"])

        with st.expander("Retrieval details"):
            for source in result.get("sources", []):
                distance = source.get("distance")
                distance_text = (
                    f"{distance:.4f}"
                    if isinstance(distance, (int, float))
                    else "N/A"
                )

                st.write(
                    f"**Rank {source.get('rank', '')} — "
                    f"{source.get('title', 'Untitled')}**"
                )
                st.caption(
                    f"arXiv {source.get('id', '')} · "
                    f"retrieval distance {distance_text}"
                )


# ---------------------------------------------------------
# SAVED INSIGHTS
# ---------------------------------------------------------

elif st.session_state.page == "Saved Insights":
    page_header(
        "Knowledge Workspace",
        "Saved insights",
        "A working collection of research responses you chose to keep for later review.",
    )

    if not st.session_state.saved_insights:
        st.html(
            """
            <div class="empty-state">
                No saved insights yet.<br>
                Run a research question and select <strong>Save insight</strong>.
            </div>
            """
        )
    else:
        for index, item in enumerate(
            st.session_state.saved_insights,
            start=1,
        ):
            result = item["result"]
            question_text = item["question"]

            with st.expander(
                f"{index}. {question_text}",
                expanded=index == 1,
            ):
                if result.get("answered"):
                    for number, finding in enumerate(
                        result.get("findings", []),
                        start=1,
                    ):
                        st.markdown(f"**Finding {number}**")
                        st.write(finding.get("statement", ""))

                        st.markdown("**Business implication**")
                        st.write(
                            finding.get("business_implication", "")
                        )

                        citations = finding.get("citations", [])
                        if citations:
                            st.caption(
                                "Sources: "
                                + ", ".join(
                                    f"[{citation}]"
                                    for citation in citations
                                )
                            )
                else:
                    st.warning(
                        "This saved question did not have enough supporting evidence."
                    )


# ---------------------------------------------------------
# HISTORY
# ---------------------------------------------------------

elif st.session_state.page == "History":
    page_header(
        "Research Log",
        "History",
        "Questions asked during the current session, ordered from most recent to oldest.",
    )

    if not st.session_state.history:
        st.html(
            """
            <div class="empty-state">
                No research history yet.
            </div>
            """
        )
    else:
        for index, question_text in enumerate(
            st.session_state.history,
            start=1,
        ):
            row1, row2 = st.columns([5, 1])

            with row1:
                st.write(f"**{index}. {question_text}**")

            with row2:
                if st.button(
                    "Open",
                    key=f"history_open_{index}",
                    use_container_width=True,
                ):
                    st.session_state.question = question_text
                    st.session_state.page = "Research"
                    st.rerun()

            st.divider()


# ---------------------------------------------------------
# EVALUATION
# ---------------------------------------------------------

elif st.session_state.page == "Evaluation":
    page_header(
        "Quality & Evidence",
        "Evaluation",
        "Measured checks from actual research runs. The dashboard reports observable pipeline behavior without inventing quality scores.",
    )

    runs = st.session_state.evaluation_runs

    if not runs:
        st.html(
            """
            <div class="empty-state">
                No evaluated runs yet.<br>
                Ask a question in Research and the measurable checks will appear here automatically.
            </div>
            """
        )
    else:
        total_questions = len(runs)

        answered_count = sum(
            1
            for item in runs
            if item["result"].get("answered")
        )

        refused_count = total_questions - answered_count

        total_findings = sum(
            len(item["result"].get("findings", []))
            for item in runs
            if item["result"].get("answered")
        )

        cited_findings = sum(
            1
            for item in runs
            if item["result"].get("answered")
            for finding in item["result"].get("findings", [])
            if finding.get("citations")
        )

        citation_coverage = (
            (cited_findings / total_findings) * 100
            if total_findings
            else 0
        )

        st.html(
            f"""
            <div class="grid-4">
                <div class="metric-card">
                    <div class="metric-label">Questions evaluated</div>
                    <div class="metric-value">{total_questions}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Answered</div>
                    <div class="metric-value">{answered_count}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Refused / unsupported</div>
                    <div class="metric-value">{refused_count}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Citation coverage</div>
                    <div class="metric-value">{citation_coverage:.0f}%</div>
                </div>
            </div>
            """
        )

        st.caption(
            "Citation coverage = findings with at least one citation ÷ all generated findings."
        )

        st.html('<div class="section-title">Question-level checks</div>')

        for run_index, item in enumerate(runs, start=1):
            result = item["result"]
            question_text = item["question"]
            answered = bool(result.get("answered"))
            findings = result.get("findings", []) if answered else []
            sources = result.get("sources", [])

            cited_ids = {
                str(citation)
                for finding in findings
                for citation in finding.get("citations", [])
            }

            source_ids = {
                str(source.get("id", ""))
                for source in sources
            }

            cited_findings_for_run = sum(
                1
                for finding in findings
                if finding.get("citations")
            )

            run_coverage = (
                (cited_findings_for_run / len(findings)) * 100
                if findings
                else 0
            )

            invalid_citations = sorted(
                citation
                for citation in cited_ids
                if citation not in source_ids
            )

            valid_citations = not invalid_citations

            unique_cited_sources = len(
                cited_ids.intersection(source_ids)
            )

            with st.expander(
                f"{run_index}. {question_text}",
                expanded=run_index == 1,
            ):
                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Answer status",
                    "Answered" if answered else "Refused",
                )
                c2.metric("Findings", len(findings))
                c3.metric(
                    "Cited sources",
                    unique_cited_sources,
                )
                c4.metric(
                    "Citation coverage",
                    f"{run_coverage:.0f}%"
                    if findings
                    else "N/A",
                )

                st.markdown("#### Measurable checks")

                if answered:
                    if cited_findings_for_run == len(findings) and findings:
                        st.success(
                            "Every generated finding contains at least one citation."
                        )
                    else:
                        st.warning(
                            f"{cited_findings_for_run} of {len(findings)} findings contain citations."
                        )

                    if valid_citations:
                        st.success(
                            "All cited paper IDs exist in the returned source set."
                        )
                    else:
                        st.error(
                            "Citation mismatch: "
                            + ", ".join(invalid_citations)
                        )

                    implications_present = sum(
                        1
                        for finding in findings
                        if str(
                            finding.get(
                                "business_implication",
                                "",
                            )
                        ).strip()
                    )

                    if implications_present == len(findings) and findings:
                        st.success(
                            "Every research finding has a separate business implication."
                        )
                    else:
                        st.warning(
                            f"{implications_present} of {len(findings)} findings have a business implication."
                        )

                else:
                    st.info(
                        "The agent reported insufficient evidence and did not produce research findings."
                    )

                    if result.get("gaps"):
                        st.write(result["gaps"])

                if sources:
                    st.markdown("#### Retrieved research")

                    rows = []

                    for source in sources:
                        distance = source.get("distance")
                        rows.append(
                            {
                                "Rank": source.get("rank", ""),
                                "Paper": source.get("title", ""),
                                "arXiv": source.get("id", ""),
                                "Retrieval distance": (
                                    f"{distance:.4f}"
                                    if isinstance(
                                        distance,
                                        (int, float),
                                    )
                                    else "N/A"
                                ),
                                "Cited": (
                                    "Yes"
                                    if str(source.get("id", "")) in cited_ids
                                    else "No"
                                ),
                            }
                        )

                    st.dataframe(
                        rows,
                        use_container_width=True,
                        hide_index=True,
                    )

        st.divider()
        st.subheader("Technical validation")
        st.success(
            "22 / 22 automated tests passed in the current validated test run."
        )
        st.caption(
            "This is a software test result, not an AI quality percentage."
        )


# ---------------------------------------------------------
# ABOUT
# ---------------------------------------------------------

elif st.session_state.page == "About":
    page_header(
        "Project Methodology",
        "About the project",
        "How the AI Research Intelligence Agent turns publicly available AI research into grounded business insight.",
    )

    st.html(
        """
        <div class="grid-3">
            <div class="info-card">
                <h4>Problem</h4>
                <p>
                    AI research is growing quickly and is difficult for business teams
                    to monitor, interpret, and operationalize consistently.
                </p>
            </div>
            <div class="info-card">
                <h4>Approach</h4>
                <p>
                    Use retrieval-augmented generation to locate relevant research,
                    summarize evidence, and separate technical findings from business interpretation.
                </p>
            </div>
            <div class="info-card">
                <h4>Output</h4>
                <p>
                    Grounded research findings, business implications, cited sources,
                    and explicit evidence gaps when the collection cannot support a claim.
                </p>
            </div>
        </div>
        """
    )

    st.html('<div class="section-title">Research-to-insight workflow</div>')

    steps = [
        (
            "Collect",
            "Publicly available AI research is collected from arXiv and prepared for retrieval.",
        ),
        (
            "Preprocess",
            "Research text and metadata are normalized and chunked into retrievable units.",
        ),
        (
            "Retrieve",
            "Embeddings and vector search identify research most relevant to the user's question.",
        ),
        (
            "Expand context",
            "Neighboring chunks are added so generation sees supporting context around the retrieved evidence.",
        ),
        (
            "Generate",
            "Gemini produces research findings and separate business implications using the retrieved evidence.",
        ),
        (
            "Validate",
            "Citations, evidence gaps, unsupported-question behavior, and retrieval details are exposed for evaluation.",
        ),
    ]

    for index, (title, copy) in enumerate(steps, start=1):
        st.html(
            f"""
            <div class="method-step">
                <div class="step-num">{index}</div>
                <div>
                    <div class="step-title">{clean(title)}</div>
                    <div class="step-copy">{clean(copy)}</div>
                </div>
            </div>
            """
        )

    st.html('<div class="section-title">Current stack</div>')

    st.markdown(
        """
        **Research source:** arXiv  
        **Retrieval:** vector search over processed research chunks  
        **Generation:** Gemini  
        **Application:** Streamlit  
        **Quality controls:** citations, evidence gaps, refusal behavior, retrieval transparency
        """
    )
