# AGENT-ANALYTIX: A Multi-Agent Framework for Verifiable Autonomous Data Analysis Using Large Language Models

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit App](https://img.shields.io/badge/Streamlit-UI-FF4B4B.svg)](https://streamlit.io/)
[![Verification Status](https://img.shields.io/badge/Ground--Truth-100%25%20Verifiable-success.svg)](#verification-protocol)

---

## 📖 Executive Summary

Autonomous data analysis systems powered by Large Language Models (LLMs) (e.g., Code Interpreters, PandasAI, Text2SQL, AutoGPT) frequently suffer from three critical failure modes:
1. **Unchecked Hallucination of Metrics**: Fabricating plausible-sounding numbers, averages, and counts not present in the underlying dataset.
2. **Fabricated Execution Trails**: Pretending that code or queries were executed when they were not, or generating synthetic outputs.
3. **Absence of Verifiable Lineage**: Providing answers without cryptographic, tamper-evident lineage linking claims back to row-level database ground truth.

**AGENT-ANALYTIX** introduces a **Multi-Agent Verification Architecture** that decomposes autonomous data analysis into specialized agent roles with an **Adversarial Audit Loop**, **Deterministic (Non-LLM) Numerical Grounding**, and **Cryptographic Proof of Verification Certificates (SHA-256)**.

---

## 🏛️ System Architecture

```
                             User Business Question
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │      Planner Agent            │
                       │ (Hypothesis & DAG Decomp)     │
                       └───────────────┬───────────────┘
                                       │ Analytical Plan
                                       ▼
                       ┌───────────────────────────────┐
                       │        Coder Agent            │
                       │  (Dialect-Safe SQL Generator) │
                       └───────────────┬───────────────┘
                                       │ SQL Query
                                       ▼
                       ┌───────────────────────────────┐
                       │  Sandboxed Execution Engine   │
                       │   (Read-Only SQLite Sandbox)  │
                       └───────────────┬───────────────┘
                                       │ Raw Output & Data Hash (H_data)
                    ┌──────────────────┴──────────────────┐
                    │                                     │
                    ▼                                     ▼
     ┌───────────────────────────────┐     ┌───────────────────────────────┐
     │   Adversarial Auditor Agent   │     │  Deterministic Fact-Checker   │
     │  (Zero-Trust Semantic Audit,  │     │ (Algorithmic Entity Extractor,│
     │   Boundary & Division Checks) │     │   Numerical Matching Engine)  │
     └──────────────┬────────────────┘     └──────────────┬────────────────┘
                    │ Auditor Verdict                     │ Groundedness Score
                    └──────────────────┬──────────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │    Synthesis & Visualizer     │
                       │ (Grounded Report & Plotly)    │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  Cryptographic Proof Engine   │
                       │  (SHA-256 Tamper-Proof Cert)  │
                       └───────────────────────────────┘
```

---

## 🤖 Multi-Agent Roles & Specialization

| Agent | Formal Designation | Core Responsibilities |
|---|---|---|
| **Planner Agent** | $\mathcal{A}_{plan}$ | Deconstructs ambiguous business questions into structured analytical hypotheses; inspects schemas and flags high-cardinality columns. |
| **Coder Agent** | $\mathcal{A}_{code}$ | Generates dialect-safe, read-only SQL queries; enforces defensive execution rules (preventing integer division truncation and unbounded queries). |
| **Sandboxed Execution Engine** | $\mathcal{E}_{sql}$ | Sandboxes query execution, enforces single-statement read-only safety, profiles latency (ms), and computes SHA-256 result hashes. |
| **Adversarial Auditor Agent** | $\mathcal{A}_{audit}$ | Operates under a zero-trust model; scrutinizes query semantics, tests boundary conditions, and issues formal verdicts (`CONFIRMED` or `FLAGGED`). |
| **Deterministic Fact-Checker** | $\mathcal{V}_{fact}$ | Non-LLM algorithmic validator that extracts all numerical entities from the prose and cross-checks them against raw query rows. |
| **Synthesis & Visualizer** | $\mathcal{A}_{synth}$ | Compiles executive insights with empirical citations and constructs interactive Plotly chart specifications. |
| **Proof Generator** | $\mathcal{P}_{cert}$ | Issues a cryptographically signed SHA-256 Verification Certificate guaranteeing tamper-evident analytical provenance. |

---

## 📐 Mathematical Formulation: Factual Groundedness

Let the synthesized prose report contain a set of extracted numerical claims:
$$\mathcal{C} = \{c_1, c_2, \dots, c_n\}$$

Let the sandboxed database execution return a ground-truth value matrix:
$$\mathcal{T} = \{t_1, t_2, \dots, t_m\}$$

A claim $c_i$ is **Grounded** if and only if there exists a ground-truth value $t_j \in \mathcal{T}$ such that:
$$|c_i - t_j| \le \epsilon \cdot |t_j| + \delta$$
*(where $\epsilon = 0.01$ is the relative tolerance and $\delta = 0.01$ is the absolute tolerance for rounding).*

The **Factual Groundedness Score** is defined as:
$$\text{Groundedness Score}(\mathcal{C}, \mathcal{T}) = \frac{|\{c \in \mathcal{C} \mid c \text{ is Grounded in } \mathcal{T}\}|}{|\mathcal{C}|} \times 100\%$$

If $|\mathcal{C}| = 0$ (qualitative response), the score defaults to $100\%$ with a qualitative badge. If the query failed or returned no tools, the score is $0\%$.

---

## 🔐 Cryptographic Proof of Verification

Every analysis generates a verifiable digital certificate:
$$\mathcal{H}_{cert} = \text{SHA-256}(\text{Timestamp} \parallel \text{Question} \parallel \text{SQL} \parallel \mathcal{H}(Data) \parallel \text{Verdict} \parallel \text{Score})$$

This certificate provides an immutable proof-of-lineage that can be archived, audited, and independently verified without sharing proprietary underlying data.

---

## 📊 Benchmark Domains Out of the Box

| Domain | Database / Source | Records | Sample Question |
|---|---|---|---|
| **🏬 Retail Superstore** | `retail_data.db` (`orders`) | 5,000 | *"What are the top 3 categories by total sales and profit?"* |
| **👥 HR Analytics** | `hr_data.db` (`employees`) | 3,000 | *"What is the attrition rate across different departments?"* |
| **🏦 FinTech Loan Risk** | `loan_data.db` (`loans`) | 4,000 | *"What is the default rate by loan grade?"* |
| **💳 Fraud Detection** | `fraud_data.db` (`transactions`) | 20,000 | *"How does ProductCD relate to fraud rate?"* |
| **🛒 E-Commerce Behavior** | `ecommerce_data.db` (`orders`) | 4,000 | *"Which device type has the highest conversion rate and cart value?"* |
| **📈 Live Crypto Market** | `crypto_data.db` (`coins`) | Live API | *"Which coins had the highest price change percentage today?"* |
| **📤 Custom CSV / SQLite** | User Uploaded | Dynamic | Instant schema inspection and verifiable analysis on any uploaded file. |

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
# Clone or enter workspace
cd agent-analytix

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Streamlit Web Application

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 💻 CLI & Programmatic Usage

Run verifiable analysis directly from your terminal:

```bash
# Analyze Retail dataset
python cli.py --db retail_data.db --table orders --question "What are the top 3 categories by sales and profit?"

# Analyze HR Attrition dataset
python cli.py --db hr_data.db --table employees --question "What is the attrition rate by department?"

# Export full cryptographic JSON certificate
python cli.py --db loan_data.db --table loans --question "What is default rate by grade?" --json
```

---

## 🧪 Automated Benchmarking & Stress Testing

Run the automated empirical benchmark suite:

```bash
python benchmark.py
```

### Adversarial Stress Testing:
The benchmark includes an **Adversarial Hallucination Injection Test** that injects fabricated claims (e.g. *"Our fraud rate exploded to 88.5% with 95,000 transactions"*). The deterministic verification engine automatically flags the ungrounded tokens and catches the hallucination with $100\%$ precision!

---

## 🔬 Comparison with Existing Frameworks

| Capability | Single-Agent LLM (ChatGPT / Claude) | PandasAI / Auto-Analyst | **AGENT-ANALYTIX (This Work)** |
|---|---|---|---|
| **Hallucination Detection** | ❌ None | ❌ None | ✅ **Algorithmic Fact-Checking Engine** |
| **Adversarial Audit** | ❌ None (Self-confirmation) | ❌ None | ✅ **Dedicated Auditor Agent** |
| **Execution Sandboxing** | ❌ Black-box execution | ⚠️ Basic Python exec | ✅ **Read-Only AST & Injection Safe Sandbox** |
| **Cryptographic Provenance**| ❌ None | ❌ None | ✅ **SHA-256 Digital Proof Certificate** |
| **Factual Groundedness Score**| ❌ Unquantified | ❌ Unquantified | ✅ **Mathematical Score ($0-100\%$)** |
| **Interactive Visuals** | ⚠️ Static images | ⚠️ Static images | ✅ **Dynamic Plotly Dashboards** |

---

## 📁 Repository Structure

```
agent-analytix/
├── core/
│   ├── __init__.py
│   ├── llm_client.py          # Multi-model client (OpenAI, Ollama, Resilient Engine)
│   ├── sandbox.py             # Read-only SQL Sandbox with AST guards & query plan
│   ├── verification_engine.py # Deterministic fact-checking & hallucination detector
│   ├── proof_receipt.py       # SHA-256 Cryptographic Verification Generator
│   ├── agents.py              # Specialized agents (Planner, Coder, Auditor, Synthesizer)
│   └── pipeline.py            # End-to-end multi-agent verification pipeline
├── data/
│   └── generate_datasets.py   # Synthetic enterprise benchmark dataset generator
├── tests/
│   └── test_verification.py   # Unit test suite for sandbox, fact-checker & proofs
├── app.py                     # Streamlit 5-tab Interactive Web Application
├── cli.py                     # Command-line interface with audit logs
├── benchmark.py               # Empirical benchmarking & adversarial stress test
├── fetch_crypto_data.py       # Live Binance cryptocurrency feed integration
├── requirements.txt           # Dependency specifications
└── README.md                  # Comprehensive academic & engineering documentation
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
