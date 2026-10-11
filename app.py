import streamlit as st

import pandas as pd

import sqlite3

import json

import os

import streamlit.components.v1 as components

import plotly.express as px

import plotly.graph_objects as go

from typing import Dict, Any, Optional

from core.pipeline import VerifiableAnalysisPipeline

from core.sandbox import SQLSandbox

from core.verification_engine import DeterministicFactChecker

from core.proof_receipt import CryptographicProofGenerator

from fetch_crypto_data import fetch_live_crypto_data

# Page Configuration

st.set_page_config(

    page_title="AGENT-ANALYTIX | Verifiable Autonomous Data Analysis",

    page_icon="🛡️",

    layout="wide",

    initial_sidebar_state="expanded"

)

# Ultra-Modern Cyber-Glassmorphism & Neon Ambient Theme

st.markdown("""

<style>

    /* Global Ambient Background */

    .stApp {

        background: radial-gradient(circle at 15% 20%, rgba(14, 165, 233, 0.08) 0%, transparent 40%),

                    radial-gradient(circle at 85% 75%, rgba(16, 185, 129, 0.08) 0%, transparent 40%),

                    radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 60%),

                    #0B0F19;

        color: #F1F5F9;

        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

    }

    /* Header Gradient */

    .hero-title {

        font-size: 2.6rem;

        font-weight: 900;

        letter-spacing: -0.02em;

        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #34D399 100%);

        -webkit-background-clip: text;

        -webkit-text-fill-color: transparent;

        margin-bottom: 0.1rem;

        display: inline-block;

    }

    .hero-subtitle {

        font-size: 1.05rem;

        color: #94A3B8;

        font-weight: 400;

        margin-bottom: 1.8rem;

    }

    /* Glassmorphism Cards */

    .glass-card {

        background: rgba(17, 24, 39, 0.7);

        backdrop-filter: blur(16px);

        -webkit-backdrop-filter: blur(16px);

        border: 1px solid rgba(255, 255, 255, 0.08);

        border-radius: 14px;

        padding: 20px;

        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);

        margin-bottom: 1.2rem;

        transition: transform 0.2s ease, border-color 0.2s ease;

    }

    .glass-card:hover {

        border-color: rgba(56, 189, 248, 0.3);

    }

    /* Neon Pulsing Badges */

    .badge-verified {

        background: linear-gradient(135deg, rgba(6, 95, 70, 0.8) 0%, rgba(4, 120, 87, 0.9) 100%);

        color: #6EE7B7;

        padding: 8px 18px;

        border-radius: 30px;

        font-weight: 700;

        font-size: 0.92rem;

        display: inline-flex;

        align-items: center;

        gap: 8px;

        border: 1px solid #10B981;

        box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);

        animation: pulse 2.5s infinite;

    }

    .badge-partial {

        background: linear-gradient(135deg, rgba(120, 53, 15, 0.8) 0%, rgba(180, 83, 9, 0.9) 100%);

        color: #FDE68A;

        padding: 8px 18px;

        border-radius: 30px;

        font-weight: 700;

        font-size: 0.92rem;

        display: inline-flex;

        align-items: center;

        gap: 8px;

        border: 1px solid #F59E0B;

        box-shadow: 0 0 15px rgba(245, 158, 11, 0.3);

    }

    .badge-flagged {

        background: linear-gradient(135deg, rgba(127, 29, 29, 0.8) 0%, rgba(185, 28, 28, 0.9) 100%);

        color: #FECACA;

        padding: 8px 18px;

        border-radius: 30px;

        font-weight: 700;

        font-size: 0.92rem;

        display: inline-flex;

        align-items: center;

        gap: 8px;

        border: 1px solid #EF4444;

        box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);

    }

    /* Hash string container */

    .hash-display {

        font-family: 'Fira Code', monospace;

        font-size: 0.82rem;

        background: rgba(15, 23, 42, 0.85);

        border: 1px solid rgba(56, 189, 248, 0.2);

        border-radius: 8px;

        padding: 8px 12px;

        color: #38BDF8;

        word-break: break-all;

    }

    /* Key stat pill */

    .stat-pill {

        background: rgba(30, 41, 59, 0.6);

        border: 1px solid rgba(255, 255, 255, 0.05);

        border-radius: 10px;

        padding: 12px;

        text-align: center;

    }

    .stat-label {

        font-size: 0.78rem;

        color: #94A3B8;

        text-transform: uppercase;

        letter-spacing: 0.05em;

    }

    .stat-val {

        font-size: 1.4rem;

        font-weight: 700;

        color: #F8FAFC;

        margin-top: 4px;

    }

    @keyframes pulse {

        0%, 100% { transform: scale(1); }

        50% { transform: scale(1.02); }

    }

</style>

""", unsafe_allow_html=True)

# Domain Specifications

DOMAINS = {

    "🏬 Retail (Superstore Orders)": {

        "db": "retail_data.db",

        "table": "orders",

        "desc": "5,000 retail orders across Technology, Furniture, and Office Supplies with Sales, Profit, and Discounts.",

        "sample_questions": [

            "What are the top 3 categories by total sales and profit?",

            "Which region generates the highest profit margin?",

            "What is the average discount and sales per customer segment?"

        ]

    },

    "👥 HR Attrition & Analytics": {

        "db": "hr_data.db",

        "table": "employees",

        "desc": "3,000 employee records with Department, Monthly Income, Overtime, and Attrition status.",

        "sample_questions": [

            "What is the attrition rate across different departments?",

            "How does overtime work affect employee attrition rate?",

            "What is the average monthly income by job role?"

        ]

    },

    "🏦 FinTech Loan Risk & Default": {

        "db": "loan_data.db",

        "table": "loans",

        "desc": "4,000 personal and business loans with Interest Rate, DTI, Credit Score, and Default status.",

        "sample_questions": [

            "What is the default rate by loan grade?",

            "Which loan purpose has the highest average loan amount?",

            "How does credit score correlate with loan default?"

        ]

    },

    "💳 Fraud Detection (Credit Card)": {

        "db": "fraud_data.db",

        "table": "transactions",

        "desc": "20,000 real credit card transactions with ProductCD, TransactionAmt, and isFraud flags.",

        "sample_questions": [

            "How does ProductCD relate to fraud rate?",

            "What is the total transaction volume and fraud count?",

            "Which card types have the highest average transaction amount?"

        ]

    },

    "🛒 E-Commerce Customer Journeys": {

        "db": "ecommerce_data.db",

        "table": "orders",

        "desc": "4,000 user web sessions with Device, Traffic Source, Cart Value, and Conversion flags.",

        "sample_questions": [

            "Which device type has the highest conversion rate and cart value?",

            "What traffic source drives the highest total order value?",

            "What is the average duration and page views per country?"

        ]

    },

    "📈 Live Cryptocurrency Market": {

        "db": "crypto_data.db",

        "table": "coins",

        "desc": "Live 24h Binance USDT ticker prices, trading volume, and price change percentages.",

        "sample_questions": [

            "Which 5 coins had the highest price change percentage today?",

            "What are the top 5 cryptocurrencies by 24h trading volume?",

            "Which coin has the highest lastPrice among active pairs?"

        ]

    }

}

# Persistent Session State

if "last_analysis_result" not in st.session_state:

    st.session_state.last_analysis_result = None

if "chat_history" not in st.session_state:

    st.session_state.chat_history = []

# Sidebar Controls

