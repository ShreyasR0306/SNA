
import streamlit as st
import pandas as pd
import subprocess
import sys
import io
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER

import streamlit.components.v1 as components


# =========================================
# PROJECT PATHS
# =========================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

ORIGINAL_RESULTS_PATH = OUTPUT_DIR / "influencer_results.csv"
ENHANCED_RESULTS_PATH = OUTPUT_DIR / "enhanced_influencer_results.csv"
COMMUNITY_TOP_PATH = OUTPUT_DIR / "community_top_influencers.csv"
BRIDGE_USERS_PATH = OUTPUT_DIR / "bridge_users.csv"
COMMUNITY_SIZES_PATH = OUTPUT_DIR / "community_sizes.csv"

GRAPH_PATH = OUTPUT_DIR / "largest_community.png"
INTERACTIVE_GRAPH_PATH = OUTPUT_DIR / "interactive_network.html"
REPORT_PATH = OUTPUT_DIR / "agent_report.txt"
SIMULATION_RESULTS_PATH = OUTPUT_DIR / "latest_diffusion_simulation.json"


def render_topic_card(title, description, eyebrow, level=2):

    heading_tag = f"h{level}"

    st.markdown(
        f"""
        <article class="topic-card">
            <span class="topic-card-mark" aria-hidden="true">✦</span>
            <div class="topic-card-copy">
                <span class="topic-card-eyebrow">{escape(str(eyebrow))}</span>
                <{heading_tag}>{escape(str(title))}</{heading_tag}>
                <p>{escape(str(description))}</p>
            </div>
        </article>
        """,
        unsafe_allow_html=True
    )


# =========================================
# PDF GENERATION
# =========================================

def create_pdf(report_text):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=17,
        leading=22,
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=5
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        spaceAfter=5
    )

    story = [
        Paragraph(
            "FACEBOOK SOCIAL NETWORK ANALYSIS",
            title_style
        ),
        Paragraph(
            "Multi-Agent AI Project Report",
            styles["Heading2"]
        ),
        Spacer(1, 12),
        HRFlowable(width="100%"),
        Spacer(1, 12)
    ]

    for raw_line in report_text.splitlines():

        line = raw_line.strip()

        if not line:
            story.append(Spacer(1, 4))
            continue

        clean_line = re.sub(r"^#{1,6}\s*", "", line)
        clean_line = clean_line.replace("**", "")
        clean_line = clean_line.replace("__", "")
        clean_line = clean_line.replace("`", "")

        clean_line = clean_line.encode(
            "ascii",
            errors="replace"
        ).decode("ascii")

        safe_line = escape(clean_line)

        if raw_line.strip().startswith("#") or re.match(
            r"^\d+[\.\)]\s+",
            clean_line
        ):

            story.append(
                Paragraph(safe_line, heading_style)
            )

        else:

            story.append(
                Paragraph(safe_line, body_style)
            )

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# =========================================
# PAGE CONFIGURATION
# =========================================

st.set_page_config(
    page_title="Facebook Influencer Detection",
    page_icon="🌐",
    layout="wide"
)

_theme_spacer, theme_control = st.columns([8, 2])

with theme_control:
    dark_mode = st.toggle(
        "Dark theme",
        key="dashboard_dark_theme"
    )

