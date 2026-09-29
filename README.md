# Smart Guided Troubleshooting Engine (Samsung PRISM - Theme 2)

[![Tests](https://img.shields.io/badge/pytest-107%20passed-brightgreen.svg)](backend/)
[![Backend](https://img.shields.io/badge/FastAPI-0.100+-blue.svg)](backend/)
[![Frontend](https://img.shields.io/badge/React%2018-Vite-61dafb.svg)](frontend/)
[![Decision Engine](https://img.shields.io/badge/Laya%20AI-System--1%20Router-orange.svg)](backend/decision_engine.py)
[![Safety Protocol](https://img.shields.io/badge/Safety-Curated%20KB%20Retrieval-success.svg)](backend/knowledge_base.py)

> A high-throughput, question-first diagnostic troubleshooting engine for mobile devices. Engineered with a **sub-millisecond Fast Local Gate**, **Laya AI System-1 discrete decision routing**, and a **deterministic Sufficiency Gate**, ensuring instant solutions for clear queries and dynamic, guided clarification when information is ambiguous.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [AI Routing Order & Decision Flow](#ai-routing-order--decision-flow)
- [Laya AI Model Integration & Verification](#laya-ai-model-integration--verification)
- [Empirical Benchmarks & Performance](#empirical-benchmarks--performance)
- [Project Directory Structure](#project-directory-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Docker Setup](#docker-setup)
  - [Configuration (.env)](#configuration-env)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [AI Disclosure & Safety Guarantees](#ai-disclosure--safety-guarantees)
- [Submission Artifacts](#submission-artifacts)
- [License](#license)

---

## Overview

Traditional mobile troubleshooting assistants often rely on open-ended Large Language Models (LLMs) to converse, diagnose, and hallucinate troubleshooting steps on every user interaction. This architecture introduces critical flaws:
1. **Unnecessary Latency:** 2 to 5 second wait times even for routine queries with obvious solutions.
2. **Hallucination Risk:** Generative models can invent non-existent settings, invalid recovery menus, or dangerous battery handling steps.
3. **Premature Diagnoses:** Chatbots attempt to guess solutions without verifying whether essential diagnostic variables (e.g., error codes, device state, charging conditions) are known.

The **Smart Guided Troubleshooting Engine** resolves these issues through a tiered, question-first diagnostic pipeline:
- **Zero-Neural Fast Path (< 8ms end-to-end, < 1ms gate):** Resolves unambiguous queries directly from verified knowledge without invoking any neural models (0 LLMs, 0 Laya calls).
- **Laya Primary Decision Engine (< 12ms):** Uses discrete System-1 typed decision primitives (`choice`, `score`, `action`) to arbitrate ambiguous domains, symptoms, and actions without open-ended text generation.
- **Sufficiency Gate & Invariant Guard:** Automatically identifies missing diagnostic slots and prompts the user with targeted clarification questions before database retrieval is allowed.
- **Curated Knowledge Base Retrieval:** Troubleshooting steps are retrieved strictly from human-verified canonical procedures—unsupported queries return a graceful no-match response.

---

## System Architecture

The following diagram illustrates the verified execution order implemented in `backend/main.py`:

```
                              User Query / Input
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │   Fast Local Gate (< 1ms)         │
                    │  (Deterministic Phrase Preproc)   │
                    └─────────────────┬─────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
      [ CLEAR VERDICT ]      [ PARTIAL VERDICT ]      [ VAGUE VERDICT ]
              │                       │                       │
              ▼                       ▼                       ▼
     Deterministic Slot       Domain Entry Tree       Laya Decision Engine
     Sufficiency Check         Follow-up Card          (System-1 Router)
              │                       │                       │
     ┌────────┴────────┐              │              ┌────────┴────────┐
     ▼                 ▼              │              ▼                 ▼
[Sufficient]    [Missing Slots]       │      [Resolved Domain]    [Unresolved]
     │                 │              │              │                 │
     │                 ▼              │              ▼                 ▼
     │            Follow-up           │     Sufficiency Check    Gemini LLM
     │          Slot Question         │              │           (Exceptional
     │                                │      ┌───────┴───────┐     Fallback)
     │                                │      ▼               ▼         │
     │                                │  [Sufficient]  [Missing Slots] │
     │                                │      │               │         │
     │                                │      │               ▼         │
     │                                │      │           Follow-up     │
     │                                │      │         Slot Question   │
     │                                │      │                         │
     └────────────────────────────────┼──────┴─────────────────────────┘
                                      ▼
                     ┌───────────────────────────────────┐
                     │   Verified Knowledge Base (KB)    │
                     │  (Curated Procedures / Supabase)  │
                     └────────────────┬──────────────────┘
                                      ▼
                           Verified Solution Output
```

---

## AI Routing Order & Decision Flow

The engine enforces a strict routing hierarchy to maximize speed and eliminate hallucination:

1. **Tier 1 — Fast Local Gate (Zero-Neural Path):**
   - Implemented in [`backend/fast_gate.py`](backend/fast_gate.py).
   - If a query matches pre-indexed canonical aliases and exhibits sufficient specificity, verdict is `CLEAR`.
   - Evaluates slot sufficiency deterministically.
   - **Neural Footprint:** Exactly **0.0 LLM calls** and **0.0 Laya calls**. Measured average latency: **7.4 ms** (end-to-end API).

2. **Tier 2 — Guided Diagnostic Trees (Partial Path):**
   - When the domain is clear but the issue is unstated (e.g., *"I have a battery problem"*), the engine returns verdict `PARTIAL`.
   - Directly presents a follow-up diagnostic tree card for that domain without running unnecessary inference.

3. **Tier 3 — Laya Primary Decision Engine (Ambiguous/Vague Path):**
   - Implemented in [`backend/decision_engine.py`](backend/decision_engine.py).
   - Ambiguous inputs are evaluated **first** by Laya AI using discrete System-1 typed primitives (`choice`, `score`).
   - If Laya resolves the domain and issue, the request is checked by the [`SufficiencyGate`](backend/sufficiency_gate.py).
   - If required slots are missing, a targeted clarification question is asked.
   - If slots are verified, verified procedures are retrieved from the knowledge base.

4. **Tier 4 — Gemini LLM Exceptional Fallback:**
   - Implemented in [`backend/classifier.py`](backend/classifier.py).
   - Invoked **strictly as an exceptional fallback** when both the Fast Gate and Laya cannot categorize the query.
   - Categorizes raw text into candidate categories. It does **not** generate troubleshooting advice.
   - If all classification attempts fail, the system outputs an official support link.

---

## Laya AI Model Integration & Verification

### Codebase & Dependency Audit Findings
A comprehensive static and runtime audit of [`backend/decision_engine.py`](backend/decision_engine.py) and the `laya` package (`v0.3.20`) was performed:

1. **Integration Interface:**
   - Integrated via the official `laya` Python package (`v0.3.20`).
   - Managed as a thread-safe singleton (`_get_router()`) with thread-pool timeout protection (`LAYA_TIMEOUT = 2.0s`) and automatic fallback to rule-based decision trees.

2. **Underlying Model Checkpoint:**
   - The Laya Router loads the specialized checkpoint **`convaiinnovations/laya`** (specifically task subfolder `typed-decisions`).
   - Developed by ConvAI Innovations as a fast, discrete decision transformer designed for System-1 classification.

3. **Typed Primitives Employed:**
   - **`choice`**: Selects canonical troubleshooting domain (`battery`, `display`, `camera`, `performance`) and matches specific issues within domain criteria.
   - **`score`**: Assesses evidence sufficiency against criteria thresholds.
   - **`action`**: Arbitrates next operational step (`ASK_USER`, `LOOKUP_KNOWLEDGE`, `RESOLVE`, `NO_MATCH`).

4. **Model Verification Regarding "Jev":**
   - **Audit Finding:** The codebase, imports, and dependencies do **not** use, load, or reference any model named "Jev".
   - **Technical Fact:** Laya AI is powered exclusively by `convaiinnovations/laya`. Any mention of "Jev" is factually incorrect with respect to the verified implementation. Laya is strictly a discrete decision router and does not generate conversational prose.

---

## Empirical Benchmarks & Performance

Performance was benchmarked across 200 requests (20 iterations per scenario across 10 representative troubleshooting queries) using [`backend/benchmark_refactor.py`](backend/benchmark_refactor.py).

### Test Environment
- **Operating System:** Windows 11 x86_64
- **Runtime:** Python 3.10.10, Pytest 8.3.4, FastAPI TestClient
- **Measurement Tool:** High-precision hardware timer (`time.perf_counter()`)

### Measured Benchmark Data

| Scenario | Category | Status | Avg Latency | P50 Latency | P95 Latency | LLM Calls | Laya Calls | DB Queries |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Battery Drain (Clear)** | Fast Path | `follow_up` (slot check) | **6.2 ms** | 0.0 ms | 16.0 ms | **0.0** | **0.0** | 0.0 |
| **Screen Flicker (Clear)** | Fast Path | `success` | **7.8 ms** | 15.0 ms | 16.0 ms | **0.0** | **0.0** | 1.0 |
| **Slow Phone (Clear)** | Fast Path | `follow_up` (slot check) | **7.8 ms** | 15.0 ms | 16.0 ms | **0.0** | **0.0** | 0.0 |
| **Camera Blur (Clear)** | Fast Path | `follow_up` (slot check) | **7.8 ms** | 15.0 ms | 16.0 ms | **0.0** | **0.0** | 0.0 |
| **Phone Overheating** | Ambiguous | `follow_up` (tree) | **3.2 ms** | 0.0 ms | 16.0 ms | **0.0** | **0.0** | 0.0 |
| **Battery Problem** | Ambiguous | `follow_up` (tree) | **14.1 ms** | 16.0 ms | 16.0 ms | **0.0** | **0.0** | 0.0 |
| **Multi-Issue (Flicker + Drain)** | Multi-Path | `success` | **10.9 ms** | 15.0 ms | 16.0 ms | **0.0** | **0.0** | 1.0 |
| **Acting Weird (Vague)** | Vague | `follow_up` (tree) | **9.4 ms** | 15.0 ms | 16.0 ms | **0.0** | **0.0** | 0.0 |
| **Anomalous Smell (No-Match)** | Out-of-Scope | `no_match` | **676.6 ms** | 516.0 ms | 2016.0 ms | 1.0 | 1.0 | 0.0 |
| **Detailed (After Update)** | Detailed | `follow_up` (slot check) | **12.4 ms** | 15.0 ms | 16.0 ms | **0.0** | **0.0** | 0.0 |

### Key Empirical Takeaways:
- **Fast Gate Latency:** Deterministic preprocessor runs in **0.61 ms**.
- **Clear Path Latency:** Averages **7.4 ms** with **0.0 LLM calls** and **0.0 Laya calls**.
- **Ambiguous Path Latency:** Averages **8.7 ms** with **0.0 LLM calls**.
- **Heavy Fallback Exclusion:** Gemini LLM is excluded from over 85% of standard interactions, invoked solely for unstructured, out-of-scope complaints.

---

## Project Directory Structure

```
samsung-prism-troubleshooting-engine/
├── .env.example                                      # Environment template
├── .gitignore                                        # Secret & artifact exclusion rules
├── Dockerfile                                        # Container build specification
├── docker-compose.yml                                # Multi-service orchestration
├── README.md                                         # Project documentation
├── requirements.txt                                  # Root Python dependencies
├── backend/
│   ├── benchmark.py                                  # Latency benchmark suite
│   ├── benchmark_refactor.py                         # Scenario regression benchmarks
│   ├── classifier.py                                 # Exceptional Gemini LLM fallback
│   ├── config.py                                     # Configuration & timeouts
│   ├── decision_engine.py                            # Laya AI System-1 Router & typed decisions
│   ├── diagnostic_flow.py                            # Interactive diagnostic trees
│   ├── diagnostic_state.py                           # Multi-turn diagnostic state machine
│   ├── fast_gate.py                                  # Deterministic local gate preprocessor
│   ├── knowledge_base.py                             # Knowledge base retrieval
│   ├── logger.py                                     # Request tracing & logging
│   ├── main.py                                       # FastAPI service & request routing
│   ├── perf.py                                       # Performance timers & metrics
│   ├── requirements.txt                              # Backend dependencies
│   ├── schemas.py                                    # Pydantic data contracts
│   ├── seed_data.json                                # Canonical troubleshooting procedures
│   ├── serp_fallback.py                              # External web search fallback
│   ├── session.py                                    # Diagnostic session manager
│   ├── sufficiency_gate.py                           # Slot evaluation & diagnostic guards
│   ├── test_engine.py                                # Pipeline integration tests
│   ├── test_fast_gate.py                             # Sub-millisecond gate unit tests
│   ├── test_perf_optimizations.py                    # Singleton, caching & timeout tests
│   └── test_question_first_architecture.py           # Dynamic clarification tests
├── frontend/
│   ├── src/                                          # React 18 application source
│   ├── index.html                                    # Application entrypoint
│   ├── package.json                                  # NPM dependencies
│   └── vite.config.js                                # Vite configuration
├── docs/
│   ├── AI_DISCLOSURE.md                              # AI transparency document
│   └── architecture.png                              # System architecture diagram
├── demo/
│   └── README.md                                     # Interactive demo walkthrough
└── presentation/
    └── PRISM_Theme2_Troubleshooting_Engine_Submission.pdf # Submission presentation PDF
```

---

## Getting Started

### Prerequisites
- **Python:** 3.10 or higher
- **Node.js:** 18.x or higher
- **npm:** 9.x or higher

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # On Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # On Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (see Configuration section)
   ```

5. **Start the FastAPI server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   API interactive documentation is available at `http://localhost:8000/docs`.

---

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   The UI will launch at `http://localhost:5173`.

4. **Production Build:**
   ```bash
   npm run build
   ```

---

### Docker Setup

To launch the entire stack using Docker:

```bash
docker-compose up --build
```
The unified container will build the React frontend and serve both the FastAPI API and frontend assets at `http://localhost:8000`.

---

### Configuration (.env)

A `.env.example` file is provided at both the root and `backend/`:

```ini
# Optional: Primary API Key for exceptional LLM fallback
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Supabase Knowledge Brain (falls back to local seed_data.json)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Optional: SERP API Fallback
SERPAPI_API_KEY=optional_serpapi_key_here

# Performance & Timeout Tuning
FAST_PATH_CONFIDENCE=0.85
LLM_TIMEOUT=10.0
SUPABASE_TIMEOUT=5.0
```

> **Security Note:** `.env` files are strictly excluded via `.gitignore`. Never commit live production credentials.

---

## Testing & Quality Assurance

The test suite includes **107 automated tests** covering latency, sufficiency, resilience, and safety invariants.

### Running Backend Tests
From the `backend/` directory:

```bash
pytest -v
```

### Test Suite Summary

| Test Suite | Tests | Purpose / Coverage |
| :--- | :---: | :--- |
| [`test_fast_gate.py`](backend/test_fast_gate.py) | **29** | Verifies `< 1ms` resolution of clear queries, keyword matching, specificity scoring, and zero-LLM/zero-Laya bypass. |
| [`test_engine.py`](backend/test_engine.py) | **25** | End-to-end API response contract, domain routing, procedure retrieval, and status codes. |
| [`test_perf_optimizations.py`](backend/test_perf_optimizations.py) | **34** | Singleton router reuse, timeout handling, fallback to rule engines, metric tracking, and concurrency safety. |
| [`test_question_first_architecture.py`](backend/test_question_first_architecture.py) | **19** | Dynamic slot extraction, follow-up question synthesis, sufficiency guards, and session state continuity. |
| **Total** | **107** | **100% Pass Rate** |

---

## AI Disclosure & Safety Guarantees

In accordance with responsible AI standards and hackathon submission criteria, a detailed disclosure is available in [`docs/AI_DISCLOSURE.md`](docs/AI_DISCLOSURE.md):

1. **System-1 Decision Making vs. Generative Text:**
   - AI is used strictly for **discrete classification, categorical routing, and relevance scoring** (`Laya AI` with checkpoint `convaiinnovations/laya`, and optional `Gemini`).
   - Neither model is permitted to draft or invent troubleshooting procedures.
2. **Curated Knowledge Base Retrieval:**
   - Troubleshooting steps are retrieved strictly from a curated, verified knowledge base. Unsupported or out-of-scope issues return a safe no-match response directing users to official support channels.
3. **Deterministic Invariant Enforcement:**
   - Before any solution is shown to a user, the request must pass the [`SufficiencyGate`](backend/sufficiency_gate.py). If vital parameters (e.g. error codes, physical damage signs) are absent, the engine pauses and asks clarifying questions.
4. **Fail-Safe Operation:**
   - If AI services encounter network latency or timeouts, the system automatically degrades to deterministic decision trees without crashing or giving unverified advice.

For full details, see [**docs/AI_DISCLOSURE.md**](docs/AI_DISCLOSURE.md).

---

## Submission Artifacts

- **GitHub Repository:** [https://github.com/Srishant14/samsung-prism-troubleshooting-engine](https://github.com/Srishant14/samsung-prism-troubleshooting-engine)
- **Presentation Deck:** [presentation/PRISM_Theme2_Troubleshooting_Engine_Submission.pdf](presentation/PRISM_Theme2_Troubleshooting_Engine_Submission.pdf)
- **Interactive Demo Walkthrough:** [demo/README.md](demo/README.md)
- **Git Submission Tag:** `PRISM_GENAI_HACKATHON_2026`

---

## License

This project is prepared for the **Samsung PRISM GenAI Hackathon 2026 (Theme 2: Smart Guided Troubleshooting Engine)**. All rights reserved.