with st.sidebar:

    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)

    st.markdown("### **System Control Center**")

    st.markdown("**🤖 Model Orchestrator**")

    provider_choice = st.selectbox(

        "Model Orchestration",

        options=["auto", "openai", "ollama", "fallback"],

        format_func=lambda x: {

            "auto": "🌟 Auto (OpenAI with Resilient Failover)",

            "openai": "⚡ OpenAI Cloud (GPT-4o-mini)",

            "ollama": "🦙 Ollama Local (Qwen 2.5:7B)",

            "fallback": "🛡️ High-Speed Grounded Engine"

        }[x],

        label_visibility="collapsed"

    )

    st.markdown("---")

    # Custom CSV Upload — automatically infer the domain from the uploaded dataset.
    st.markdown("---")
    st.markdown("**📤 Ingest Custom CSV**")
    uploaded_file = st.file_uploader(
        "Upload CSV for Verifiable Analysis",
        type=["csv"],
        label_visibility="collapsed",
        key="custom_csv_uploader",
    )

    if uploaded_file is not None:
        try:
            custom_df = pd.read_csv(uploaded_file, encoding="latin1")
            if custom_df.empty or len(custom_df.columns) == 0:
                st.error("The uploaded CSV has no usable data.")
                st.stop()

            custom_db = "custom_data.db"
            custom_table = "custom_records"
            with sqlite3.connect(custom_db) as conn:
                custom_df.to_sql(custom_table, conn, if_exists="replace", index=False)

            filename = os.path.splitext(uploaded_file.name)[0]
            pretty_name = filename.replace("_", " ").replace("-", " ").title()
            columns = {
                str(col).lower().replace("_", "").replace(" ", "")
                for col in custom_df.columns
            }
            file_key = filename.lower().replace("_", " ").replace("-", " ")

            if "heartdisease" in columns or {"chestpaintype", "maxhr"}.issubset(columns) or "heart" in file_key:
                detected_domain = "❤️ Heart Disease Prediction"
            elif "isfraud" in columns or "fraud" in file_key or {"transactionid", "transactionamt"}.issubset(columns):
                detected_domain = "💳 Fraud Detection"
            elif "attrition" in columns or "employee" in file_key or "hr analytics" in file_key:
                detected_domain = "👥 HR Analytics"
            elif {"sales", "profit"}.issubset(columns) or "retail" in file_key or "superstore" in file_key:
                detected_domain = "🛍️ Retail Analytics"
            elif "trafficvolume" in columns or "traffic" in file_key:
                detected_domain = "🚦 Traffic Analytics"
            elif "loan" in file_key or "default" in columns:
                detected_domain = "🏦 Loan Risk Analytics"
            elif "crypto" in file_key or "symbol" in columns:
                detected_domain = "📈 Cryptocurrency Analytics"
            else:
                detected_domain = f"📄 {pretty_name or 'Custom Dataset'} Analytics"

            num_cols = [c for c in custom_df.columns if pd.api.types.is_numeric_dtype(custom_df[c])]
            cat_cols = [c for c in custom_df.columns if not pd.api.types.is_numeric_dtype(custom_df[c])]
            
            sample_qs = []
            if num_cols and cat_cols:
                sample_qs.append(f"What are the top 5 records by {num_cols[0]}?")
                sample_qs.append(f"What is the average {num_cols[0]} across {cat_cols[0]}?")
                sample_qs.append(f"What are the summary statistics of {num_cols[0]}?")
                sample_qs.append(f"What is the distribution of {cat_cols[0]}?")
            elif num_cols:
                sample_qs.append(f"What are the top 5 records by {num_cols[0]}?")
                sample_qs.append(f"What are the summary statistics of {num_cols[0]}?")
            elif cat_cols:
                sample_qs.append(f"What is the distribution of {cat_cols[0]}?")
                sample_qs.append(f"What are the top 5 records by {cat_cols[0]}?")
            sample_qs.append("Are there any missing values in this dataset?")
            sample_qs.append("How many total records are in this dataset?")

            domain_name = detected_domain
            domain_cfg = {
                "db": custom_db,
                "table": custom_table,
                "desc": f"Uploaded dataset '{uploaded_file.name}' with {len(custom_df):,} rows and {len(custom_df.columns)} columns.",
                "sample_questions": sample_qs,
            }
            st.success(f"Detected Target Domain: {domain_name}")
            st.caption(domain_cfg["desc"])
        except Exception as e:
            st.error(f"Error parsing uploaded file: {e}")
            st.stop()
    else:
        st.markdown("---")
        st.markdown("**📂 Target Domain**")
        domain_name = st.selectbox(
            "Choose Benchmark Domain",
            list(DOMAINS.keys()),
            label_visibility="collapsed",
        )
        domain_cfg = DOMAINS[domain_name]
        st.caption(domain_cfg["desc"])

        if "Live Cryptocurrency" in domain_name:
            if st.button("🔄 Fetch Live 24hr Binance Feed", use_container_width=True):
                with st.spinner("Streaming real-time ticker prices from Binance..."):
                    try:
                        df_live = fetch_live_crypto_data()
                        with sqlite3.connect("crypto_data.db") as conn:
                            df_live.to_sql("coins", conn, if_exists="replace", index=False)
                        st.success(f"Streamed {len(df_live)} live tickers into crypto_data.db!")
                    except Exception as e:
                        st.error(f"Feed error: {e}")

# Track active dataset identity and reset session state on switch
if uploaded_file is not None:
    active_ds_key = f"upload::{uploaded_file.name}::{getattr(uploaded_file, 'size', 0)}"
else:
    active_ds_key = f"preset::{domain_name}::{domain_cfg['db']}::{domain_cfg['table']}"

if st.session_state.get("current_active_ds_key") != active_ds_key:
    st.session_state.current_active_ds_key = active_ds_key
    st.session_state.last_analysis_result = None
    if "adv_input_claim" in st.session_state:
        st.session_state.adv_input_claim = ""

# Header

st.markdown('<div class="hero-title">AGENT-ANALYTIX</div>', unsafe_allow_html=True)

st.markdown('<div class="hero-subtitle">A Multi-Agent Framework for Verifiable Autonomous Data Analysis Using Large Language Models</div>', unsafe_allow_html=True)

# Main Navigation Tabs

tab_analysis, tab_visuals, tab_stats, tab_simulator, tab_audit, tab_schema, tab_stress, tab_paper = st.tabs([

    "🚀 Verifiable Analysis",

    "📊 Multi-Chart Canvas",

    "📐 Descriptive Statistics",

    "🎛️ What-If Simulator",

    "🕵️ Audit Sandbox",

    "🗄️ Schema Explorer",

    "🧪 Stress Testing",

    "📑 Academic Paper"

])

# ==============================================================================

# TAB 1: AUTONOMOUS ANALYSIS

# ==============================================================================