st.markdown(
    """
    <style>
    :root {
        --ink: #17233f;
        --muted: #64748b;
        --accent: #536dfe;
        --accent-deep: #3649c9;
        --surface: rgba(255, 255, 255, 0.82);
        --line: rgba(100, 116, 139, 0.16);
    }

    html {
        scroll-behavior: smooth;
    }

    [data-testid="stMain"] {
        scroll-behavior: smooth !important;
        scroll-padding-top: 6rem;
    }

    #network-story,
    #network-overview,
    #influencer-rankings,
    #community-analysis,
    #bridge-users,
    #cross-community,
    #diffusion-simulation,
    #ai-analysis {
        scroll-margin-top: 6rem;
    }

    body,
    .stApp {
        color: var(--ink);
        background:
            radial-gradient(ellipse at 9% 5%, rgba(114, 139, 255, 0.14), transparent 32rem),
            radial-gradient(ellipse at 94% 22%, rgba(69, 211, 199, 0.12), transparent 30rem),
            #f5f7fc;
    }

    [data-testid="stHeader"] {
        background: rgba(245, 247, 252, 0.78);
        backdrop-filter: blur(14px);
    }

    [data-testid="stMainBlockContainer"] {
        width: 100%;
        max-width: 1540px;
        margin-inline: auto;
        padding: 1.25rem clamp(1rem, 3vw, 2.5rem) 4rem;
        box-sizing: border-box;
    }

    [data-testid="stHeader"] {
        display: none;
    }

    [data-testid="stMain"]::before {
        content: "";
        position: sticky;
        z-index: 9999;
        top: 0;
        display: block;
        width: 100%;
        height: 3px;
        margin-bottom: -3px;
        pointer-events: none;
        transform: scaleX(0);
        transform-origin: left center;
        background: linear-gradient(90deg, #536dfe, #46d3c7, #a855f7);
    }

    @supports (animation-timeline: scroll()) {
        [data-testid="stMain"]::before {
            animation: reading-progress linear both;
            animation-timeline: scroll(nearest block);
        }
    }

    @keyframes reading-progress {
        to { transform: scaleX(1); }
    }

    .hero-shell {
        position: relative;
        display: flex;
        min-height: 390px;
        align-items: center;
        justify-content: space-between;
        gap: 2rem;
        overflow: hidden;
        margin-top: 5.5rem;
        padding: clamp(2rem, 5vw, 4rem);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 30px;
        color: #f8faff;
        background:
            radial-gradient(circle at 84% 8%, rgba(91, 225, 214, 0.3), transparent 19rem),
            linear-gradient(122deg, #172447 0%, #293b7b 58%, #5269dc 100%);
        box-shadow: 0 26px 70px rgba(37, 55, 119, 0.2);
        animation: hero-arrive 800ms cubic-bezier(.2, .75, .25, 1) both;
    }

    .hero-shell::after {
        position: absolute;
        top: -90px;
        right: 12%;
        width: 260px;
        height: 260px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 50%;
        content: "";
        animation: orbit-drift 16s ease-in-out infinite alternate;
    }

    .hero-shell::before {
        position: absolute;
        inset: 0;
        background-image:
            radial-gradient(circle at 78% 30%, rgba(255,255,255,.3) 1px, transparent 2px),
            radial-gradient(circle at 91% 66%, rgba(159,241,227,.6) 1px, transparent 2px),
            linear-gradient(110deg, transparent 56%, rgba(255,255,255,.05) 56.2%, transparent 56.6%);
        background-size: 58px 58px, 83px 83px, 100% 100%;
        content: "";
        opacity: .48;
        pointer-events: none;
    }

    .hero-copy {
        position: relative;
        z-index: 1;
        max-width: 730px;
    }

    .hero-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: .55rem;
        margin-bottom: 1rem;
        color: #a9f4e9;
        font-size: .75rem;
        font-weight: 750;
        letter-spacing: .16em;
        text-transform: uppercase;
    }

    .hero-eyebrow::before {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #64e5d1;
        box-shadow: 0 0 18px #64e5d1;
        content: "";
    }

    .hero-title {
        margin: 0;
        color: transparent;
        font-size: clamp(2.2rem, 5vw, 4.25rem);
        font-weight: 780;
        letter-spacing: -.055em;
        line-height: 1.02;
        background-image:
            linear-gradient(110deg, #ffffff 4%, #9ff1e3 28%, #ffffff 52%, #b7c8ff 76%, #ffffff 96%),
            repeating-linear-gradient(135deg, rgba(255,255,255,.28) 0 1px, transparent 1px 9px);
        background-size: 220% 220%;
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: masked-title-drift 8s ease-in-out infinite alternate;
    }

    .hero-title span {
        color: transparent;
        background: inherit;
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-description {
        max-width: 620px;
        margin: 1.1rem 0 0;
        color: rgba(241, 245, 255, .82);
        font-size: 1.05rem;
        line-height: 1.7;
    }

    .hero-art {
        position: relative;
        z-index: 1;
        flex: 0 0 190px;
        width: 190px;
        height: 190px;
        border: 1px solid rgba(255, 255, 255, .2);
        border-radius: 50%;
        background: radial-gradient(circle, rgba(91, 225, 214, .18), rgba(255,255,255,.025) 68%);
        animation: float-gently 6s ease-in-out infinite;
    }

    .hero-art::before,
    .hero-art::after {
        position: absolute;
        inset: 20px;
        border: 1px solid rgba(255, 255, 255, .18);
        border-radius: 50%;
        content: "";
    }

    .hero-art::after {
        inset: 45px;
        border-color: rgba(159, 241, 227, .48);
    }

    .hero-node {
        position: absolute;
        z-index: 2;
        width: 13px;
        height: 13px;
        border: 2px solid rgba(255, 255, 255, .9);
        border-radius: 50%;
        background: #64e5d1;
        box-shadow: 0 0 20px rgba(100, 229, 209, .8);
    }

    .hero-node:nth-child(1) { top: 17px; left: 80px; }
    .hero-node:nth-child(2) { top: 57px; right: 17px; animation-delay: .4s; }
    .hero-node:nth-child(3) { right: 32px; bottom: 28px; animation-delay: .9s; }
    .hero-node:nth-child(4) { bottom: 13px; left: 70px; animation-delay: .2s; }
    .hero-node:nth-child(5) { top: 68px; left: 14px; animation-delay: .7s; }
    .hero-node:nth-child(6) { top: 88px; left: 88px; width: 17px; height: 17px; background: #fff; }

    .section-nav {
        position: fixed;
        z-index: 9998;
        top: .75rem;
        left: 50%;
        display: flex;
        width: calc(100vw - 2rem);
        max-width: 1540px;
        flex-wrap: nowrap;
        justify-content: center;
        gap: .55rem;
        margin: 0;
        padding: .7rem 11rem .7rem .7rem;
        overflow-x: auto;
        border: 1px solid rgba(100, 116, 139, .14);
        border-radius: 18px;
        background: rgba(255, 255, 255, .78);
        box-shadow: 0 8px 26px rgba(30, 48, 91, .07);
        backdrop-filter: blur(18px);
        box-sizing: border-box;
        transform: translateX(-50%);
    }

    .section-nav a {
        flex: 0 0 auto;
        padding: .55rem .85rem;
        border-radius: 12px;
        color: #42516f !important;
        font-size: .85rem;
        font-weight: 650;
        text-decoration: none !important;
        white-space: nowrap;
        transition: color .2s ease, background .2s ease, transform .2s ease;
    }

    .section-nav a:hover {
        transform: translateY(-2px);
        color: #fff !important;
        background: #536dfe;
    }

    @media (min-width: 701px) and (max-width: 1100px) {
        .section-nav {
            gap: .25rem;
            padding: .55rem 9.5rem .55rem .55rem;
        }

        .section-nav a {
            padding: .48rem .58rem;
            font-size: .78rem;
        }
    }

    @media (min-width: 701px) and (max-height: 800px) {
        .hero-shell {
            min-height: clamp(290px, calc(100svh - 170px), 390px);
            margin-top: 4.75rem;
            padding: clamp(1.5rem, 4vh, 3rem) clamp(1.5rem, 4vw, 3.5rem);
        }
    }

    .topic-card {
        position: relative;
        display: grid;
        grid-template-columns: 2.8rem minmax(0, 1fr);
        align-items: start;
        gap: 1rem;
        margin: 1.1rem 0 1.35rem;
        padding: 1.15rem 1.3rem;
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 20px;
        background: var(--surface);
        box-shadow: 0 12px 30px rgba(27, 44, 86, .07);
        transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
    }

    .topic-card::after {
        position: absolute;
        top: 0;
        right: 0;
        width: 42%;
        height: 100%;
        background: linear-gradient(105deg, transparent, rgba(83,109,254,.045));
        content: "";
        pointer-events: none;
    }

    .topic-card:hover {
        transform: translateY(-3px);
        border-color: rgba(83,109,254,.34);
        box-shadow: 0 18px 38px rgba(27, 44, 86, .12);
    }

    .topic-card-mark {
        display: grid;
        width: 2.7rem;
        height: 2.7rem;
        place-items: center;
        border-radius: 15px;
        color: #fff;
        background: linear-gradient(140deg, #536dfe, #46d3c7);
        box-shadow: 0 8px 18px rgba(83,109,254,.22);
        font-size: 1.15rem;
    }

    .topic-card-copy {
        position: relative;
        z-index: 1;
        min-width: 0;
    }

    .topic-card-eyebrow {
        display: block;
        margin: 0 0 .3rem;
        color: #536dfe;
        font-size: .68rem;
        font-weight: 780;
        letter-spacing: .13em;
        text-transform: uppercase;
    }

    .topic-card h2,
    .topic-card h3 {
        margin: 0 !important;
        color: var(--ink) !important;
        font-size: clamp(1.15rem, 2vw, 1.55rem);
        font-weight: 760;
        line-height: 1.25;
    }

    .topic-card h3 {
        font-size: clamp(1.02rem, 1.6vw, 1.25rem);
    }

    .topic-card p {
        margin: .45rem 0 0;
        color: var(--muted) !important;
        font-size: .94rem;
        line-height: 1.65;
    }

    .scroll-placard {
        position: relative;
        display: grid;
        min-height: 170vh;
        grid-template-columns: minmax(0, 1fr) minmax(280px, .9fr);
        align-items: start;
        gap: clamp(2rem, 7vw, 7rem);
        margin: 3rem 0 4rem;
        padding: clamp(4rem, 10vh, 7rem) clamp(1.5rem, 6vw, 6rem);
        overflow: clip;
        border: 1px solid var(--line);
        border-radius: 30px;
        background:
            radial-gradient(circle at 10% 18%, rgba(83,109,254,.13), transparent 22rem),
            radial-gradient(circle at 90% 82%, rgba(70,211,199,.12), transparent 24rem),
            var(--surface);
        view-timeline-name: --placard-scroll;
        view-timeline-axis: block;
    }

    .placard-copy {
        position: sticky;
        top: 20vh;
        align-self: start;
        max-width: 620px;
        padding-top: 2rem;
    }

    .placard-kicker {
        color: #536dfe;
        font-size: .76rem;
        font-weight: 780;
        letter-spacing: .15em;
        text-transform: uppercase;
    }

    .placard-copy h2 {
        margin: .9rem 0 1rem !important;
        font-size: clamp(2rem, 4vw, 3.25rem);
        line-height: 1.08;
    }

    .placard-copy p {
        color: var(--muted);
        font-size: 1.05rem;
        line-height: 1.75;
    }

    .placard-hint {
        display: inline-flex;
        align-items: center;
        gap: .6rem;
        margin-top: 1rem;
        padding: .7rem 1rem;
        border: 1px solid var(--line);
        border-radius: 999px;
        color: var(--muted);
        background: var(--surface);
        font-size: .82rem;
        font-weight: 650;
    }

    .placard-hint::before {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #46d3c7;
        box-shadow: 0 0 0 5px rgba(70,211,199,.14);
        content: "";
    }

    .placard-card-wrap {
        position: sticky;
        top: max(1rem, calc((100vh - 330px) / 2));
        width: min(100%, 370px);
        height: 330px;
        align-self: start;
        justify-self: center;
        perspective: 1300px;
    }

    .placard-card-inner,
    .placard-card-face {
        position: absolute;
        inset: 0;
        border-radius: 26px;
    }

    .placard-card-inner {
        transform-style: preserve-3d;
        transform: rotateY(0deg);
        transition: transform 900ms cubic-bezier(.22, 1, .36, 1);
        will-change: transform;
    }

    .placard-card-inner.is-flipped {
        transform: rotateY(180deg);
    }

    .placard-card-face {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        overflow: hidden;
        padding: 1.6rem;
        border: 1px solid rgba(255,255,255,.26);
        color: #f7f9ff;
        background:
            radial-gradient(circle at 85% 12%, rgba(95,230,212,.28), transparent 13rem),
            linear-gradient(145deg, #172447, #344a91 72%, #536dfe);
        box-shadow: 0 28px 70px rgba(31,49,111,.23);
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
    }

    .placard-card-face--back {
        position: absolute;
        transform: rotateY(180deg);
        background:
            radial-gradient(circle at 8% 90%, rgba(95,230,212,.25), transparent 14rem),
            linear-gradient(145deg, #1a2b58, #253970 65%, #315c80);
    }

    .placard-card-label {
        color: #a9f4e9;
        font-size: .72rem;
        font-weight: 750;
        letter-spacing: .14em;
        text-transform: uppercase;
    }

    .placard-card-number {
        display: block;
        margin: .3rem 0;
        color: #fff;
        font-size: clamp(3rem, 7vw, 4.8rem);
        font-weight: 800;
        letter-spacing: -.07em;
        line-height: 1;
    }

    .placard-card-caption {
        color: rgba(241,245,255,.8);
        font-size: .9rem;
        line-height: 1.55;
    }

    .placard-network-art {
        width: 100%;
        max-height: 110px;
        opacity: .9;
    }

    .placard-card-face--back h3 {
        margin: .8rem 0;
        color: #fff;
        font-size: 1.45rem;
    }

    .placard-card-face--back p {
        color: rgba(241,245,255,.86);
        font-size: .96rem;
        line-height: 1.7;
    }

    .placard-scroll-label {
        color: #a9f4e9;
        font-size: .76rem;
        font-weight: 700;
        letter-spacing: .08em;
    }

    h1, h2, h3 {
        color: var(--ink);
        letter-spacing: -.035em;
    }

    h2 {
        margin-top: 1.2rem !important;
        font-weight: 750 !important;
    }

    [data-testid="stMetric"] {
        min-height: 110px;
        padding: 1rem 1.2rem;
        border: 1px solid rgba(100, 116, 139, .14);
        border-radius: 20px;
        background: var(--surface);
        box-shadow: 0 10px 28px rgba(35, 53, 96, .07);
        transition: transform .25s ease, box-shadow .25s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 34px rgba(35, 53, 96, .12);
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] p {
        color: #53617b !important;
        font-weight: 650 !important;
    }

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] div {
        color: #17233f !important;
        font-weight: 780 !important;
        letter-spacing: -.035em;
    }

    [data-testid="stDataFrame"],
    [data-testid="stAlert"],
    [data-testid="stExpander"] {
        overflow: hidden;
        border: 1px solid rgba(100, 116, 139, .14);
        border-radius: 18px;
        background: rgba(255, 255, 255, .82);
    }

    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        border: 0;
        border-radius: 13px;
        font-weight: 700;
        transition: transform .2s ease, box-shadow .2s ease;
    }

    div[data-testid="stButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(59, 78, 177, .16);
    }

    .st-key-ai_generated_report table {
        width: 100%;
        overflow: hidden;
        border: 1px solid #dfe5f5 !important;
        border-collapse: separate !important;
        border-spacing: 0;
        border-radius: 16px !important;
        background: #fff;
        box-shadow: 0 12px 30px rgba(35, 53, 96, .09);
        font-size: .93rem;
    }

    .st-key-ai_generated_report thead th {
        padding: .9rem 1rem !important;
        border: 0 !important;
        color: #fff !important;
        background: linear-gradient(110deg, #27376e, #536dfe) !important;
        font-weight: 750 !important;
    }

    .st-key-ai_generated_report thead th * {
        color: #fff !important;
    }

    .st-key-ai_generated_report tbody td {
        padding: .8rem 1rem !important;
        border-bottom: 1px solid #edf0f7 !important;
        color: #263451 !important;
        background: #fff;
        transition: background-color .18s ease;
    }

    .st-key-ai_generated_report tbody tr:nth-child(even) td {
        background: #f5f7ff;
    }

    .st-key-ai_generated_report tbody tr:hover td {
        background: #e9edff !important;
    }

    @keyframes hero-arrive {
        from { opacity: 0; transform: translateY(18px) scale(.99); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    @keyframes float-gently {
        0%, 100% { transform: translateY(0) rotate(-4deg); }
        50% { transform: translateY(-10px) rotate(4deg); }
    }

    @keyframes orbit-drift {
        from { transform: translate(0, 0) scale(.96); }
        to { transform: translate(24px, 18px) scale(1.05); }
    }

    @keyframes masked-title-drift {
        from { background-position: 0% 40%; }
        to { background-position: 100% 60%; }
    }

    @supports (animation-timeline: view()) {
        [data-testid="stMain"] h2,
        [data-testid="stMain"] h3,
        [data-testid="stMain"] h4,
        [data-testid="stMain"] [data-testid="stMetric"],
        [data-testid="stMain"] [data-testid="stDataFrame"],
        .st-key-ai_generated_report table {
            animation: blur-text-on-scroll 900ms cubic-bezier(.2, .75, .25, 1) both;
            animation-timeline: view(block);
            animation-range: entry 0% entry 44%;
        }

        @keyframes blur-text-on-scroll {
            from { opacity: .18; filter: blur(9px); transform: translateY(30px); }
            to { opacity: 1; filter: blur(0); transform: translateY(0); }
        }
    }

    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"] {
            width: 100%;
            padding: 1rem .5rem 3rem;
        }

        .hero-shell {
            min-height: 0;
            margin-top: 5rem;
            padding: 2rem 1.4rem;
            border-radius: 22px;
        }

        .hero-art {
            display: none;
        }

        .section-nav {
            top: .45rem;
            width: calc(100vw - 1rem);
            max-width: none;
            justify-content: flex-start;
            gap: .15rem;
            padding: .4rem 8.5rem .4rem .4rem;
        }

        .section-nav a {
            padding: .45rem .55rem;
            font-size: .74rem;
        }

        .scroll-placard {
            min-height: 185vh;
            grid-template-columns: 1fr;
            gap: 2rem;
            padding: 2.5rem 1.25rem;
            border-radius: 22px;
        }

        .topic-card {
            grid-template-columns: 2.4rem minmax(0, 1fr);
            gap: .75rem;
            padding: 1rem;
            border-radius: 17px;
        }

        .topic-card-mark {
            width: 2.35rem;
            height: 2.35rem;
            border-radius: 13px;
        }

        .placard-copy {
            position: relative;
            top: auto;
            padding-top: 0;
        }

        .placard-card-wrap {
            top: max(1rem, calc((100vh - 300px) / 2));
            width: min(100%, 340px);
            height: 300px;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        html { scroll-behavior: auto; }
        [data-testid="stMain"] { scroll-behavior: auto !important; }
        *, *::before, *::after {
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: .01ms !important;
        }
        [data-testid="stAppViewContainer"]::before { display: none; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

light_theme = """
:root {
    color-scheme: light;
    --page-bg: #f5f7fc;
    --surface: rgba(255,255,255,.84);
    --surface-solid: #ffffff;
    --ink: #17233f;
    --muted: #53617b;
    --line: rgba(100,116,139,.18);
    --table-alt: #f5f7ff;
    --cursor-glow: rgba(83,109,254,.16);
}
"""

dark_theme = """
:root {
    color-scheme: dark;
    --page-bg: #0c1222;
    --surface: rgba(22,31,53,.9);
    --surface-solid: #17223a;
    --ink: #e8eefc;
    --muted: #b0bdd4;
    --line: rgba(160,177,210,.2);
    --table-alt: #202c47;
    --cursor-glow: rgba(108,132,255,.22);
}
"""

shared_theme_styles = """
body,
.stApp,
[data-testid="stAppViewContainer"] {
    color: var(--ink) !important;
    background:
        radial-gradient(ellipse at 9% 5%, rgba(114,139,255,.13), transparent 32rem),
        radial-gradient(ellipse at 94% 22%, rgba(69,211,199,.1), transparent 30rem),
        var(--page-bg) !important;
}

[data-testid="stAppViewContainer"] {
    position: relative;
    isolation: isolate;
}

[data-testid="stAppViewContainer"]::before {
    position: fixed;
    z-index: 0;
    inset: 0;
    background: radial-gradient(
        600px circle at var(--cursor-x, 50vw) var(--cursor-y, 35vh),
        var(--cursor-glow),
        transparent 72%
    );
    content: "";
    pointer-events: none;
}

[data-testid="stMain"] {
    position: relative;
    z-index: 1;
}

[data-testid="stApp"] {
    --text-color: var(--ink);
    --background-color: var(--page-bg);
    --secondary-background-color: var(--surface-solid);
    --primary-color: #667cff;
    --border-color: var(--line);
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.section-nav {
    border-color: var(--line);
    background: var(--surface);
}

.section-nav a {
    color: var(--ink) !important;
}

.st-key-dashboard_dark_theme {
    position: fixed !important;
    z-index: 10001;
    top: .65rem;
    right: max(1rem, calc((100vw - 1540px) / 2 + 1rem));
    width: 150px;
    padding: .35rem .45rem;
    border: 0;
    border-radius: 12px;
    background: transparent;
    box-shadow: none;
}

[data-testid="stMetric"] {
    border-color: var(--line);
    background: var(--surface);
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p {
    color: var(--muted) !important;
}

[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div {
    color: var(--ink) !important;
}

[data-testid="stDataFrame"],
[data-testid="stAlert"],
[data-testid="stExpander"] {
    border-color: var(--line);
    background: var(--surface);
}

.stMarkdown,
[data-testid="stText"],
label,
h2,
h3,
h4 {
    color: var(--ink);
}

hr {
    border-color: var(--line) !important;
}

.hero-shell .hero-description {
    color: rgba(241,245,255,.86) !important;
}

.scroll-placard {
    border-color: var(--line);
    background:
        radial-gradient(circle at 10% 18%, rgba(83,109,254,.13), transparent 22rem),
        radial-gradient(circle at 90% 82%, rgba(70,211,199,.1), transparent 24rem),
        var(--surface);
}

.scroll-placard .placard-copy p {
    color: var(--muted);
}

.scroll-placard .placard-card-face--back p {
    color: rgba(241,245,255,.86) !important;
}

.placard-hint {
    border-color: var(--line);
    color: var(--muted);
    background: var(--surface);
}

.st-key-ai_generated_report table {
    border-color: var(--line) !important;
    background: var(--surface-solid);
}

.st-key-ai_generated_report tbody td {
    border-bottom-color: var(--line) !important;
    color: var(--ink) !important;
    background: var(--surface-solid);
}

.st-key-ai_generated_report tbody tr:nth-child(even) td {
    background: var(--table-alt);
}
"""

st.markdown(
    "<style>"
    + (dark_theme if dark_mode else light_theme)
    + shared_theme_styles
    + "</style>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <section class="hero-shell">
        <div class="hero-copy">
            <div class="hero-eyebrow">Social graph intelligence</div>
            <h1 class="hero-title">Facebook Network<br><span>Explorer</span></h1>
            <p class="hero-description">
                Explore influence, communities, bridge users and simulated
                information spread across an anonymized friendship network.
            </p>
        </div>
        <div class="hero-art" aria-hidden="true">
            <span class="hero-node"></span><span class="hero-node"></span>
            <span class="hero-node"></span><span class="hero-node"></span>
            <span class="hero-node"></span><span class="hero-node"></span>
        </div>
    </section>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <nav class="section-nav" aria-label="Dashboard sections">
        <a href="#network-story">About</a>
        <a href="#network-overview">Overview</a>
        <a href="#influencer-rankings">Influencers</a>
        <a href="#community-analysis">Communities</a>
        <a href="#bridge-users">Bridge users</a>
        <a href="#diffusion-simulation">Simulation</a>
        <a href="#ai-analysis">AI report</a>
    </nav>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <section class="scroll-placard" id="network-story">
        <div class="placard-copy">
            <span class="placard-kicker">A closer look at the graph</span>
            <h2>Every connection tells part of the story.</h2>
            <p>
                This dashboard explores an anonymized friendship network.
                Scroll to turn the placard and reveal how to read its nodes,
                communities and influence scores.
            </p>
            <span class="placard-hint">Scroll down to reveal · scroll up to reset</span>
        </div>
        <div
            class="placard-card-wrap"
            role="group"
            aria-label="Scroll-animated network placard"
        >
            <div class="placard-card-inner">
                <div class="placard-card-face placard-card-face--front">
                    <span class="placard-card-label">Network field note · 01</span>
                    <div>
                        <span class="placard-card-number">4,039</span>
                        <span class="placard-card-caption">
                            anonymous nodes connected by friendship ties
                        </span>
                    </div>
                    <svg class="placard-network-art" viewBox="0 0 320 92" aria-hidden="true">
                        <g fill="none" stroke="rgba(169,244,233,.58)" stroke-width="1.5">
                            <path d="M18 60 75 28 128 66 180 22 230 58 298 30M75 28 90 78 180 22 194 78 230 58M128 66 194 78 298 30"/>
                        </g>
                        <g fill="#9ff1e3">
                            <circle cx="18" cy="60" r="5"/><circle cx="75" cy="28" r="6"/>
                            <circle cx="128" cy="66" r="5"/><circle cx="180" cy="22" r="7"/>
                            <circle cx="230" cy="58" r="6"/><circle cx="298" cy="30" r="5"/>
                            <circle cx="90" cy="78" r="4"/><circle cx="194" cy="78" r="4"/>
                        </g>
                    </svg>
                    <span class="placard-scroll-label">Scroll to turn the card ↓</span>
                </div>
                <div class="placard-card-face placard-card-face--back">
                    <span class="placard-card-label">How to read this</span>
                    <div>
                        <h3>Structure, not identity.</h3>
                        <p>
                            Each node is an anonymous user ID and each edge is
                            a friendship tie. Influence scores describe network
                            structure, not real-world popularity or personal identity.
                        </p>
                    </div>
                    <span class="placard-scroll-label">Scroll up to turn it back ↑</span>
                </div>
            </div>
        </div>
    </section>
    """,
    unsafe_allow_html=True
)

components.html(
    """
    <script>
    (() => {
        const host = window.parent;
        const document = host.document;
        const cleanupKey = "__facebookNetworkExplorerEffectsCleanup";

        const install = () => {
            const main = document.querySelector('[data-testid="stMain"]');
            const card = document.querySelector(".placard-card-wrap");
            const cardInner = document.querySelector(".placard-card-inner");

            if (!main || !card || !cardInner) return false;

            if (typeof host[cleanupKey] === "function") {
                host[cleanupKey]();
            }

            const root = document.documentElement;
            let pointerFrame = 0;
            let targetX = host.innerWidth / 2;
            let targetY = host.innerHeight * 0.35;
            let currentX = targetX;
            let currentY = targetY;

            const paintPointer = () => {
                pointerFrame = 0;
                currentX += (targetX - currentX) * 0.2;
                currentY += (targetY - currentY) * 0.2;
                root.style.setProperty("--cursor-x", `${currentX}px`);
                root.style.setProperty("--cursor-y", `${currentY}px`);

                if (Math.abs(targetX - currentX) > 0.25 || Math.abs(targetY - currentY) > 0.25) {
                    pointerFrame = host.requestAnimationFrame(paintPointer);
                }
            };

            const onPointerMove = (event) => {
                if (event.pointerType === "touch") return;
                targetX = event.clientX;
                targetY = event.clientY;
                if (!pointerFrame) pointerFrame = host.requestAnimationFrame(paintPointer);
            };

            const updateFlip = () => {
                const mainRect = main.getBoundingClientRect();
                const cardRect = card.getBoundingClientRect();
                const mainCenter = mainRect.top + main.clientHeight / 2;
                const cardCenter = cardRect.top + cardRect.height / 2;
                cardInner.classList.toggle("is-flipped", cardCenter <= mainCenter + 2);
            };

            const onResize = () => {
                targetX = Math.min(targetX, host.innerWidth);
                targetY = Math.min(targetY, host.innerHeight);
                updateFlip();
            };

            const cleanup = () => {
                host.removeEventListener("pointermove", onPointerMove);
                host.removeEventListener("resize", onResize);
                main.removeEventListener("scroll", updateFlip);
                if (pointerFrame) host.cancelAnimationFrame(pointerFrame);
                if (host[cleanupKey] === cleanup) delete host[cleanupKey];
            };

            host[cleanupKey] = cleanup;
            host.addEventListener("pointermove", onPointerMove, { passive: true });
            host.addEventListener("resize", onResize, { passive: true });
            main.addEventListener("scroll", updateFlip, { passive: true });
            window.addEventListener("pagehide", cleanup, { once: true });
            root.style.setProperty("--cursor-x", `${currentX}px`);
            root.style.setProperty("--cursor-y", `${currentY}px`);
            updateFlip();
            return true;
        };

        if (!install()) {
            const observer = new host.MutationObserver(() => {
                if (install()) {
                    observer.disconnect();
                    host.clearTimeout(timeout);
                }
            });
            observer.observe(document.documentElement, { childList: true, subtree: true });
            const timeout = host.setTimeout(() => {
                observer.disconnect();
                if (!host[cleanupKey]) {
                    console.error("Dashboard scroll effects could not find the placard elements.");
                }
            }, 5000);
        }
    })();
    </script>
    """,
    height=1,
    width=1,
    scrolling=False
)

st.divider()


# =========================================
# LOAD DATA
# =========================================

if not ORIGINAL_RESULTS_PATH.exists():

    st.error(
        "Original influencer results not found. "
        "Please run python main.py first."
    )

    st.stop()


original_df = pd.read_csv(ORIGINAL_RESULTS_PATH)

enhanced_df = None

if ENHANCED_RESULTS_PATH.exists():

    enhanced_df = pd.read_csv(ENHANCED_RESULTS_PATH)

    enhanced_df["User_ID"] = enhanced_df["User_ID"].astype(int)


community_top_df = (
    pd.read_csv(COMMUNITY_TOP_PATH)
    if COMMUNITY_TOP_PATH.exists()
    else None
)

bridge_df = (
    pd.read_csv(BRIDGE_USERS_PATH)
    if BRIDGE_USERS_PATH.exists()
    else None
)

community_sizes_df = (
    pd.read_csv(COMMUNITY_SIZES_PATH)
    if COMMUNITY_SIZES_PATH.exists()
    else None
)


# =========================================
# NETWORK OVERVIEW
# =========================================

st.markdown('<div id="network-overview"></div>', unsafe_allow_html=True)
render_topic_card(
    "Network Overview",
    "A quick read of the network's size and detected community structure.",
    "NETWORK SNAPSHOT"
)

metric_source = (
    enhanced_df
    if enhanced_df is not None
    else original_df
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Users",
    "4,039"
)

col2.metric(
    "Total Connections",
    "88,234"
)

community_count = (
    len(community_sizes_df)
    if community_sizes_df is not None
    else metric_source["Community"].nunique()
)

col3.metric(
    "Communities Detected",
    f"{community_count:,}"
)


# =========================================
# INFLUENCER RANKINGS
# =========================================

st.markdown('<div id="influencer-rankings"></div>', unsafe_allow_html=True)
st.divider()

render_topic_card(
    "Influencer Rankings",
    "Explore the users with the strongest structural influence in the friendship graph.",
    "RANKED INSIGHTS"
)

if enhanced_df is not None:

    score_column = "Enhanced_Influence_Score"

    ranking_df = enhanced_df.sort_values(
        score_column,
        ascending=False
    )

    render_topic_card(
        "Top 10 Influencers – Enhanced Score",
        "The enhanced score brings multiple network signals together to highlight influential users.",
        "TOP RANKINGS",
        level=3
    )

    display_columns = [
        column for column in [
            "Influencer_Rank",
            "User_ID",
            score_column,
            "Community"
        ]
        if column in ranking_df.columns
    ]

    st.dataframe(
        ranking_df[display_columns].head(10),
        width="stretch",
        hide_index=True
    )

    st.bar_chart(
        ranking_df.head(10).set_index("User_ID")[score_column],
        y_label="Enhanced influence score"
    )

    st.download_button(
        "⬇️ Download Enhanced Results CSV",
        data=ranking_df.to_csv(index=False).encode("utf-8"),
        file_name="enhanced_influencer_results.csv",
        mime="text/csv",
        width="stretch"
    )

else:

    ranking_df = original_df.sort_values(
        "Influence_Score",
        ascending=False
    )

    st.dataframe(
        ranking_df.head(10),
        width="stretch",
        hide_index=True
    )

    st.warning(
        "Run python enhancements.py to generate enhanced results."
    )


# =========================================
# CENTRALITY ANALYSIS
# =========================================

if enhanced_df is not None:

    st.divider()

    render_topic_card(
        "Centrality Analysis",
        "Compare centrality measures to see how users occupy important positions in the network.",
        "NETWORK POSITION"
    )

    centrality_options = [
        "Degree_Centrality",
        "Betweenness_Centrality",
        "Closeness_Centrality",
        "PageRank",
        "Eigenvector_Centrality"
    ]

    available = [
        column
        for column in centrality_options
        if column in enhanced_df.columns
    ]

    if available:

        selected_measure = st.selectbox(
            "Choose a centrality measure",
            available
        )

        centrality_top = enhanced_df.nlargest(
            10,
            selected_measure
        )

        st.bar_chart(
            centrality_top.set_index("User_ID")[selected_measure],
            y_label=selected_measure.replace("_", " ")
        )

        st.dataframe(
            centrality_top[
                ["User_ID", selected_measure, "Community"]
            ],
            width="stretch",
            hide_index=True
        )


# =========================================
# COMMUNITY ANALYSIS
# =========================================

st.markdown('<div id="community-analysis"></div>', unsafe_allow_html=True)
st.divider()

render_topic_card(
    "Community Analysis",
    "See how the friendship graph groups users into communities and inspect influential members in each group.",
    "GROUP STRUCTURE"
)

if community_sizes_df is not None:

    chart_df = community_sizes_df.sort_values(
        "Number_of_Users",
        ascending=False
    )

    st.bar_chart(
        chart_df.set_index("Community")["Number_of_Users"],
        y_label="Number of users"
    )

else:

    st.bar_chart(
        metric_source["Community"].value_counts().sort_index(),
        y_label="Number of users"
    )


if community_top_df is not None:

    render_topic_card(
        "Top Influencers in Each Community",
        "Choose a community to inspect its highest-ranked members and their network metrics.",
        "COMMUNITY SPOTLIGHT",
        level=3
    )

    community_ids = sorted(
        community_top_df["Community"].dropna().unique().tolist()
    )

    selected_community = st.selectbox(
        "Select a community",
        community_ids,
        key="community_filter"
    )

    one_community = community_top_df[
        community_top_df["Community"] == selected_community
    ]

    display_cols = [
        column
        for column in [
            "User_ID",
            "Enhanced_Influence_Score",
            "Degree_Centrality",
            "Betweenness_Centrality",
            "Community"
        ]
        if column in one_community.columns
    ]

    st.dataframe(
        one_community[display_cols],
        width="stretch",
        hide_index=True
    )

else:

    st.info(
        "Run python enhancements.py to generate community-wise rankings."
    )


# =========================================
# BRIDGE USERS
# =========================================


# =========================================
# BRIDGE USERS AND CROSS-COMMUNITY ANALYSIS
# =========================================

st.markdown('<div id="bridge-users"></div>', unsafe_allow_html=True)
st.divider()

render_topic_card(
    "Important Bridge Users",
    "Find users whose connections link otherwise separate communities and help information travel between them.",
    "CROSS-COMMUNITY ROLE"
)

if bridge_df is not None:

    # Check whether new bridge metrics are available

    required_bridge_columns = [
        "Cross_Community_Edge_Count",
        "Connected_Communities_Count"
    ]

    if all(
        col in bridge_df.columns
        for col in required_bridge_columns
    ):

        st.success(
            "Enhanced cross-community bridge analysis available!"
        )

        # Sort bridge users using actual cross-community metrics

        bridge_df = bridge_df.sort_values(
            by=[
                "Cross_Community_Edge_Count",
                "Connected_Communities_Count",
                "Betweenness_Centrality"
            ],
            ascending=[False, False, False]
        )

        # -------------------------------------
        # BRIDGE USER SUMMARY
        # -------------------------------------

        render_topic_card(
            "Bridge Network Summary",
            "A compact view of the strongest bridge user's cross-community reach.",
            "AT A GLANCE",
            level=3
        )

        top_bridge = bridge_df.iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Top Bridge User",
            int(top_bridge["User_ID"])
        )

        col2.metric(
            "Cross-Community Edges",
            int(top_bridge["Cross_Community_Edge_Count"])
        )

        col3.metric(
            "Communities Connected",
            int(top_bridge["Connected_Communities_Count"])
        )

        # -------------------------------------
        # BRIDGE USER TABLE
        # -------------------------------------

        render_topic_card(
            "Top 20 Bridge Users",
            "Ranked by cross-community edges, distinct connected communities, and betweenness centrality.",
            "BRIDGE RANKINGS",
            level=3
        )

        bridge_cols = [
            "User_ID",
            "Community",
            "Cross_Community_Edge_Count",
            "Connected_Communities_Count",
            "Betweenness_Centrality",
            "Enhanced_Influence_Score"
        ]

        available_bridge_cols = [
            col for col in bridge_cols
            if col in bridge_df.columns
        ]

        st.dataframe(
            bridge_df[available_bridge_cols].head(20),
            width="stretch",
            hide_index=True
        )

        # -------------------------------------
        # BRIDGE USER VISUALIZATION
        # -------------------------------------

        render_topic_card(
            "Bridge User Comparison",
            "Compare how frequently top bridge users connect across community boundaries.",
            "COMPARISON",
            level=3
        )

        chart_df = bridge_df.head(10).copy()

        chart_df["User_ID"] = (
            chart_df["User_ID"].astype(str)
        )

        st.bar_chart(
            chart_df.set_index("User_ID")[
                "Cross_Community_Edge_Count"
            ],
            y_label="Cross-community edges"
        )

        # -------------------------------------
        # CONNECTED COMMUNITIES CHART
        # -------------------------------------

        render_topic_card(
            "Number of Communities Connected",
            "See how many distinct communities each leading bridge user reaches.",
            "COMMUNITY REACH",
            level=3
        )

        st.bar_chart(
            chart_df.set_index("User_ID")[
                "Connected_Communities_Count"
            ],
            y_label="Other communities connected"
        )

    else:

        st.warning(
            "Your bridge_users.csv contains old results. "
            "Run python enhancements.py again."
        )

        st.dataframe(
            bridge_df.head(20),
            width="stretch",
            hide_index=True
        )

else:

    st.info(
        "Run python enhancements.py to generate bridge_users.csv."
    )


# =========================================
# CROSS-COMMUNITY EDGE ANALYSIS
# =========================================

st.markdown('<div id="cross-community"></div>', unsafe_allow_html=True)
st.divider()

render_topic_card(
    "Cross-Community Connections",
    "Inspect the friendship ties that cross detected community boundaries.",
    "INTER-COMMUNITY TIES"
)

CROSS_EDGES_PATH = (
    OUTPUT_DIR / "cross_community_edges.csv"
)

if CROSS_EDGES_PATH.exists():

    cross_edges_df = pd.read_csv(CROSS_EDGES_PATH)

    col1, col2 = st.columns(2)

    col1.metric(
        "Total Cross-Community Edges",
        f"{len(cross_edges_df):,}"
    )

    col2.metric(
        "Communities Involved",
        cross_edges_df[
            ["Community_1", "Community_2"]
        ].stack().nunique()
    )

    render_topic_card(
        "Cross-Community Edge Records",
        "Browse individual friendship links and the communities joined by each edge.",
        "EDGE EXPLORER",
        level=3
    )

    st.dataframe(
        cross_edges_df.head(100),
        width="stretch",
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Cross-Community Edges",
        data=cross_edges_df.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="cross_community_edges.csv",
        mime="text/csv",
        width="stretch"
    )

else:

    st.warning(
        "Cross-community edge file not found. "
        "Run python enhancements.py first."
    )



# =========================================
# COMPARE TWO USERS
# =========================================


# =========================================
# INFLUENCE DIFFUSION SIMULATION
# =========================================

st.markdown('<div id="diffusion-simulation"></div>', unsafe_allow_html=True)
import random
import networkx as nx
from pathlib import Path

st.divider()

render_topic_card(
    "Influence Diffusion Simulation",
    "Explore how information may spread through the friendship network with the Independent Cascade Model. Each newly influenced user gets an independent chance to reach inactive friends in the next round.",
    "SIMULATION LAB"
)

# -----------------------------------------
# LOAD FACEBOOK NETWORK
# -----------------------------------------

@st.cache_resource
def load_diffusion_graph():

    dataset_path = (
        Path(__file__).resolve().parent
        / "dataset"
        / "facebook_combined.txt"
    )

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}"
        )

    graph = nx.read_edgelist(
        str(dataset_path),
        nodetype=int
    )

    return graph


