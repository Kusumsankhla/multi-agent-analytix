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
    st.markdown("**📂 Target Domain**")
    domain_name = st.selectbox("Choose Benchmark Domain", list(DOMAINS.keys()), label_visibility="collapsed")
    domain_cfg = DOMAINS[domain_name]
    st.caption(f"_{domain_cfg['desc']}_")

    # Live Crypto Refresh
    if "Live Crypto" in domain_name:
        if st.button("🔄 Fetch Live 24hr Binance Feed", use_container_width=True):
            with st.spinner("Streaming real-time ticker prices from Binance..."):
                try:
                    df_live = fetch_live_crypto_data()
                    conn = sqlite3.connect("crypto_data.db")
                    df_live.to_sql("coins", conn, if_exists="replace", index=False)
                    conn.close()
                    st.success(f"Streamed {len(df_live)} live tickers into crypto_data.db!")
                except Exception as e:
                    st.error(f"Feed error: {e}")

    # Custom File Uploader
    st.markdown("---")
    st.markdown("**📤 Ingest Custom CSV**")
    uploaded_file = st.file_uploader("Upload CSV for Verifiable Analysis", type=["csv"], label_visibility="collapsed")
    if uploaded_file is not None:
        try:
            custom_df = pd.read_csv(uploaded_file, encoding="latin1")
            custom_db = "custom_data.db"
            custom_table = "custom_records"
            conn = sqlite3.connect(custom_db)
            custom_df.to_sql(custom_table, conn, if_exists="replace", index=False)
            conn.close()
            st.success(f"Indexed '{uploaded_file.name}' ({len(custom_df)} rows)!")
            use_custom = st.checkbox("Analyze uploaded dataset", value=True)
            if use_custom:
                domain_cfg = {
                    "db": custom_db,
                    "table": custom_table,
                    "desc": f"Custom dataset '{uploaded_file.name}' with {len(custom_df)} rows.",
                    "sample_questions": [f"What are the top 5 records by {custom_df.columns[0]}?"]
                }
        except Exception as e:
            st.error(f"Error parsing uploaded file: {e}")

# Header
st.markdown('<div class="hero-title">AGENT-ANALYTIX</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">A Multi-Agent Framework for Verifiable Autonomous Data Analysis Using Large Language Models</div>', unsafe_allow_html=True)