with tab_analysis:

    col_q, col_sample = st.columns([3, 2])

    with col_sample:

        st.markdown("**Domain Suggested Prompts:**")

        selected_preset = st.selectbox("Presets", domain_cfg["sample_questions"], label_visibility="collapsed")

    with col_q:

        st.markdown("**Enter Natural Language Analysis Query:**")

        user_question = st.text_input(

            "Query Input",

            value=selected_preset,

            placeholder="e.g. What are the top 3 categories by total sales and profit?",

            label_visibility="collapsed"

        )

    run_clicked = st.button("🚀 Run Autonomous Multi-Agent Analysis", type="primary", use_container_width=True)

    if run_clicked and user_question:

        pipeline = VerifiableAnalysisPipeline(provider=provider_choice)

        progress_bar = st.progress(0)

        status_text = st.empty()

        def ui_progress(stage, msg):

            stage_map = {

                "SCHEMA_INSPECTION": (10, "🔍 Planner: Inspecting Database Schema & Column Cardinality..."),

                "PLANNING": (25, "🎯 Planner: Formulating Analytical Hypotheses & Execution DAG..."),

                "CODING": (45, "💻 Coder: Generating Dialect-Safe Read-Only SQL Query..."),

                "EXECUTION": (60, "⚡ Sandbox: Executing Read-Only SQL & Computing SHA-256 Result Hash..."),

                "AUDITING": (75, "🕵️ Auditor: Performing Adversarial Boundary & Semantic Cross-Check..."),

                "STATISTICS": (85, "📐 Statistical Engine: Running Hypothesis Tests (H0/H1) & p-values..."),

                "SYNTHESIS": (92, "📊 Synthesizer: Generating Multi-Chart Suite & Grounded Takeaways..."),

                "FACT_CHECKING": (97, "🔬 Fact-Checker: Running Algorithmic Ground-Truth Entity Verification..."),

                "COMPLETE": (100, "✅ Verifiable Pipeline Execution Completed; inspect verification status")

            }

            pct, default_msg = stage_map.get(stage, (50, msg))

            progress_bar.progress(pct)

            status_text.info(f"**[{stage}]** {msg}")

        try:

            with st.spinner("Multi-Agent Framework executing verifiable analysis loop..."):

                analysis_result = pipeline.run(

                    db_path=domain_cfg["db"],

                    table_name=domain_cfg["table"],

                    question=user_question,

                    progress_callback=ui_progress

                )

                st.session_state.last_analysis_result = analysis_result

                st.session_state.chat_history.append({

                    "question": user_question,

                    "answer": analysis_result["synthesis"],

                    "badge": analysis_result["proof_certificate"]["badge_text"],

                    "hash": analysis_result["proof_certificate"]["certificate_hash"]

                })

                progress_bar.progress(100)

                status_text.success("Analysis finished. Review the auditor verdict and verification limitations below.")

        except Exception as e:

            status_text.error(f"Pipeline execution error: {str(e)}")

    # Display Current Result

    res = st.session_state.last_analysis_result

    if res:

        st.markdown("---")

        # 1. Verification Certificate Badge & Metrics

        cert = res["proof_certificate"]

        exec_meta = res["execution"]

        fact_meta = res["fact_check"]

        badge_level = cert["badge_level"]

        col_badge, col_m1, col_m2, col_m3, col_m4 = st.columns([2.6, 1, 1, 1, 1])

        with col_badge:
            if badge_level == "CRYPTOGRAPHICALLY_VERIFIED":
                st.markdown(f'<div class="badge-verified">🛡️ {cert["badge_text"]}</div>', unsafe_allow_html=True)
            elif badge_level == "PARTIALLY_VERIFIED":
                st.markdown(f'<div class="badge-partial">⚠️ {cert["badge_text"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="badge-flagged">🚨 {cert["badge_text"]}</div>', unsafe_allow_html=True)
            st.caption(f"SHA-256 Certificate: `{cert['certificate_hash'][:22]}...` • Proves record was not altered; does not prove answer correctness.")

        with col_m1:
            g_score = fact_meta.get("groundedness_score")
            g_text = f"{g_score}%" if g_score is not None else "N/A (0 claims)"
            st.markdown(f'<div class="stat-pill"><div class="stat-label">Groundedness</div><div class="stat-val">{g_text}</div></div>', unsafe_allow_html=True)

        with col_m2:
            st.markdown('<div class="stat-pill"><div class="stat-label">Exec Latency</div><div class="stat-val">' + f"{exec_meta['execution_time_ms']} ms" + '</div></div>', unsafe_allow_html=True)

        with col_m3:
            st.markdown('<div class="stat-pill"><div class="stat-label">Rows Verified</div><div class="stat-val">' + f"{exec_meta['row_count']}" + '</div></div>', unsafe_allow_html=True)

        with col_m4:
            st.markdown('<div class="stat-pill"><div class="stat-label">Auditor Verdict</div><div class="stat-val">' + f"{res['audit']['verdict']}" + '</div></div>', unsafe_allow_html=True)

        # Question-to-SQL Intent Alignment Indicator
        iv = res.get("intent_validation")
        if iv:
            if not iv.get("is_aligned", True):
                st.warning(f"⚠️ **Question-to-SQL Intent Warning**: {iv.get('summary', '')}")
            else:
                st.info(f"🎯 **Question-to-SQL Intent Aligned**: {iv.get('summary', '')}")

        # Active Engine Disclosure
        llm_meta = res.get("llm_runtime", {})
        if llm_meta.get("fallback_used", False):
            st.info("⚙️ **Engine Mode**: Deterministic Analytic Engine (Local Fallback — OpenAI API credits exhausted or offline)")
        else:
            active_p = llm_meta.get("active_provider", "LLM")
            st.caption(f"🤖 **Engine Mode**: Live Multi-Agent LLM ({active_p} - {llm_meta.get('model', '')})")

        # 2. Executive Synthesis with Audio Player
        st.markdown("### 📋 Grounded Executive Summary")

        # Text-To-Speech Web Speech API Component

        clean_speech_text = res["synthesis"].replace("###", "").replace("**", "").replace("`", "").replace("'", "\\\\'")

        tts_html = f"""

        <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 10px;">

            <button onclick="speakReport()" style="background: linear-gradient(135deg, #0284C7, #0369A1); color: white; border: none; padding: 7px 14px; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">

                🔊 Play Audio Executive Briefing

            </button>

            <button onclick="window.speechSynthesis.cancel()" style="background: rgba(255,255,255,0.1); color: #94A3B8; border: 1px solid rgba(255,255,255,0.2); padding: 7px 12px; border-radius: 8px; font-weight: 500; cursor: pointer;">

                ⏹️ Stop

            </button>

            <span id="speech-status" style="font-size: 0.85rem; color: #38BDF8;"></span>

        </div>

        <script>

            function speakReport() {{

                window.speechSynthesis.cancel();

                var text = `{clean_speech_text}`;

                var utterance = new SpeechSynthesisUtterance(text);

                utterance.rate = 1.05;

                utterance.pitch = 1.0;

                document.getElementById('speech-status').innerText = 'Playing natural audio briefing...';

                utterance.onend = function() {{

                    document.getElementById('speech-status').innerText = '';

                }};

                window.speechSynthesis.speak(utterance);

            }}

        </script>

        """

        components.html(tts_html, height=50)

        st.markdown(res["synthesis"])

        # 3. Primary Chart Preview with Kinetic Growth Motion & Controls

        charts = res.get("chart_suite", {})

        if "primary" in charts:

            st.markdown("### 📊 Kinetic Analytical Distribution & Motion Engine")

            st.caption("✨ **Realistic Kinetic Motion Active** • Click **▶ Play Growth Motion** on the chart or scrub the timeline slider below to watch growth trajectory and progression unfold dynamically.")

            if "growth_motion" in charts and charts["growth_motion"] is not charts["primary"]:

                c_mode1, c_mode2 = st.columns([3, 1])

                with c_mode2:

                    motion_view = st.radio(

                        "Motion View",

                        ["Dynamic Primary", "📈 Growth Trajectory"],

                        horizontal=True,

                        label_visibility="collapsed"

                    )

                with c_mode1:

                    pass

                active_fig = charts["growth_motion"] if motion_view == "📈 Growth Trajectory" else charts["primary"]

            else:

                active_fig = charts["primary"]

            st.plotly_chart(
                active_fig,
                use_container_width=True,
                config={"displayModeBar": True, "displaylogo": False, "responsive": True},
                key="tab1_active_chart"
            )

        # 4. Visual Verification Proof DAG

        with st.expander("🔗 Visual Verification DAG & Cryptographic Provenance", expanded=False):

            st.markdown("#### Cryptographic Execution Lineage")

            clean_q = res['question'][:25].replace('"', "'")

            clean_verdict = res['audit']['verdict']

            clean_grounding = fact_meta['groundedness_score']

            clean_data_hash = exec_meta['query_hash'][:8]

            clean_cert_hash = cert['certificate_hash'][:10]

           
            
            # Render lineage directly with Plotly (no Mermaid or CDN required)
            stages = [
                ("User Query", clean_q[:22] + "..."),
                ("Planner", "Analysis plan"),
                ("SQL Coder", "Query generation"),
                ("SQLite", "Data execution"),
                ("Data Hash", clean_data_hash),
                ("Auditor", clean_verdict[:18]),
                ("Fact Check", f"{clean_grounding}% grounded" if clean_grounding is not None else "grounding N/A"),
                ("Certificate", clean_cert_hash),
            ]

            fig_lineage = go.Figure()

            x_positions = list(range(len(stages)))
            y_positions = [0] * len(stages)

            # Connect each stage with arrows
            for i in range(len(stages) - 1):
                fig_lineage.add_annotation(
                    x=x_positions[i + 1] - 0.18,
                    y=0,
                    ax=x_positions[i] + 0.18,
                    ay=0,
                    xref="x",
                    yref="y",
                    axref="x",
                    ayref="y",
                    text="",
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1.2,
                    arrowwidth=2,
                    arrowcolor="#38BDF8",
                )

            # Draw the nodes
            fig_lineage.add_trace(go.Scatter(
                x=x_positions,
                y=y_positions,
                mode="markers+text",
                text=[
                    f"<b>{stage[0]}</b><br>{stage[1]}"
                    for stage in stages
                ],
                textposition="bottom center",
                textfont=dict(size=10, color="#F8FAFC"),
                marker=dict(
                    size=25,
                    color=[
                        "#2563EB", "#2563EB", "#2563EB", "#2563EB",
                        "#0891B2", "#7C3AED", "#7C3AED", "#059669"
                    ],
                    line=dict(color="#BAE6FD", width=1.5),
                ),
                hovertemplate="%{text}<extra></extra>",
            ))

            fig_lineage.update_layout(
                title="Verified Analysis Execution Flow",
                template="plotly_dark",
                height=330,
                margin=dict(l=35, r=35, t=60, b=105),
                showlegend=False,
                paper_bgcolor="rgba(15,23,42,0)",
                plot_bgcolor="rgba(15,23,42,0)",
                xaxis=dict(
                    visible=False,
                    range=[-0.5, len(stages) - 0.5],
                ),
                yaxis=dict(
                    visible=False,
                    range=[-0.8, 0.8],
                ),
            )

            st.plotly_chart(
                fig_lineage,
                use_container_width=True,
                config={
                    "displayModeBar": True,
                    "displaylogo": False,
                },
                key="tab1_lineage_chart"
            )

