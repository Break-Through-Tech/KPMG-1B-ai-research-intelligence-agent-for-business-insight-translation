import base64
import html
import os
import sys
from pathlib import Path

import streamlit as st


# Project imports

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from generation import expand_neighbor_context, summarize
from retrieval import build_vector_store, load_chunks, search


# Page setup

st.set_page_config(
    page_title="AI Research Intelligence Agent",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Image helper

def image_to_base64(path):
    return base64.b64encode(
        Path(path).read_bytes()
    ).decode()


KPMG_LOGO = image_to_base64(
    ROOT / "static" / "kpmg-logo.png"
)

BTT_WATERMARK = image_to_base64(
    ROOT / "static" / "btt-watermark.png"
)


# Icons

def icon(name, size=24):
    return (
        f'<span class="icon icon-{name}" '
        f'style="width:{size}px;height:{size}px;"></span>'
    )


# Custom styles

st.html(
    """
    <style>

    :root {
        --navy: #071a37;
        --purple: #5b35f5;
        --text: #0d1d3a;
        --muted: #5f718d;
    }

    header[data-testid="stHeader"] {
        height: 0;
        background: transparent;
    }

    [data-testid="stToolbar"] {
        display: none;
    }

    #MainMenu,
    footer {
        display: none;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 88% -5%,
                rgba(110, 70, 255, 0.16),
                transparent 25rem
            ),
            radial-gradient(
                circle at 18% 105%,
                rgba(79, 115, 255, 0.12),
                transparent 25rem
            ),
            #fbfbfe;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 1.5rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
        padding-bottom: 3rem;
    }

    .top-wave-one {
        position: fixed;
        width: 430px;
        height: 150px;
        right: -60px;
        top: -55px;
        border-radius: 45% 55% 60% 40%;
        transform: rotate(8deg);
        background:
            linear-gradient(
                120deg,
                rgba(76, 145, 255, 0.30),
                rgba(123, 68, 255, 0.58)
            );
        pointer-events: none;
    }

    .top-wave-two {
        position: fixed;
        width: 340px;
        height: 115px;
        right: -20px;
        top: 25px;
        border-radius: 60% 40% 50% 50%;
        transform: rotate(-6deg);
        background:
            linear-gradient(
                110deg,
                rgba(118, 163, 255, 0.22),
                rgba(181, 103, 255, 0.30)
            );
        pointer-events: none;
    }

    .bottom-wave {
        position: fixed;
        width: 390px;
        height: 150px;
        left: 225px;
        bottom: -80px;
        border-radius: 55% 45% 0 0;
        transform: rotate(10deg);
        background:
            linear-gradient(
                90deg,
                rgba(75, 126, 255, 0.48),
                rgba(105, 61, 250, 0.25)
            );
        pointer-events: none;
    }

    .profile-circle {
        position: fixed;
        top: 18px;
        right: 22px;
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: #243b63;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 15px;
        z-index: 20;
        box-shadow: 0 4px 14px rgba(0,0,0,0.12);
    }

    section[data-testid="stSidebar"] {
        width: 250px !important;
        min-width: 250px !important;
        background:
            linear-gradient(
                180deg,
                #071832 0%,
                #0a2854 100%
            );
        border-right: none;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 0 !important;
    }

    [data-testid="stSidebarContent"] {
        padding-top: 0 !important;
    }

    [data-testid="stSidebarUserContent"] {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        padding: 0 16px 14px 16px !important;
        transform: translateY(-55px);
    }

    .side-brand {
        display: flex;
        align-items: center;
        gap: 9px;
        padding: 2px 2px 12px 2px;
        
        margin-bottom: 8px;
    }

    .logo-wrap {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .kpmg-logo-img {
        width: 74px;
        height: auto;
        display: block;
    }

    .brand-divider {
        width: 1px;
        height: 38px;
        background: rgba(255,255,255,0.22);
    }

    .brand-name {
        color: white;
        font-size: 12px;
        line-height: 1.25;
        font-weight: 650;
    }

    .nav-item {
        display: flex;
        align-items: center;
        gap: 13px;
        padding: 10px 14px;
        margin: 2px 0;
        border-radius: 10px;
        color: #eef3fb;
        font-size: 14px;
        font-weight: 520;
    }

    .nav-icon {
        width: 22px;
        height: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .nav-active {
        background:
            linear-gradient(
                90deg,
                #5531dd,
                #7249f3
            );
        box-shadow:
            0 5px 18px rgba(87, 46, 221, 0.38);
    }

    .side-agent {
        margin-top: auto;
        margin-bottom: 0px;
        transform: translateY(80px);

        border-radius: 16px;
        padding: 16px;
        color: white;

        background:
            radial-gradient(
                circle at 92% 100%,
                rgba(116, 51, 255, 0.78),
                transparent 42%
            ),
            linear-gradient(
                135deg,
                #193b72,
                #352884
            );

        border:
            1px solid rgba(135, 116, 255, 0.35);

        box-shadow:
            0 10px 25px rgba(0,0,0,0.15);
    }

    .sparkle {
        color: #7041ff;
        font-size: 26px;
        line-height: 1;
        margin-bottom: 10px;
    }

    .side-agent .sparkle {
        color: #c6adff;
    }

    .side-agent-title {
        font-weight: 750;
        font-size: 15px;
        margin-bottom: 7px;
    }

    .side-agent-copy {
        color: #d8dcf3;
        font-size: 13px;
        line-height: 1.45;
    }

    .hero {
        position: relative;
        overflow: hidden;
        text-align: center;
        padding: 30px 24px 34px;
        margin-bottom: 22px;
        border-radius: 26px;
        background:
            linear-gradient(
                180deg,
                rgba(248,247,255,0.78),
                rgba(250,249,255,0.96)
            );
    }

    .hero-watermark {
        position: absolute;
        width: 390px;
        right: 28px;
        top: 5px;
        opacity: 0.055;
        z-index: 0;
        pointer-events: none;
    }

    .hero-content {
        position: relative;
        z-index: 1;
    }

    .hero-chip {
        display: inline-block;
        padding: 8px 17px;
        border-radius: 30px;
        background: #f0ecff;
        color: #5327de;
        font-size: 12px;
        font-weight: 750;
        margin-bottom: 18px;
    }

    .hero-title {
        color: #0a1c3a;
        font-size: 48px;
        line-height: 1.08;
        letter-spacing: -1.8px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .hero-title span {
        color: #5732de;
    }

    .hero-subtitle {
        max-width: 760px;
        margin: auto;
        color: #536783;
        font-size: 16px;
        line-height: 1.55;
    }

    div[data-testid="stTextInput"] {
        position: relative;
    }

    div[data-testid="stTextInput"]::before {
        content: "⌕";
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 25px;
        color: #0d1d3a;
        z-index: 5;
        pointer-events: none;
    }

    div[data-testid="stTextInput"] input {
        height: 68px;
        border-radius: 15px;
        border: 1.5px solid #9c79ff;
        background-color: white;
        padding-left: 58px;
        font-size: 15px;
        box-shadow:
            0 7px 22px rgba(81, 48, 204, 0.07);
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #7248ef;
        box-shadow:
            0 0 0 1px #7248ef,
            0 7px 24px rgba(81, 48, 204, 0.09);
    }

    div[data-testid="stButton"] button {
        border-radius: 10px;
        min-height: 46px;
        font-weight: 650;
    }

    .stButton > button[kind="primary"] {
        min-height: 68px;
        border-radius: 14px;
        border: none;
        color: white;
        font-size: 15px;
        background:
            linear-gradient(
                90deg,
                #5731db,
                #7145eb
            );
        box-shadow:
            0 7px 20px rgba(83, 48, 216, 0.20);
    }

    .feature-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 25px;
        padding: 0 12px;
        margin-top: 18px;
        margin-bottom: 34px;
    }

    .feature {
        display: flex;
        align-items: center;
        gap: 13px;
    }

    .feature-circle {
        min-width: 48px;
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background:
            linear-gradient(
                145deg,
                #f0edff,
                #fafaff
            );
        box-shadow:
            0 4px 12px rgba(67, 48, 170, 0.08);
    }

    .feature-title {
        color: #0e1e3a;
        font-size: 14px;
        font-weight: 760;
    }

    .feature-copy {
        color: #64758c;
        font-size: 12px;
        margin-top: 2px;
    }

    .example-heading {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #0d1c38;
        font-size: 18px;
        font-weight: 780;
        margin-top: 5px;
        margin-bottom: 15px;
    }

    .example-card {
        position: relative;
        min-height: 190px;
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #e7e6ef;
        background:
            linear-gradient(
                145deg,
                #f0f6ff,
                #f4f7ff
            );
    }

    .example-card.purple-card {
        background:
            linear-gradient(
                145deg,
                #f8f4ff,
                #f2eeff
            );
    }

    .example-card.green-card {
        background:
            linear-gradient(
                145deg,
                #f1fbf9,
                #eaf9f4
            );
    }

    .example-icon {
        height: 38px;
        margin-bottom: 12px;
    }

    .example-icon .icon {
        width: 34px !important;
        height: 34px !important;
    }

    .example-title {
        color: #0d1d39;
        font-size: 14px;
        font-weight: 780;
        margin-bottom: 8px;
    }

    .example-copy {
        color: #425773;
        font-size: 12px;
        line-height: 1.45;
        padding-right: 7px;
    }

    .example-arrow {
        position: absolute;
        right: 16px;
        bottom: 12px;
        color: #5630df;
        font-size: 25px;
        font-weight: 600;
    }

    div[data-testid="stHorizontalBlock"] {
        align-items: center;
    }

    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        margin-top: -48px;
        float: right;
        width: 48px;
        min-height: 38px;
        background: transparent;
        border: none;
        color: transparent;
        box-shadow: none;
        z-index: 10;
        position: relative;
    }

    .right-card {
        background: rgba(255,255,255,0.94);
        border: 1px solid #ededf4;
        border-radius: 17px;
        padding: 19px;
        box-shadow:
            0 8px 30px rgba(23, 38, 66, 0.055);
        margin-bottom: 18px;
    }

    .right-heading {
        display: flex;
        align-items: center;
        gap: 9px;
        color: #0d1d39;
        font-size: 15px;
        font-weight: 780;
        margin-bottom: 12px;
    }

    .recent {
        display: flex;
        gap: 10px;
        padding: 11px 0;
        border-bottom: 1px solid #edf0f5;
    }

    .recent:last-child {
        border-bottom: none;
    }

    .recent-title {
        color: #1a2a45;
        font-size: 12px;
        font-weight: 650;
        line-height: 1.35;
    }

    .recent-time {
        color: #8b99ab;
        font-size: 11px;
        margin-top: 2px;
    }

    .build-card {
        padding: 21px 15px;
        text-align: center;
        border-radius: 15px;
        background:
            linear-gradient(
                145deg,
                #f5efff,
                #eae8ff
            );
    }

    .build-graphic {
        font-size: 38px;
        margin-bottom: 8px;
    }

    .build-title {
        color: #0d1d39;
        font-size: 15px;
        font-weight: 780;
        margin-bottom: 8px;
    }

    .build-copy {
        color: #576b85;
        font-size: 12px;
        line-height: 1.5;
    }

    .result-card {
        background: white;
        border: 1px solid #e7e8ef;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 13px;
        box-shadow:
            0 4px 18px rgba(15, 33, 60, 0.04);
    }

    .business-result {
        background:
            linear-gradient(
                145deg,
                #f7f4ff,
                #faf9ff
            );
        border-color: #e1dbfb;
    }

    .result-label {
        color: #5c3bd6;
        text-transform: uppercase;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .04em;
        margin-bottom: 8px;
    }

    .result-text {
        color: #334860;
        font-size: 15px;
        line-height: 1.65;
    }

    .icon {
        display: inline-block;
        background-color: #5b35f5;
        mask-repeat: no-repeat;
        mask-position: center;
        mask-size: contain;
        -webkit-mask-repeat: no-repeat;
        -webkit-mask-position: center;
        -webkit-mask-size: contain;
    }

    .icon-home-white {
        background-color: white;
        mask-image: url("/app/static/icons/home-white.svg");
        -webkit-mask-image: url("/app/static/icons/home-white.svg");
    }

    .icon-search-white {
        background-color: #e5ecf7;
        mask-image: url("/app/static/icons/search-white.svg");
        -webkit-mask-image: url("/app/static/icons/search-white.svg");
    }

    .icon-layers-white {
        background-color: #e5ecf7;
        mask-image: url("/app/static/icons/layers-white.svg");
        -webkit-mask-image: url("/app/static/icons/layers-white.svg");
    }

    .icon-clock-white {
        background-color: #e5ecf7;
        mask-image: url("/app/static/icons/clock-white.svg");
        -webkit-mask-image: url("/app/static/icons/clock-white.svg");
    }

    .icon-chart-white {
        background-color: #e5ecf7;
        mask-image: url("/app/static/icons/chart-white.svg");
        -webkit-mask-image: url("/app/static/icons/chart-white.svg");
    }

    .icon-info-white {
        background-color: #e5ecf7;
        mask-image: url("/app/static/icons/info-white.svg");
        -webkit-mask-image: url("/app/static/icons/info-white.svg");
    }

    .icon-file-purple {
        background-color: #6238f6;
        mask-image: url("/app/static/icons/file-purple.svg");
        -webkit-mask-image: url("/app/static/icons/file-purple.svg");
    }

    .icon-target-purple {
        background-color: #6238f6;
        mask-image: url("/app/static/icons/target-purple.svg");
        -webkit-mask-image: url("/app/static/icons/target-purple.svg");
    }

    .icon-layers-purple {
        background-color: #643bfa;
        mask-image: url("/app/static/icons/layers-purple.svg");
        -webkit-mask-image: url("/app/static/icons/layers-purple.svg");
    }

    .icon-cpu-blue {
        background-color: #2878f5;
        mask-image: url("/app/static/icons/cpu-blue.svg");
        -webkit-mask-image: url("/app/static/icons/cpu-blue.svg");
    }

    .icon-bars-green {
        background-color: #12b98a;
        mask-image: url("/app/static/icons/bars-green.svg");
        -webkit-mask-image: url("/app/static/icons/bars-green.svg");
    }

    .icon-monitor {
        background-color: #6238f6;
        mask-image: url("/app/static/icons/monitor.svg");
        -webkit-mask-image: url("/app/static/icons/monitor.svg");
    }

    .icon-clock {
        background-color: #6238f6;
        mask-image: url("/app/static/icons/clock.svg");
        -webkit-mask-image: url("/app/static/icons/clock.svg");
    }

    </style>
    """
)


# Background decoration

st.html(
    """
    <div class="top-wave-one"></div>
    <div class="top-wave-two"></div>
    <div class="bottom-wave"></div>
    """
)


# Profile

st.html(
    """
    <div class="profile-circle">
        M
    </div>
    """
)


# Load research engine

@st.cache_resource(show_spinner=False)
def load_engine():
    chunks = load_chunks("arxiv")

    collection, model = build_vector_store(
        chunks,
        "arxiv",
    )

    return chunks, collection, model


# Run research question

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


# Helper functions

def clean(text):
    return html.escape(str(text or ""))


def choose_example(question):
    st.session_state.question = question


# Session state

if "question" not in st.session_state:
    st.session_state.question = ""

if "history" not in st.session_state:
    st.session_state.history = []


# Sidebar

with st.sidebar:

    st.html(
        f"""
        <div class="side-brand">

            <div class="logo-wrap">
                <img
                    src="data:image/png;base64,{KPMG_LOGO}"
                    class="kpmg-logo-img"
                    alt="KPMG"
                >
            </div>

            <div class="brand-divider"></div>

            <div class="brand-name">
                Break Through<br>
                Tech AI Studio
            </div>

        </div>

        <div class="nav-item nav-active">
            <div class="nav-icon">
                {icon("home-white", 21)}
            </div>
            <span>Home</span>
        </div>

        <div class="nav-item">
            <div class="nav-icon">
                {icon("search-white", 21)}
            </div>
            <span>Research</span>
        </div>

        <div class="nav-item">
            <div class="nav-icon">
                {icon("layers-white", 21)}
            </div>
            <span>Saved Insights</span>
        </div>

        <div class="nav-item">
            <div class="nav-icon">
                {icon("clock-white", 21)}
            </div>
            <span>History</span>
        </div>

        <div class="nav-item">
            <div class="nav-icon">
                {icon("chart-white", 21)}
            </div>
            <span>Evaluation</span>
        </div>

        <div class="nav-item">
            <div class="nav-icon">
                {icon("info-white", 21)}
            </div>
            <span>About</span>
        </div>

        <div class="side-agent">

            <div class="sparkle">
                ✦
            </div>

            <div class="side-agent-title">
                AI Research Agent
            </div>

            <div class="side-agent-copy">
                Turn research into<br>
                business insights.
            </div>

        </div>
        """
    )


# Main layout

main_col, right_col = st.columns(
    [3.65, 1.1],
    gap="large",
)


# Main section

with main_col:

    # Hero

    st.html(
        f"""
        <div class="hero">

            <img
                src="data:image/png;base64,{BTT_WATERMARK}"
                class="hero-watermark"
                alt=""
            >

            <div class="hero-content">

                <div class="hero-chip">
                    KPMG × Break Through Tech AI Studio
                </div>

                <div class="hero-title">
                    AI Research
                    <span>Intelligence Agent</span>
                </div>

                <div class="hero-subtitle">
                    Turn AI research into clear business insights with grounded
                    findings, practical implications, and source citations.
                </div>

            </div>

        </div>
        """
    )


    # Search bar

    search_col, ask_col = st.columns(
        [5.7, 1.3],
        gap="small",
    )

    with search_col:
        question = st.text_input(
            "Research question",
            key="question",
            placeholder="Ask a business or research question...",
            label_visibility="collapsed",
        )

    with ask_col:
        ask_button = st.button(
            "✦ Ask Agent",
            type="primary",
            use_container_width=True,
        )


    # Feature row

    st.html(
        f"""
        <div class="feature-row">

            <div class="feature">

                <div class="feature-circle">
                    {icon("file-purple", 25)}
                </div>

                <div>
                    <div class="feature-title">
                        Research Findings
                    </div>

                    <div class="feature-copy">
                        Evidence from academic papers
                    </div>
                </div>

            </div>

            <div class="feature">

                <div class="feature-circle">
                    {icon("target-purple", 25)}
                </div>

                <div>
                    <div class="feature-title">
                        Business Implications
                    </div>

                    <div class="feature-copy">
                        Real-world impact and value
                    </div>
                </div>

            </div>

            <div class="feature">

                <div class="feature-circle">
                    {icon("layers-purple", 25)}
                </div>

                <div>
                    <div class="feature-title">
                        Cited Sources
                    </div>

                    <div class="feature-copy">
                        Links to original research
                    </div>
                </div>

            </div>

        </div>
        """
    )


    # Example heading

    st.html(
        """
        <div class="example-heading">
            <span class="sparkle">✦</span>
            Try an example question
        </div>
        """
    )


    # Example cards

    example1, example2, example3 = st.columns(3)


    with example1:

        st.html(
            f"""
            <div class="example-card">

                <div class="example-icon">
                    {icon("cpu-blue", 34)}
                </div>

                <div class="example-title">
                    AI model cost & capability
                </div>

                <div class="example-copy">
                    How can a company choose between cheaper
                    and more capable AI models while controlling cost?
                </div>

                <div class="example-arrow">
                    →
                </div>

            </div>
            """
        )

        st.button(
            "Select",
            key="cost_question",
            on_click=choose_example,
            args=(
                "How can a company choose between cheaper and more capable AI models while controlling cost?",
            ),
            use_container_width=True,
        )


    with example2:

        st.html(
            f"""
            <div class="example-card purple-card">

                <div class="example-icon">
                    {icon("layers-purple", 34)}
                </div>

                <div class="example-title">
                    Workflow knowledge
                </div>

                <div class="example-copy">
                    How can organizations turn recorded computer activity
                    into reusable workflow knowledge?
                </div>

                <div class="example-arrow">
                    →
                </div>

            </div>
            """
        )

        st.button(
            "Select",
            key="workflow_question",
            on_click=choose_example,
            args=(
                "How can organizations turn recorded computer activity into reusable workflow knowledge?",
            ),
            use_container_width=True,
        )


    with example3:

        st.html(
            f"""
            <div class="example-card green-card">

                <div class="example-icon">
                    {icon("bars-green", 34)}
                </div>

                <div class="example-title">
                    AI algorithm improvement
                </div>

                <div class="example-copy">
                    How could AI agents help a company improve algorithms
                    instead of only optimizing hardware performance?
                </div>

                <div class="example-arrow">
                    →
                </div>

            </div>
            """
        )

        st.button(
            "Select",
            key="algorithm_question",
            on_click=choose_example,
            args=(
                "How could AI agents help a company improve algorithms instead of only optimizing hardware performance?",
            ),
            use_container_width=True,
        )


    # Run research agent

    if ask_button:

        question_text = question.strip()

        if not question_text:

            st.warning(
                "Please enter a question."
            )

        else:

            try:

                with st.spinner(
                    "Searching research and preparing the answer..."
                ):

                    result = ask_agent(
                        question_text
                    )

                st.session_state.result = result

                if question_text not in st.session_state.history:

                    st.session_state.history.insert(
                        0,
                        question_text,
                    )

                st.session_state.history = (
                    st.session_state.history[:5]
                )

            except Exception as error:

                st.error(
                    "Something went wrong while running the research agent."
                )

                with st.expander(
                    "Technical details"
                ):
                    st.code(str(error))


    # Research results

    result = st.session_state.get(
        "result"
    )

    if result:

        st.divider()

        st.subheader(
            "Research Response"
        )

        st.caption(
            result["question"]
        )

        if result["answered"]:

            for number, finding in enumerate(
                result["findings"],
                start=1,
            ):

                st.html(
                    f"""
                    <div class="result-card">

                        <div class="result-label">
                            Research Finding {number}
                        </div>

                        <div class="result-text">
                            {clean(finding["statement"])}
                        </div>

                    </div>
                    """
                )

                st.html(
                    f"""
                    <div class="result-card business-result">

                        <div class="result-label">
                            Business Implication
                        </div>

                        <div class="result-text">
                            {clean(
                                finding["business_implication"]
                            )}
                        </div>

                    </div>
                    """
                )


            # Coverage gaps

            if result.get("gaps"):

                st.subheader(
                    "Coverage / Gaps"
                )

                st.info(
                    result["gaps"]
                )


            # Sources

            st.subheader(
                "Sources"
            )

            cited_ids = {
                citation
                for finding in result["findings"]
                for citation in finding["citations"]
            }

            for source in result["sources"]:

                if source["id"] not in cited_ids:
                    continue

                st.html(
                    f"""
                    <div class="result-card">

                        <div class="result-label">
                            Cited Research
                        </div>

                        <div class="result-text">

                            <strong>
                                {clean(source["title"])}
                            </strong>

                            <br>

                            arXiv {clean(source["id"])}

                        </div>

                    </div>
                    """
                )

                st.link_button(
                    "View Paper",
                    source["url"],
                )


        else:

            st.warning(
                "The current research collection does not contain enough evidence to answer this question reliably."
            )

            if result.get("gaps"):

                st.subheader(
                    "What is missing"
                )

                st.write(
                    result["gaps"]
                )


        # Research details

        with st.expander(
            "Research details"
        ):

            for source in result["sources"]:

                distance = source.get(
                    "distance"
                )

                if isinstance(
                    distance,
                    (int, float),
                ):
                    distance_text = f"{distance:.4f}"

                else:
                    distance_text = "N/A"

                st.write(
                    f"**Rank {source['rank']} — "
                    f"{source['title']}**"
                )

                st.caption(
                    f"arXiv {source['id']} · "
                    f"Retrieval distance {distance_text}"
                )


# Right panel

with right_col:

    # Recent questions

    history = st.session_state.history[:3]

    if history:

        recent_items = ""

        recent_icons = [
            "monitor",
            "file-purple",
            "layers-purple",
        ]

        for index, recent in enumerate(history):

            icon_name = recent_icons[
                min(index, len(recent_icons) - 1)
            ]

            recent_items += f"""
            <div class="recent">

                <div>
                    {icon(icon_name, 20)}
                </div>

                <div>

                    <div class="recent-title">
                        {clean(recent)}
                    </div>

                    <div class="recent-time">
                        Recent
                    </div>

                </div>

            </div>
            """

    else:

        recent_items = """
        <div class="recent">
            <div>
                <div class="recent-title">
                    Your recent questions will show here.
                </div>
            </div>
        </div>
        """


    st.html(
        f"""
        <div class="right-card">

            <div class="right-heading">
                {icon("clock", 21)}
                Recent Questions
            </div>

            {recent_items}

        </div>
        """
    )


    # Build on AI research

    st.html(
        """
        <div class="right-card">

            <div class="build-card">

                <div class="build-graphic">
                    🔎
                </div>

                <div class="build-title">
                    Build on AI Research
                </div>

                <div class="build-copy">
                    Explore findings, identify business
                    opportunities, and discover gaps
                    for future work.
                </div>

            </div>

        </div>
        """
    )