# Main Navigation Tabs
tab_analysis, tab_visuals, tab_stats, tab_simulator, tab_audit, tab_schema, tab_stress, tab_paper = st.tabs([
    "🚀 Verifiable Analysis",
    "📊 Multi-Chart Canvas",
    "📐 Statistical Hypotheses",
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
                "COMPLETE": (100, "✅ Verifiable Pipeline Execution Successfully Certified!")
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
                status_text.success("🎉 Analysis & Ground-Truth Verification Successfully Certified!")
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
            st.caption(f"SHA-256 Certificate: `{cert['certificate_hash'][:22]}...`")

        with col_m1:
            st.markdown('<div class="stat-pill"><div class="stat-label">Groundedness</div><div class="stat-val">' + f"{fact_meta['groundedness_score']}%" + '</div></div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown('<div class="stat-pill"><div class="stat-label">Exec Latency</div><div class="stat-val">' + f"{exec_meta['execution_time_ms']} ms" + '</div></div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown('<div class="stat-pill"><div class="stat-label">Rows Verified</div><div class="stat-val">' + f"{exec_meta['row_count']}" + '</div></div>', unsafe_allow_html=True)
        with col_m4:
            st.markdown('<div class="stat-pill"><div class="stat-label">Auditor Verdict</div><div class="stat-val">' + f"{res['audit']['verdict']}" + '</div></div>', unsafe_allow_html=True)

        # 2. Executive Synthesis with Audio Player
        st.markdown("### 📋 Grounded Executive Summary")
        
        # Text-To-Speech Web Speech API Component
        clean_speech_text = res["synthesis"].replace("###", "").replace("**", "").replace("`", "").replace("'", "\\'")
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
                config={"displayModeBar": True, "displaylogo": False, "responsive": True}
            )

        # 4. Visual Verification Proof DAG
        with st.expander("🔗 Visual Verification DAG & Cryptographic Provenance", expanded=False):
            st.markdown("#### Cryptographic Execution Lineage")
            clean_q = res['question'][:25].replace('"', "'")
            clean_verdict = res['audit']['verdict']
            clean_grounding = fact_meta['groundedness_score']
            clean_data_hash = exec_meta['query_hash'][:8]
            clean_cert_hash = cert['certificate_hash'][:10]
            
            mermaid_svg_html = f"""
            <div id="mermaid-container" style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 12px; display: flex; justify-content: center; overflow-x: auto;">
                <pre class="mermaid" style="background: transparent;">
                flowchart LR
                    Q["❓ Query: {clean_q}..."] --> P["🎯 Planner DAG"]
                    P --> C["💻 Coder SQL"]
                    C --> S["⚡ Sandboxed SQLite"]
                    S --> H["🔒 Data: {clean_data_hash}..."]
                    H --> A["🕵️ Auditor: {clean_verdict}"]
                    A --> F["🔬 Fact: {clean_grounding}%"]
                    F --> Cert["🛡️ Cert: {clean_cert_hash}..."]

                    classDef default fill:#1E293B,stroke:#38BDF8,stroke-width:1.5px,color:#F8FAFC;
                    classDef cert fill:#065F46,stroke:#10B981,stroke-width:2px,color:#A7F3D0;
                    class Cert cert;
                </pre>
            </div>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
            </script>
            """
            components.html(mermaid_svg_html, height=160)

        # 5. Export Report
        st.markdown("---")
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            report_md = f"""# AGENT-ANALYTIX VERIFIED REPORT
- **Question**: {res['question']}
- **Certificate Hash**: {cert['certificate_hash']}
- **Verification Status**: {cert['badge_text']}
- **Groundedness Score**: {fact_meta['groundedness_score']}%
- **Executed SQL**: 
```sql
{res['sql']}
```

## Executive Synthesis
{res['synthesis']}
"""
            st.download_button(
                "📥 Download Verified Markdown Report",
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
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                if "donut" in charts:
                    st.plotly_chart(charts["donut"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True})
                elif "primary" in charts:
                    st.plotly_chart(charts["primary"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True})
            with col_v2:
                if "treemap" in charts:
                    st.plotly_chart(charts["treemap"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True})
                elif "box" in charts:
                    st.plotly_chart(charts["box"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True})

            col_v3, col_v4 = st.columns(2)
            with col_v3:
                if "box" in charts and "treemap" in charts:
                    st.plotly_chart(charts["box"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True})
                elif "growth_motion" in charts:
                    st.plotly_chart(charts["growth_motion"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True})
            with col_v4:
                if "radar" in charts:
                    st.plotly_chart(charts["radar"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True})
                elif "growth_motion" in charts and ("box" not in charts or "treemap" not in charts):
                    st.plotly_chart(charts["growth_motion"], use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True})

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
                st.metric("Test Statistic (Z)", hypo["test_statistic"])
            with col_p2:
                sig_text = "p < 0.05 (Significant)" if hypo["significant"] else "p >= 0.05"
                st.metric("p-value", hypo["p_value"], delta=sig_text)
            with col_p3:
                st.metric("Group Mean", stats["mean"])
            with col_p4:
                st.metric("95% CI for Mean", f"[{stats['confidence_interval_95'][0]}, {stats['confidence_interval_95'][1]}]")

            st.markdown(f"**Statistical Decision**: `{hypo['conclusion']}`")

            # Anomalies / Outliers Table
            st.markdown("---")
            st.markdown("#### Detected Outliers & Anomalies (|z| >= 1.8)")
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
        st.info("Run an analysis in the first tab to activate the sensitivity simulator.")
    else:
        exec_rows = res["execution"].get("rows", [])
        exec_cols = res["execution"].get("columns", [])
        
        if not exec_rows or len(exec_cols) < 2:
            st.warning("Insufficient baseline data for scenario simulation.")
        else:
            df_base = pd.DataFrame(exec_rows, columns=exec_cols)
            dim_col = exec_cols[0]
            val_col = exec_cols[1]
            
            st.markdown(f"**Simulating Scenarios on Dimension `{dim_col}` and Metric `{val_col}`:**")
            
            col_sim1, col_sim2 = st.columns(2)
            with col_sim1:
                growth_slider = st.slider("Projected Growth / Expansion (%):", min_value=-50, max_value=100, value=15, step=5)
            with col_sim2:
                efficiency_slider = st.slider("Operational Efficiency / Cost Reduction (%):", min_value=-20, max_value=40, value=8, step=2)

            # Recalculate simulated values
            multiplier = 1.0 + (growth_slider / 100.0)
            df_sim = df_base.copy()
            
            if pd.api.types.is_numeric_dtype(df_sim[val_col]) or any(isinstance(v, (int, float)) for v in df_sim[val_col]):
                df_sim[val_col] = pd.to_numeric(df_sim[val_col], errors="coerce")
                df_sim["Simulated " + val_col] = df_sim[val_col] * multiplier

                fig_sim = go.Figure()
                fig_sim.add_trace(go.Bar(
                    x=df_sim[dim_col],
                    y=df_sim[val_col],
                    name="Verified Baseline",
                    marker_color="#38BDF8",
                    marker_line=dict(color="#0284C7", width=1.5),
                    text=[f"{v:,.0f}" for v in df_sim[val_col]],
                    textposition="outside"
                ))
                fig_sim.add_trace(go.Bar(
                    x=df_sim[dim_col],
                    y=df_sim["Simulated " + val_col],
                    name=f"Projected (+{growth_slider}%)",
                    marker_color="#10B981",
                    marker_line=dict(color="#059669", width=1.5),
                    text=[f"{v:,.0f}" for v in df_sim["Simulated " + val_col]],
                    textposition="outside"
                ))
                fig_sim.add_trace(go.Scatter(
                    x=df_sim[dim_col],
                    y=df_sim["Simulated " + val_col],
                    mode="lines+markers",
                    name="Projected Trajectory",
                    line=dict(color="#10B981", width=2.5, shape="spline", smoothing=1.3),
                    marker=dict(size=8, color="#FFFFFF", line=dict(color="#10B981", width=2))
                ))
                fig_sim.update_layout(
                    barmode="group",
                    title=f"📈 <b>What-If Kinetic Projection</b>: {val_col} under +{growth_slider}% Growth",
                    template="plotly_dark",
                    height=450,
                    margin=dict(l=40, r=40, t=55, b=40),
                    paper_bgcolor="rgba(11, 15, 25, 0.95)",
                    plot_bgcolor="rgba(15, 23, 42, 0.55)",
                    transition=dict(duration=400, easing="cubic-in-out")
                )
                st.plotly_chart(fig_sim, use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "responsive": True})
                
                # Impact delta
                base_sum = df_sim[val_col].sum()
                sim_sum = df_sim["Simulated " + val_col].sum()
                delta_sum = sim_sum - base_sum
                
                col_i1, col_i2, col_i3 = st.columns(3)
                with col_i1:
                    st.metric("Verified Baseline Total", f"{round(base_sum, 2):,}")
                with col_i2:
                    st.metric("Projected Total", f"{round(sim_sum, 2):,}", delta=f"{round(delta_sum, 2):,}")
                with col_i3:
                    st.metric("Net Projected Change", f"{growth_slider}%")

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
                st.success("No numerical claims were extracted or qualitative analysis confirmed.")
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
            verified_count = fact_meta.get("verified_count", 0)
            ungrounded_count = fact_meta.get("ungrounded_count", 0)
            
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
                text=f"<b>{fact_meta.get('groundedness_score', 0)}%</b><br><span style='font-size:10px; color:#94A3B8;'>GROUNDED</span>",
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

        st.markdown("#### Cryptographic Digital Certificate (SHA-256 Provenance)")
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
with tab_stress:
    st.subheader("Verification Benchmark & Adversarial Hallucination Stress Test")
    st.caption("Demonstrate how the framework systematically catches and flags ungrounded claims.")

    st.markdown("### 🥊 Adversarial Hallucination Injection Simulator")
    st.write(
        "Inject custom text with fabricated statistics into the verification engine to see how it "
        "detects hallucinations without trusting the LLM."
    )

    col_sim1, col_sim2 = st.columns([3, 2])
    with col_sim1:
        simulated_claim = st.text_area(
            "Enter text with potential hallucinations:",
            value="Our fraud rate exploded to 88.5% across 950,000 transactions with $45.2M in unauthorized transfers.",
            height=120
        )
    with col_sim2:
        st.markdown("**Ground-Truth Reference Context:**")
        st.write("Current selected table: `" + domain_cfg["table"] + "` in `" + domain_cfg["db"] + "`.")
        sim_run = st.button("🧪 Run Adversarial Detection Test", type="primary")

    if sim_run and simulated_claim:
        if st.session_state.last_analysis_result and st.session_state.last_analysis_result.get("execution", {}).get("success"):
            real_exec = st.session_state.last_analysis_result["execution"]
            st.info(f"Evaluating claim against active analysis query: `{st.session_state.last_analysis_result['sql']}`")
        else:
            sb = SQLSandbox(domain_cfg["db"])
            tbl = domain_cfg["table"]
            real_exec = sb.execute(f'SELECT * FROM "{tbl}" LIMIT 5;')
            st.info(f"Evaluating claim against baseline dataset rows from `{tbl}`.")

        adversarial_audit = DeterministicFactChecker.verify_claims(simulated_claim, real_exec)

        st.markdown("#### Verification Engine Verdict:")
        adv_status = adversarial_audit["status"]
        adv_score = adversarial_audit["groundedness_score"]

        if adv_status == "HALLUCINATION_DETECTED":
            st.error(f"🚨 **HALLUCINATION DETECTED!** Groundedness Score: **{adv_score}%**")
            st.markdown(f"The verification engine successfully identified that the numbers in the statement have **no grounding** in the real database.")
        elif adv_status == "FULLY_GROUNDED":
            st.success(f"✅ **FULLY GROUNDED!** Groundedness Score: **{adv_score}%**")
        else:
            st.warning(f"⚠️ Status: **{adv_status}** | Groundedness Score: **{adv_score}%**")

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
    1. **Hypothesis & Planning Agent ($\mathcal{A}_{plan}$)**:
       Deconstructs natural language queries into a formal Directed Acyclic Graph (DAG) of analytical hypotheses.
    2. **SQL Coder Agent ($\mathcal{A}_{code}$)**:
       Translates the plan into dialect-aware, sandboxed SQL queries with defensive constraints (zero integer division truncation, strict LIMIT bounds).
    3. **Sandboxed Execution Engine ($\mathcal{E}_{sql}$)**:
       Executes read-only queries in an isolated SQLite environment, records execution latency, and computes a cryptographic SHA-256 fingerprint $H_{data}$ of raw rows.
    4. **Adversarial Auditor Agent ($\mathcal{A}_{audit}$)**:
       Operates under a zero-trust model, validating semantic consistency, boundary correctness, and counter-factual hypotheses.
    5. **Statistical Engine ($\mathcal{S}_{stat}$)**:
       Computes formal hypothesis tests ($H_0/H_1$), p-values, 95% confidence intervals, and anomaly IQR dispersion.
    6. **Deterministic Fact-Checking Engine ($\mathcal{V}_{fact}$)**:
       A non-LLM algorithmic validator that extracts all numerical claims $\mathcal{C} = \{c_1, c_2, \dots, c_n\}$ from the synthesized text and validates them against the ground-truth result set $\mathcal{T}$.
    7. **Cryptographic Proof Generator ($\mathcal{P}_{cert}$)**:
       Issues a verifiable digital certificate:
       $$\mathcal{H}_{cert} = \text{SHA-256}(\text{Timestamp} \parallel \text{Query} \parallel \text{SQL} \parallel H_{data} \parallel \text{Verdict} \parallel \text{Score})$$

    ### 3. Comparison Matrix
    """)

    comp_df = pd.DataFrame([
        {"Feature": "Hallucination Resistance", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ Low (Fabricates rows & counts)", "AGENT-ANALYTIX Multi-Agent": "✅ 100% Deterministic Ground-Truth"},
        {"Feature": "Execution Auditability", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ None (Black-box prose)", "AGENT-ANALYTIX Multi-Agent": "✅ Full SQL sandbox & query plan logs"},
        {"Feature": "Numerical Grounding", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ Unchecked (Numbers invented)", "AGENT-ANALYTIX Multi-Agent": "✅ Algorithmic entity extraction & cross-check"},
        {"Feature": "Adversarial Critique", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ Self-confirmatory bias", "AGENT-ANALYTIX Multi-Agent": "✅ Dedicated Adversarial Auditor Agent"},
        {"Feature": "Statistical Testing", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ Fabricated or absent", "AGENT-ANALYTIX Multi-Agent": "✅ Automated H0/H1, p-values & Z-scores"},
        {"Feature": "Proof of Lineage", "Single-Agent LLM (ChatGPT / PandasAI)": "❌ Absent", "AGENT-ANALYTIX Multi-Agent": "✅ Cryptographic SHA-256 Certificate"}
    ])
    st.table(comp_df)

    st.markdown(r"""
    ### 4. Mathematical Groundedness Formulation
    $$\text{Groundedness Score}(\mathcal{C}, \mathcal{T}) = \frac{|\{c \in \mathcal{C} \mid \exists t \in \mathcal{T} \text{ s.t. } |c - t| \le \epsilon \cdot |t|\}|}{|\mathcal{C}|} \times 100\%$$
    Where $\epsilon$ is the floating-point tolerance parameter (default $\epsilon = 0.015$).
    """)