# 5. Export Report

        st.markdown("---")

        col_down1, col_down2 = st.columns(2)

        with col_down1:

            report_md = f"""# AGENT-ANALYTIX ANALYSIS REPORT

- **Question**: {res['question']}

- **Certificate Hash**: {cert['certificate_hash']}

- **Verification Certificate**: {cert['badge_text']} (Proves record was not altered; does not prove answer correctness)

- **Groundedness Score**: {f"{fact_meta['groundedness_score']}%" if fact_meta.get('groundedness_score') is not None else "N/A (0 numerical claims extracted)"}

- **Executed SQL**:&#x20;

```sql

{res['sql']}

```

## Executive Synthesis

{res['synthesis']}

"""

            st.download_button(

                "📥 Download Analysis Markdown Report",

                data=report_md,

                file_name="verified_analysis_report.md",

                mime="text/markdown",

                use_container_width=True

            )

        with col_down2:

            st.download_button(

                "🔐 Export Cryptographic Proof JSON",

                data=json.dumps(cert, indent=2),

                file_name="proof_certificate.json",

                mime="application/json",

                use_container_width=True

            )

# ==============================================================================

# TAB 2: MULTI-CHART CANVAS

# ==============================================================================

with tab_visuals:

    st.subheader("Multi-Dimensional Interactive Visual Canvas")

    st.caption("Publication-grade, interactive multi-chart representations of verified analytical findings.")

    res = st.session_state.last_analysis_result

    if not res:

        st.info("Run an analysis in the first tab to populate the multi-chart canvas.")

    else:

        charts = res.get("chart_suite", {})

        if not charts:

            st.warning("Insufficient multi-dimensional data returned to render visual suite.")

        else:

            rendered_canvas = set()

            col_v1, col_v2 = st.columns(2)

            with col_v1:
                if "donut" in charts:
                    st.plotly_chart(charts["donut"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True}, key="canvas_donut")
                    rendered_canvas.add("donut")
                elif "primary" in charts:
                    st.plotly_chart(charts["primary"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True}, key="canvas_primary")
                    rendered_canvas.add("primary")

            with col_v2:
                if "treemap" in charts and "treemap" not in rendered_canvas:
                    st.plotly_chart(charts["treemap"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True}, key="canvas_treemap")
                    rendered_canvas.add("treemap")
                elif "box" in charts and "box" not in rendered_canvas:
                    st.plotly_chart(charts["box"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True}, key="canvas_box_col2")
                    rendered_canvas.add("box")

            col_v3, col_v4 = st.columns(2)

            with col_v3:
                if "box" in charts and "box" not in rendered_canvas:
                    st.plotly_chart(charts["box"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True}, key="canvas_box_col3")
                    rendered_canvas.add("box")
                elif "growth_motion" in charts and "growth_motion" not in rendered_canvas:
                    st.plotly_chart(charts["growth_motion"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True}, key="canvas_growth_motion_col3")
                    rendered_canvas.add("growth_motion")
                elif "primary" in charts and "primary" not in rendered_canvas:
                    st.plotly_chart(charts["primary"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True}, key="canvas_primary_col3")
                    rendered_canvas.add("primary")

            with col_v4:
                if "radar" in charts and "radar" not in rendered_canvas:
                    st.plotly_chart(charts["radar"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True}, key="canvas_radar")
                    rendered_canvas.add("radar")
                elif "growth_motion" in charts and "growth_motion" not in rendered_canvas:
                    st.plotly_chart(charts["growth_motion"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True}, key="canvas_growth_motion_col4")
                    rendered_canvas.add("growth_motion")
                elif "primary" in charts and "primary" not in rendered_canvas:
                    st.plotly_chart(charts["primary"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True}, key="canvas_primary_col4")
                    rendered_canvas.add("primary")

# ==============================================================================

# TAB 3: STATISTICAL HYPOTHESES & ANOMALY DETECTOR

# ==============================================================================