# -----------------------------------------
# INDEPENDENT CASCADE MODEL
# -----------------------------------------

def run_diffusion_simulation(
    graph,
    starting_user,
    probability,
    max_rounds,
    random_seed=42
):

    rng = random.Random(random_seed)

    active_users = {starting_user}
    current_frontier = {starting_user}

    round_results = [
        {
            "Round": 0,
            "Newly Influenced": 1,
            "Total Influenced": 1
        }
    ]

    for round_number in range(1, max_rounds + 1):

        newly_influenced = set()

        for user in current_frontier:

            for neighbor in graph.neighbors(user):

                if neighbor not in active_users:

                    if rng.random() < probability:

                        newly_influenced.add(neighbor)

        if not newly_influenced:
            break

        active_users.update(newly_influenced)

        current_frontier = newly_influenced

        round_results.append(
            {
                "Round": round_number,
                "Newly Influenced": len(newly_influenced),
                "Total Influenced": len(active_users)
            }
        )

    return active_users, pd.DataFrame(round_results)


# -----------------------------------------
# LOAD INFLUENCER OPTIONS
# -----------------------------------------

enhanced_path = (
    Path(__file__).resolve().parent
    / "outputs"
    / "enhanced_influencer_results.csv"
)

if enhanced_path.exists():

    diffusion_influencers = pd.read_csv(
        enhanced_path
    )

    if (
        "User_ID" in diffusion_influencers.columns
        and "Enhanced_Influence_Score"
        in diffusion_influencers.columns
    ):

        diffusion_influencers = (
            diffusion_influencers.sort_values(
                "Enhanced_Influence_Score",
                ascending=False
            )
        )

        influencer_options = (
            diffusion_influencers["User_ID"]
            .dropna()
            .astype(int)
            .drop_duplicates()
            .head(20)
            .tolist()
        )

    else:
        influencer_options = []