with tab_stats:

    st.subheader("Automated Statistical Hypothesis Testing & Outlier Engine")

    st.caption("Empirical significance testing, p-values, 95% confidence intervals, and anomaly detection.")

    res = st.session_state.last_analysis_result

    if not res:

        st.info("Run an analysis in the first tab to view automated statistical hypothesis testing.")

    else:

        stats = res.get("statistics", {})

        if not stats.get("has_stats"):

            st.warning(stats.get("summary", "No numeric metric found for statistical tests."))

        else:

            hypo = stats["hypothesis_test"]

            # Hypothesis Card

            st.markdown("#### Formal Hypothesis Formulation")

            col_h1, col_h2 = st.columns(2)

            with col_h1:

                st.info(f"**{hypo['h0']}**")

            with col_h2:

                st.success(f"**{hypo['h1']}**")

            # Stat Metrics
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)

            with col_p1:
                top_ent = stats.get("top_entity", "Top Group")
                top_v = stats.get("top_value", 0)
                top_z_val = stats.get("top_z", 0.0)
                st.metric("Peak Group", f"{top_ent}: {top_v}", delta=f"z = {top_z_val}σ (from mean)")

            with col_p2:
                st.metric("Sample Std Dev", stats.get("std_dev", 0), delta=f"Median: {stats.get('median', 0)}")

            with col_p3:
                st.metric("Group Mean", stats.get("mean", 0), delta=f"IQR: {stats.get('iqr', 0)}")

            with col_p4:
                ci = stats.get("confidence_interval_95")
                ci_text = f"[{ci[0]}, {ci[1]}]" if ci else "N/A"
                st.metric("95% CI for Mean", ci_text, delta="μ ± 1.96·SE")

            st.markdown(f"**Statistical Interpretation**: `{stats.get('interpretation', hypo.get('conclusion', ''))}`")

            # Anomalies / Outliers Table
            st.markdown("---")

            st.markdown("#### Detected Outliers & Distribution Extremes (Tukey IQR & Standardized Z-Score)")
            st.caption("Identifies groups exceeding Tukey IQR bounds [Q1 - 1.5×IQR, Q3 + 1.5×IQR] or standardized threshold (|z| ≥ 1.8). Individual Z-scores represent standard deviations from the sample mean: z = (x - μ) / σ (never divided by standard error, which applies only to sample means). Group frequency peaks are sample modes, not causal drivers.")

            anomalies = stats.get("anomalies", [])

            if not anomalies:
                st.success("✅ No statistical outliers detected. The metric distribution is stable across segments.")
            else:
                st.dataframe(pd.DataFrame(anomalies), use_container_width=True)

# ==============================================================================

# TAB 4: WHAT-IF SENSITIVITY SIMULATOR

# ==============================================================================

with tab_simulator:

    st.subheader("Interactive 'What-If' Sensitivity & Scenario Modeling")

    st.caption("Dynamically adjust growth, conversion, or discount levers on top of the verified ground-truth baseline.")

    res = st.session_state.last_analysis_result

    if not res:
        st.info("Run an analysis in the first tab to activate sensitivity modeling on your query results, or initialize with baseline data below.")
        if st.button(f"⚡ Load Baseline Data from '{domain_cfg['table']}'", key="load_sim_baseline_btn"):
            sb_sim = SQLSandbox(domain_cfg["db"])
            sample_exec = sb_sim.execute(f'SELECT * FROM "{domain_cfg["table"]}" LIMIT 25;')
            if sample_exec.get("success") and sample_exec.get("rows"):
                st.session_state.last_analysis_result = {
                    "question": f"Baseline data preview for {domain_cfg['table']}",
                    "sql": f'SELECT * FROM "{domain_cfg["table"]}" LIMIT 25;',
                    "execution": sample_exec,
                    "synthesis": f"Baseline data preview for {domain_cfg['table']}.",
                    "proof_certificate": {
                        "badge_text": "BASELINE PREVIEW",
                        "certificate_hash": "preview"
                    }
                }
                st.rerun()
    else:
        exec_rows = res["execution"].get("rows", [])
        exec_cols = res["execution"].get("columns", [])

        if not exec_rows or len(exec_cols) < 1:
            st.warning("Insufficient baseline data for scenario simulation.")
        else:
            df_base = pd.DataFrame(exec_rows, columns=exec_cols)

            # Detect numeric columns intelligently
            numeric_cols = []
            for col in exec_cols:
                converted = pd.to_numeric(df_base[col], errors="coerce")
                if converted.notnull().sum() > 0 and (converted.notnull().sum() / max(len(df_base), 1)) >= 0.5:
                    numeric_cols.append(col)

            if not numeric_cols:
                st.warning(f"No numeric metrics detected among columns: {', '.join(exec_cols)}. Sensitivity simulation requires at least one quantitative metric.")
            else:
                dim_options = [c for c in exec_cols if c not in numeric_cols]
                if not dim_options:
                    dim_options = list(exec_cols)

                col_sel1, col_sel2 = st.columns(2)
                with col_sel1:
                    dim_col = st.selectbox("Dimension / Grouping Attribute:", exec_cols, index=0, key="sim_dim_select")
                with col_sel2:
                    val_options = [c for c in numeric_cols if c != dim_col] or numeric_cols
                    val_col = st.selectbox("Numerical Metric to Project:", val_options, index=0, key="sim_val_select")

                st.markdown(f"**Simulating Scenarios on Dimension `{dim_col}` and Metric `{val_col}`:**")

                col_sim1, col_sim2 = st.columns(2)
                with col_sim1:
                    growth_slider = st.slider("Projected Growth / Expansion (%):", min_value=-50, max_value=100, value=15, step=5)
                with col_sim2:
                    efficiency_slider = st.slider("Operational Efficiency / Cost Reduction (%):", min_value=-20, max_value=40, value=8, step=2)

                # Prepare simulation dataframe
                df_sim = df_base.copy()
                df_sim[val_col] = pd.to_numeric(df_sim[val_col], errors="coerce").fillna(0)

                # Aggregate if duplicate dimension values or many rows
                if df_sim[dim_col].duplicated().any() or len(df_sim) > 15:
                    df_sim = df_sim.groupby(dim_col, as_index=False)[val_col].sum()

                if len(df_sim) > 15:
                    df_sim = df_sim.sort_values(by=val_col, ascending=False).head(15)

                # Combined multiplier incorporating both growth and efficiency levers
                multiplier = (1.0 + (growth_slider / 100.0)) * (1.0 + (efficiency_slider / 100.0))
                df_sim["Simulated " + val_col] = df_sim[val_col] * multiplier
                df_sim["Delta"] = df_sim["Simulated " + val_col] - df_sim[val_col]

                # Render Plotly Chart
                fig_sim = go.Figure()
                fig_sim.add_trace(go.Bar(
                    x=df_sim[dim_col].astype(str),
                    y=df_sim[val_col],
                    name="Verified Baseline",
                    marker_color="#38BDF8",
                    marker_line=dict(color="#0284C7", width=1.5),
                    text=[f"{v:,.1f}" if abs(v) < 1000 else f"{v:,.0f}" for v in df_sim[val_col]],
                    textposition="outside"
                ))
                fig_sim.add_trace(go.Bar(
                    x=df_sim[dim_col].astype(str),
                    y=df_sim["Simulated " + val_col],
                    name=f"Projected (+{growth_slider}% Growth, +{efficiency_slider}% Eff)",
                    marker_color="#10B981",
                    marker_line=dict(color="#059669", width=1.5),
                    text=[f"{v:,.1f}" if abs(v) < 1000 else f"{v:,.0f}" for v in df_sim["Simulated " + val_col]],
                    textposition="outside"
                ))
                fig_sim.add_trace(go.Scatter(
                    x=df_sim[dim_col].astype(str),
                    y=df_sim["Simulated " + val_col],
                    mode="lines+markers",
                    name="Projected Trajectory",
                    line=dict(color="#10B981", width=2.5, shape="spline", smoothing=1.3),
                    marker=dict(size=8, color="#FFFFFF", line=dict(color="#10B981", width=2))
                ))
                fig_sim.update_layout(
                    barmode="group",
                    title=f"📈 <b>What-If Kinetic Projection</b>: {val_col} by {dim_col}",
                    template="plotly_dark",
                    height=450,
                    margin=dict(l=40, r=40, t=55, b=40),
                    paper_bgcolor="rgba(11, 15, 25, 0.95)",
                    plot_bgcolor="rgba(15, 23, 42, 0.55)",
                    transition=dict(duration=400, easing="cubic-in-out")
                )
                st.plotly_chart(fig_sim, use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True})

                # Impact delta metrics
                base_sum = float(df_sim[val_col].sum())
                sim_sum = float(df_sim["Simulated " + val_col].sum())
                delta_sum = sim_sum - base_sum
                net_pct = round(((multiplier - 1.0) * 100.0), 1)

                col_i1, col_i2, col_i3 = st.columns(3)
                with col_i1:
                    st.metric("Verified Baseline Total", f"{base_sum:,.2f}")
                with col_i2:
                    st.metric("Projected Total", f"{sim_sum:,.2f}", delta=f"{delta_sum:+,.2f}")
                with col_i3:
                    st.metric("Net Combined Impact", f"{net_pct:+}%")

                with st.expander("📋 View Scenario Simulation Data Table"):
                    view_df = df_sim[[dim_col, val_col, "Simulated " + val_col, "Delta"]].copy()
                    view_df.columns = [dim_col, f"Baseline {val_col}", f"Projected {val_col}", "Delta"]
                    st.dataframe(view_df, use_container_width=True)

# ==============================================================================

# TAB 5: AUDIT SANDBOX & FACT-CHECKER

# ==============================================================================

with tab_audit:

    st.subheader("Ground-Truth Audit & Hallucination Inspection Engine")

    st.caption("Inspect the exact mathematical cross-verification between agent prose claims and database row reality.")

    res = st.session_state.last_analysis_result

    if not res:

        st.info("Run an analysis in the first tab to view the live audit sandbox.")

    else:

        fact_meta = res["fact_check"]

        claims = fact_meta.get("claims_audit", [])

        col_audit1, col_audit2 = st.columns([3, 2])

        with col_audit1:

            st.markdown("#### Numerical Claims Grounding Table")

            if not claims:

                st.info(f"{fact_meta.get('message', 'No numerical claims available to verify.')} This does not establish semantic correctness.")

            else:

                audit_records = []

                for c in claims:

                    audit_records.append({

                        "Claim Token": c["token"],

                        "Parsed Value": c["value"],

                        "Grounded in DB?": "✅ TRUE" if c["matched"] else "❌ HALLUCINATION",

                        "Matched Row Value": c.get("ground_truth_match", "N/A"),

                        "Verification Status": c["status"]

                    })

                st.dataframe(pd.DataFrame(audit_records), use_container_width=True)

        with col_audit2:
            st.markdown("#### Groundedness Distribution")
            if not claims:
                st.warning("⚠️ **Groundedness Score: N/A**\n\nNo numerical claims were extracted from the prose summary to verify against database rows. Factual groundedness cannot be evaluated (0 claims extracted). With zero claims, 100% means nothing.")
            else:
                verified_count = fact_meta.get("verified_count", 0)
                ungrounded_count = fact_meta.get("ungrounded_count", 0)
                score_val = fact_meta.get("groundedness_score", 0)
                fig_pie = go.Figure(data=[go.Pie(
                    labels=["Verified Claims", "Ungrounded Claims"],
                    values=[verified_count, ungrounded_count],
                    hole=.55,
                    marker=dict(
                        colors=["#10B981", "#EF4444"],
                        line=dict(color="#0B0F19", width=2.5)
                    ),
                    textposition='inside',
                    textinfo='percent+label'
                )])
                fig_pie.add_annotation(
                    text=f"<b>{score_val}%</b><br><span style='font-size:10px; color:#94A3B8;'>GROUNDED</span>",
                    x=0.5, y=0.5,
                    font=dict(size=14, color="#F8FAFC", family="Inter, sans-serif"),
                    showarrow=False
                )
                fig_pie.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=25, b=25),
                    template="plotly_dark",
                    paper_bgcolor="rgba(11, 15, 25, 0.95)",
                    showlegend=False
                )
                st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False, "responsive": True})

        # Question-to-SQL Intent Alignment Inspection
        iv = res.get("intent_validation")
        if iv:
            st.markdown("---")
            st.markdown("#### 🎯 Question-to-SQL Intent Alignment & Semantic Inspection")
            st.caption("Verifies whether the generated SQL query actually answers the user's natural language question, checking target conditions, filters, and aggregations.")
            if not iv.get("is_aligned", True):
                st.error(f"🚨 **Intent Verification Mismatch**: {iv.get('summary')}")
                if iv.get("issues"):
                    for issue in iv["issues"]:
                        st.markdown(f"- ❌ **Discrepancy**: {issue}")
            else:
                st.success(f"✅ **Intent Verification Confirmed**: {iv.get('summary')}")
            if iv.get("warnings"):
                for w in iv["warnings"]:
                    st.warning(f"⚠️ **Note**: {w}")
            if iv.get("checks_performed"):
                st.caption(f"Evaluated checks: {', '.join(iv['checks_performed'])}")

        st.markdown("---")

        st.markdown("#### Sandboxed Query Execution & Database Ground Truth")

        exec_meta = res["execution"]

        col_sql, col_raw = st.columns([1, 1])

        with col_sql:

            st.markdown("**Executed SQL Query:**")

            st.code(res["sql"], language="sql")

            st.markdown("**Query Execution Plan (`EXPLAIN QUERY PLAN`):**")

            for plan_line in exec_meta.get("query_plan", ["SCAN TABLE"]):

                st.text(plan_line)

        with col_raw:

            st.markdown("**Raw Database Output Matrix (Ground Truth):**")

            rows = exec_meta.get("rows", [])

            cols = exec_meta.get("columns", [])

            if rows and cols:

                st.dataframe(pd.DataFrame(rows, columns=cols), height=250, use_container_width=True)

            else:

                st.warning("No rows returned from database query.")

        st.markdown("#### Cryptographic Digital Certificate (SHA-256 Provenance & Tamper-Evidence)")
        st.info("🔐 **Record Integrity Guarantee**: This SHA-256 certificate guarantees tamper-evidence and audit trail immutability (proving this execution record and raw database output have **not been altered** since runtime). It proves the record was not altered; it does **not** prove that the answer is right or that the SQL correctly captured intent.")
        cert = res["proof_certificate"]
        st.markdown(f'<div class="hash-display">Certificate Hash: {cert["certificate_hash"]}</div>', unsafe_allow_html=True)
        st.json(cert["provenance_payload"])

# ==============================================================================

# TAB 6: DATASET & SCHEMA EXPLORER

# ==============================================================================