else:
    influencer_options = []


# -----------------------------------------
# SIMULATION CONTROLS
# -----------------------------------------

if influencer_options:

    render_topic_card(
        "Configure Your Simulation",
        "Choose a starting influencer, spread probability, and round limit before running the model.",
        "SIMULATION SETTINGS",
        level=3
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        selected_user = st.selectbox(
            "Select Starting Influencer",
            influencer_options,
            index=0,
            key="diffusion_start_user"
        )

    with col2:

        spread_probability = st.slider(
            "Spread Probability",
            min_value=0.05,
            max_value=1.0,
            value=0.20,
            step=0.05,
            key="diffusion_probability"
        )

    with col3:

        simulation_rounds = st.slider(
            "Number of Rounds",
            min_value=1,
            max_value=10,
            value=5,
            key="diffusion_rounds"
        )

    if st.button(
        "▶ Run Influence Diffusion Simulation",
        width="stretch"
    ):

        try:

            graph = load_diffusion_graph()

            if selected_user not in graph:
                st.error(
                    "Selected user is not present in the network."
                )

            else:

                with st.spinner(
                    "Simulating information spread..."
                ):

                    influenced_users, diffusion_df = (
                        run_diffusion_simulation(
                            graph=graph,
                            starting_user=int(selected_user),
                            probability=spread_probability,
                            max_rounds=simulation_rounds
                        )
                    )

                # ---------------------------------
                # RESULTS
                # ---------------------------------

                st.success(
                    "Influence diffusion simulation completed!"
                )

                total_users = graph.number_of_nodes()

                total_influenced = len(influenced_users)

                reach_percentage = (
                    total_influenced / total_users
                ) * 100

                simulation_results = {
                    "starting_user": int(selected_user),
                    "spread_probability": float(spread_probability),
                    "max_rounds": int(simulation_rounds),
                    "random_seed": 42,
                    "total_users": int(total_users),
                    "total_influenced": int(total_influenced),
                    "reach_percentage": float(reach_percentage),
                    "round_results": diffusion_df.to_dict(
                        orient="records"
                    )
                }

                OUTPUT_DIR.mkdir(
                    parents=True,
                    exist_ok=True
                )

                temporary_results_path = (
                    SIMULATION_RESULTS_PATH.with_suffix(".tmp")
                )

                with temporary_results_path.open(
                    "w",
                    encoding="utf-8"
                ) as results_file:
                    json.dump(
                        simulation_results,
                        results_file,
                        indent=2
                    )

                temporary_results_path.replace(
                    SIMULATION_RESULTS_PATH
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Starting Influencer",
                    int(selected_user)
                )

                col2.metric(
                    "Total Influenced Users",
                    f"{total_influenced:,}"
                )

                col3.metric(
                    "Network Reach",
                    f"{reach_percentage:.2f}%"
                )

                # ---------------------------------
                # DIFFUSION CHART
                # ---------------------------------

                render_topic_card(
                    "Information Spread Across Rounds",
                    "Track the cumulative number of influenced users as the simulation advances.",
                    "CUMULATIVE REACH",
                    level=3
                )

                st.line_chart(
                    diffusion_df.set_index("Round")[
                        "Total Influenced"
                    ],
                    y_label="Total Influenced Users"
                )

                render_topic_card(
                    "Newly Influenced Users Per Round",
                    "Compare how many additional users are reached in each round.",
                    "ROUND-BY-ROUND ACTIVITY",
                    level=3
                )

                st.bar_chart(
                    diffusion_df.set_index("Round")[
                        "Newly Influenced"
                    ],
                    y_label="Newly Influenced Users"
                )

                # ---------------------------------
                # ROUND RESULTS TABLE
                # ---------------------------------

                render_topic_card(
                    "Simulation Results",
                    "Review the detailed counts recorded for each round.",
                    "RESULTS TABLE",
                    level=3
                )

                st.dataframe(
                    diffusion_df,
                    width="stretch",
                    hide_index=True
                )

                # ---------------------------------
                # DOWNLOAD INFLUENCED USERS
                # ---------------------------------

                influenced_df = pd.DataFrame(
                    {
                        "Influenced_User_ID": sorted(
                            influenced_users
                        )
                    }
                )

                st.download_button(
                    "⬇️ Download Influenced Users CSV",
                    data=influenced_df.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name="influenced_users.csv",
                    mime="text/csv",
                    width="stretch"
                )

                # ---------------------------------
                # SIMULATION EXPLANATION
                # ---------------------------------

                render_topic_card(
                    "Simulation Interpretation",
                    f"User {selected_user} started the spread at {spread_probability:.0%} probability, influencing {total_influenced:,} of {total_users:,} users. This is a probabilistic simulation, not a prediction of actual information sharing; results depend on the selected settings and random seed.",
                    "RESULTS SUMMARY",
                    level=3
                )

        except Exception as error:

            st.error(
                f"Simulation error: {error}"
            )

else:

    st.warning(
        "Influencer results are unavailable. "
        "Run python enhancements.py first."
    )

# =========================================
# MULTI-AGENT AI ANALYSIS
# =========================================

st.markdown('<div id="ai-analysis"></div>', unsafe_allow_html=True)
st.divider()

render_topic_card(
    "Multi-Agent AI Analysis",
    "Run a five-agent LangGraph workflow to analyze the network, identify influencers and communities, develop recommendations, and generate a final report.",
    "AI WORKFLOW"
)

render_topic_card(
    "Five-Agent Pipeline",
    "Network analysis → influencer detection → community detection → recommendations → AI report generation.",
    "HOW IT WORKS",
    level=3
)

if SIMULATION_RESULTS_PATH.exists():
    st.success(
        "Your latest completed diffusion simulation will be included "
        "when you run the AI agents."
    )
else:
    st.caption(
        "Run a diffusion simulation first to include its settings and "
        "round-by-round results in the next AI report."
    )

import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent
AGENT_SCRIPT = BASE_DIR / "agents.py"
REPORT_PATH = BASE_DIR / "outputs" / "agent_report.txt"

if st.button(
    "🚀 Run All 5 AI Agents",
    key="run_all_ai_agents",
    width="stretch"
):

    if not AGENT_SCRIPT.exists():

        st.error("agents.py file was not found.")

    else:

        with st.spinner(
            "Running all five AI agents. Please wait..."
        ):

            try:

                result = subprocess.run(
                    [sys.executable, str(AGENT_SCRIPT)],
                    cwd=str(BASE_DIR),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=600
                )

                if result.returncode == 0:

                    st.success(
                        "All 5 AI agents completed successfully!"
                    )

                    st.session_state["agents_completed"] = True

                else:

                    st.error(
                        "AI agent execution failed. "
                        "Check the error below."
                    )

                    st.code(
                        result.stderr or result.stdout
                    )

            except subprocess.TimeoutExpired:

                st.error(
                    "The agents took too long to finish. "
                    "Please try again."
                )

            except Exception as error:

                st.error(
                    f"Error running agents: {error}"
                )


# =========================================
# DISPLAY AI-GENERATED REPORT
# =========================================

render_topic_card(
    "AI-Generated Network Analysis Report",
    "Read or download the latest report produced by the analysis workflow.",
    "GENERATED REPORT",
    level=3
)

if REPORT_PATH.exists():

    with open(
        REPORT_PATH,
        "r",
        encoding="utf-8"
    ) as report_file:

        report_content = report_file.read()

    if report_content.strip():

        with st.container(key="ai_generated_report"):

            st.markdown(report_content)

            st.download_button(
                label="⬇️ Download AI Report",
                data=report_content,
                file_name="Facebook_Network_AI_Report.txt",
                mime="text/plain",
                key="download_ai_report",
                width="stretch"
            )

    else:

        st.warning(
            "The AI report file is empty. Run all five agents again."
        )

else:

    st.info(
        "No AI report found yet. Click 'Run All 5 AI Agents' "
        "to generate your report."
    )