with tab_schema:

    st.subheader(f"Data Dictionary & Schema Explorer: {domain_name}")

    db_file = domain_cfg["db"]

    table_name = domain_cfg["table"]

    try:

        conn = sqlite3.connect(db_file)

        cur = conn.cursor()

        cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')

        total_rows = cur.fetchone()[0]

        cur.execute(f'PRAGMA table_info("{table_name}")')

        col_info = cur.fetchall()

        schema_rows = []

        for col in col_info:

            col_id, col_name, col_type, not_null, default_val, pk = col

            cur.execute(f'SELECT COUNT(DISTINCT "{col_name}"), COUNT(*) - COUNT("{col_name}") FROM "{table_name}"')

            distinct_cnt, null_cnt = cur.fetchone()

            schema_rows.append({

                "Column Name": col_name,

                "Type": col_type,

                "Distinct Values": distinct_cnt,

                "Null Values": null_cnt,

                "Cardinality Flag": "⚠️ High Cardinality" if distinct_cnt > 50 else "✅ Low/Discrete"

            })

        sample_df = pd.read_sql_query(f'SELECT * FROM "{table_name}" LIMIT 50', conn)

        conn.close()

        col_st1, col_st2 = st.columns([1, 2])

        with col_st1:

            st.metric("Total Rows in Table", f"{total_rows:,}")

            st.metric("Total Columns", len(col_info))

        with col_st2:

            st.markdown("**Schema & Cardinality Breakdown:**")

            st.dataframe(pd.DataFrame(schema_rows), use_container_width=True, height=220)

        st.markdown("#### Data Sample Preview (First 50 Rows)")

        st.dataframe(sample_df, use_container_width=True, height=350)

    except Exception as e:

        st.error(f"Error accessing database: {str(e)}")

# ==============================================================================
# TAB 7: BENCHMARK & ADVERSARIAL STRESS TEST
# ==============================================================================

def get_sample_adversarial_claims(d_name, d_cfg, execution=None):
    """Generate realistic fabricated and grounded claims for the current domain."""
    table = d_cfg.get("table", "records")
    d_lower = d_name.lower()
    
    # Try to build a factually true claim from real execution rows
    true_claim = ""
    if execution and execution.get("rows") and execution.get("columns"):
        rows = execution["rows"]
        cols = execution["columns"]
        row = rows[0]
        str_part = None
        num_part = None
        for i, val in enumerate(row):
            if isinstance(val, (int, float)) and num_part is None:
                num_part = val
                num_c = cols[i]
            elif isinstance(val, str) and str_part is None and not any(ch.isdigit() for ch in val):
                str_part = val
                str_c = cols[i]
        if str_part is not None and num_part is not None:
            true_claim = f"In the verified database records, {str_c} '{str_part}' has an exact {num_c} of {num_part}."
        elif num_part is not None:
            true_claim = f"The ground-truth database records show a verified {num_c} of {num_part}."

    if "retail" in d_lower:
        fab = "The Technology category generated $10,000,000 in sales and achieved a 95% profit margin in 2025, making it the most profitable category."
        gro = true_claim or "Office Supplies generated 393199.37 in total sales and 79922.17 in profit across 3 segments."
    elif "heart" in d_lower:
        fab = "Patients over age 80 exhibited an average resting blood pressure of 240 mm Hg with a 98% heart disease prevalence."
        gro = true_claim or "In this clinical cohort, patient ages range from 28 to 77 years with resting blood pressure values up to 200 mm Hg."
    elif "fraud" in d_lower:
        fab = "Total fraudulent transactions amounted to $450,000,000 across 99,000 flagged accounts in 2024."
        gro = true_claim or "The transaction monitoring dataset tracks verified financial records with transaction amounts audited in the SQLite sandbox."
    elif "crypto" in d_lower:
        fab = "Bitcoin surged to $250,000 with a 24-hour transaction volume exceeding $1.5 trillion on Binance."
        gro = true_claim or "The live cryptocurrency feed streams 24-hour ticker price change percentages and volumes."
    elif "hr" in d_lower:
        fab = "The engineering department experienced an 85% attrition rate with average monthly income falling to $1,200."
        gro = true_claim or "HR employee records track monthly income and attrition across company departments."
    else:
        fab = f"This dataset records 50,000,000 entries with a 99.9% conversion rate across all records in {table}."
        gro = true_claim or f"Records in table '{table}' are validated directly against SQLite execution output."

    return fab, gro

with tab_stress:
    st.subheader("Verification Benchmark & Adversarial Hallucination Stress Test")
    st.caption("Demonstrate how the framework systematically catches and flags ungrounded claims.")
    st.markdown("### 🥊 Adversarial Hallucination Injection Simulator")
    st.markdown(
        """
        > 🧪 **Hallucination Detection Stress Test Bench**  
        > This tool tests whether the Deterministic Fact-Checking Engine can catch **fabricated numbers and ungrounded claims** without trusting the LLM.  
        >  
        > 💡 *Notice: This is not an analysis query box. To ask questions and query your data, use the **🚀 Verifiable Analysis** tab. Use this simulator to audit whether a quantitative statement or report matches the underlying database records.*
        """
    )

    active_result = st.session_state.last_analysis_result
    has_active_query = (active_result is not None and active_result.get("execution", {}).get("success"))

    if has_active_query:
        real_exec = active_result["execution"]
        ref_context_text = f"Current query: **'{active_result['question']}'** on table `{domain_cfg['table']}` in `{domain_cfg['db']}`."
    else:
        sb_stress = SQLSandbox(domain_cfg["db"])
        tbl_stress = domain_cfg["table"]
        real_exec = sb_stress.execute(f'SELECT * FROM "{tbl_stress}" LIMIT 10;')
        ref_context_text = f"Ground-truth table: `{tbl_stress}` in `{domain_cfg['db']}` (baseline rows)."

    fab_sample, gro_sample = get_sample_adversarial_claims(domain_name, domain_cfg, real_exec)

    st.markdown("**Quick Load Test Claims for Active Domain:**")
    col_claim_b1, col_claim_b2 = st.columns(2)
    with col_claim_b1:
        if st.button("🚨 Load Fabricated Claim (Adversarial Hallucination)", use_container_width=True, key="btn_load_fab"):
            st.session_state.adv_input_claim = fab_sample
            st.rerun()
    with col_claim_b2:
        if st.button("✅ Load Grounded Claim (Fact-Checked)", use_container_width=True, key="btn_load_gro"):
            st.session_state.adv_input_claim = gro_sample
            st.rerun()

    col_sim1, col_sim2 = st.columns([3, 2])
    with col_sim1:
        default_claim_val = st.session_state.get("adv_input_claim", fab_sample)
        simulated_claim = st.text_area(
            "Enter quantitative text or claim with potential hallucinations:",
            value=default_claim_val,
            height=110,
            key="adv_claim_input_text"
        )
    with col_sim2:
        st.markdown("**Ground-Truth Reference Context:**")
        st.write(ref_context_text)
        sim_run = st.button("🧪 Run Adversarial Detection Test", type="primary", use_container_width=True)

    with st.expander("🔍 View Ground-Truth Reference Rows & SQL"):
        if has_active_query and "sql" in active_result:
            st.code(active_result["sql"], language="sql")
        if real_exec.get("rows"):
            st.dataframe(pd.DataFrame(real_exec["rows"], columns=real_exec["columns"]), use_container_width=True)

    if sim_run and simulated_claim:
        adversarial_audit = DeterministicFactChecker.verify_claims(simulated_claim, real_exec)

        st.markdown("#### Verification Engine Verdict:")
        adv_status = adversarial_audit["status"]
        adv_score = adversarial_audit["groundedness_score"]

        if adv_status == "NO_CLAIMS_TO_VERIFY" or adv_score is None:
            st.info(
                "ℹ️ **No Numerical Claims Detected to Audit**\n\n"
                "The text you submitted does not contain any numbers, figures, or percentages.\n\n"
                "• The Stress Testing engine checks **quantitative claims** (e.g. '$10M sales' or '95% margin') against ground-truth database rows.\n"
                "• If you intended to **ask a question** about your dataset, please switch to the **🚀 Verifiable Analysis** tab!"
            )
        elif adv_status == "HALLUCINATION_DETECTED":
            st.error(f"🚨 **HALLUCINATION DETECTED!** Groundedness Score: **{adv_score}%**")
            st.markdown(
                f"The verification engine caught **{adversarial_audit.get('ungrounded_count', 0)} fabricated number(s)** "
                "that have **no grounding** in the real database."
            )
        elif adv_status == "FULLY_GROUNDED":
            st.success(f"✅ **FULLY GROUNDED!** Groundedness Score: **{adv_score}%**")
            st.markdown(
                f"All **{adversarial_audit.get('verified_count', 0)} quantitative figures** were confirmed "
                "in the ground-truth database records."
            )
        else:
            st.warning(f"⚠️ Status: **{adv_status}** | Groundedness Score: **{adv_score}%**")

        if adversarial_audit.get("claims_audit"):
            st.markdown("**Claims Audit Breakdown:**")
            st.dataframe(pd.DataFrame(adversarial_audit["claims_audit"]), use_container_width=True)

# ==============================================================================
# TAB 8: ACADEMIC FRAMEWORK & METHODOLOGY
# ==============================================================================

with tab_paper:
    st.subheader("Academic Framework: Formal Verification Architecture")

    st.markdown(r"""
    ### 1. Abstract & Problem Formulation
    Autonomous data analysis with LLMs frequently produces plausible yet **ungrounded conclusions**, 
    **hallucinated metrics**, and **fabricated execution logs**. This framework formalizes a 
    **Multi-Agent Verification Architecture** that enforces deterministic execution, adversarial 
    cross-auditing, mathematical fact-checking, and cryptographic proof of verification.

    ### 2. Multi-Agent Formal Roles
    1. **Hypothesis & Planning Agent ($\mathcal{A}_{\text{plan}}$)**:
       Deconstructs natural language queries into a formal Directed Acyclic Graph (DAG) of analytical hypotheses.
    2. **SQL Coder Agent ($\mathcal{A}_{\text{code}}$)**:
       Translates the plan into dialect-aware, sandboxed SQL queries with defensive constraints (zero integer division truncation, strict LIMIT bounds).
    3. **Sandboxed Execution Engine ($\mathcal{E}_{\text{sql}}$)**:
       Executes read-only queries in an isolated SQLite environment, records execution latency, and computes a cryptographic SHA-256 fingerprint $H_{\text{data}}$ of raw rows.
    4. **Adversarial Auditor Agent ($\mathcal{A}_{\text{audit}}$)**:
       Operates under a zero-trust model, validating semantic consistency, boundary correctness, and counter-factual hypotheses.
    5. **Statistical Engine ($\mathcal{S}_{\text{stat}}$)**:
       Computes formal hypothesis tests ($H_0/H_1$), p-values, 95% confidence intervals, and anomaly IQR dispersion.
    6. **Deterministic Fact-Checking Engine ($\mathcal{V}_{\text{fact}}$)**:
       A non-LLM algorithmic validator that extracts all numerical claims $\mathcal{C} = \{c_1, c_2, \dots, c_n\}$ from the synthesized text and validates them against the ground-truth result set $\mathcal{T}$.
    7. **Cryptographic Proof Generator ($\mathcal{P}_{\text{cert}}$)**:
       Issues a verifiable digital certificate:
    """)

    st.latex(r"\mathcal{H}_{\text{cert}} = \text{SHA-256}(\text{Timestamp} \parallel \text{Query} \parallel \text{SQL} \parallel H_{\text{data}} \parallel \text{Verdict} \parallel \text{Score})")

    st.markdown("### 3. Comparison Matrix")

    comp_df = pd.DataFrame([
        {"Feature": "Hallucination Resistance", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ Low (Fabricates rows & counts)", "AGENT-ANALYTIX Multi-Agent": "⚠️ Requires independent query validation"},
        {"Feature": "Execution Auditability", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ None (Black-box prose)", "AGENT-ANALYTIX Multi-Agent": "✅ Full SQL sandbox & query plan logs"},
        {"Feature": "Numerical Grounding", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ Unchecked (Numbers invented)", "AGENT-ANALYTIX Multi-Agent": "⚠️ Numeric matching only; not semantic proof"},
        {"Feature": "Adversarial Critique", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ Self-confirmatory bias", "AGENT-ANALYTIX Multi-Agent": "✅ Dedicated Adversarial Auditor Agent"},
        {"Feature": "Statistical Testing", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ Fabricated or absent", "AGENT-ANALYTIX Multi-Agent": "⚠️ Descriptive statistics where supported"},
        {"Feature": "Proof of Lineage", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ Absent", "AGENT-ANALYTIX Multi-Agent": "✅ Cryptographic SHA-256 Certificate"}
    ])

    st.table(comp_df)

    st.markdown("### 4. Mathematical Groundedness Formulation")

    st.latex(r"\text{Groundedness Score}(\mathcal{C}, \mathcal{T}) = \frac{|\{c \in \mathcal{C} \mid \exists t \in \mathcal{T} \text{ s.t. } |c - t| \le \epsilon \cdot |t|\}|}{|\mathcal{C}|} \times 100\%")

    st.caption(r"Where $\epsilon$ is the floating-point relative tolerance parameter (default $\epsilon = 0.015$).")

    # Section 5: Dynamic Domain-Specific Invariance Formalization
    st.markdown(f"### 5. Domain-Specific Invariance & Verification Formalization: {domain_name}")

    try:
        sb_paper = SQLSandbox(domain_cfg["db"])
        tbl_paper = domain_cfg["table"]
        schema_paper = sb_paper.get_schema(tbl_paper)
        count_exec = sb_paper.execute(f'SELECT COUNT(*) as total_rows FROM "{tbl_paper}";')
        total_rows = count_exec["rows"][0][0] if count_exec.get("success") and count_exec.get("rows") else "N/A"

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.metric("Target Table", f"{tbl_paper}")
        with col_p2:
            st.metric("Total Records (N)", f"{total_rows:,}" if isinstance(total_rows, (int, float)) else str(total_rows))
        with col_p3:
            st.metric("Schema Attributes (M)", f"{len(schema_paper)} columns")

        st.markdown(f"**Formal Invariant Constraints for Active Domain:** `{domain_name}`")
        attr_rows = []
        for col_info in schema_paper:
            c_name = col_info["name"]
            c_type = col_info["type"].upper()
            is_num = any(t in c_type for t in ["INT", "REAL", "FLOAT", "NUM", "DECIMAL"])
            if is_num:
                rule = "Bounded interval min(x) <= mu <= max(x), non-negative check"
            else:
                rule = "Categorical cardinality bound, discrete set membership"
            attr_rows.append({"Attribute": c_name, "Data Type": c_type, "Verification Invariant Rule": rule})
        st.dataframe(pd.DataFrame(attr_rows), use_container_width=True)

        st.markdown(r"""
        **Domain Verification Guarantees:**
        - **Schema Invariance:** Any query proposed by $\mathcal{A}_{\text{code}}$ must strictly conform to the relation $\mathcal{R}_{\text{target}}$ without accessing unauthorized external databases.
        - **Zero-Division & Cohort Protection:** Denominators and aggregation group filters are defensively verified to avoid undefined execution exceptions.
        - **Deterministic Extraction Lineage:** Every metric presented in Tab 1 undergoes strict algorithmic matching against tuples extracted from $\mathcal{R}_{\text{target}}$.
        """)
    except Exception as e:
        st.caption(f"Domain invariant inspection unavailable: {e}")
