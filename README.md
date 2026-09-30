# Samsung PRISM Troubleshooting Engine V5.1

[![Tests](https://img.shields.io/badge/pytest-107%20passed-brightgreen.svg)](backend/)
[![Backend](https://img.shields.io/badge/FastAPI-0.100+-blue.svg)](backend/)
[![Frontend](https://img.shields.io/badge/React%2018-Vite-61dafb.svg)](frontend/)
[![Decision Engine](https://img.shields.io/badge/Laya%20AI-System--1%20Router-orange.svg)](backend/decision_engine.py)
[![Safety Protocol](https://img.shields.io/badge/Safety-Curated%20KB%20Retrieval-success.svg)](backend/knowledge_base.py)
[![UI](https://img.shields.io/badge/UI-Diagnostic%20Precision%20Dark-7c3aed.svg)](frontend/src/index.css)

> A high-throughput, question-first diagnostic troubleshooting engine for Samsung devices. Engineered with a **sub-millisecond Fast Local Gate**, **Laya AI System-1 discrete decision routing**, a **deterministic Sufficiency Gate**, and a premium **Diagnostic Precision Dark** interface — delivering instant verified solutions for clear queries and dynamic guided clarification when information is ambiguous.

---

## Table of Contents

- [Overview](#overview)
- [Screenshots](#screenshots)
- [System Architecture](#system-architecture)
- [AI Routing Order & Decision Flow](#ai-routing-order--decision-flow)
- [Frontend — Diagnostic Precision Dark UI](#frontend--diagnostic-precision-dark-ui)
- [Unresolved Issue Escalation System](#unresolved-issue-escalation-system)
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

The **Samsung PRISM Troubleshooting Engine V5.1** resolves these issues through a tiered, question-first diagnostic pipeline:
- **Zero-Neural Fast Path (<8ms end-to-end, <1ms gate):** Resolves unambiguous queries directly from verified knowledge without invoking any neural models (0 LLMs, 0 Laya calls).
- **Laya Primary Decision Engine (<12ms):** Uses discrete System-1 typed decision primitives (`choice`, `score`, `action`) to arbitrate ambiguous domains, symptoms, and actions without open-ended text generation.
- **Sufficiency Gate & Invariant Guard:** Automatically identifies missing diagnostic slots and prompts the user with targeted clarification questions before database retrieval is allowed.
- **Curated Knowledge Base Retrieval:** Troubleshooting steps are retrieved strictly from human-verified canonical procedures—unsupported queries return a graceful no-match response.
- **Diagnostic Precision Dark UI:** Premium dark-themed interface with PRISM branding, console-style diagnostic input, staged resolution sequences, and a full escalation system.

---

## Screenshots

### 1. Initial Input — Console Diagnostic Prompt
The home screen features a console-style `SYS.DIAG_PROMPT` input with quick preset chips, pipeline telemetry cards, and feature cards describing the 3-tier architecture.

### 2. Clarification Flow — Laya AI Diagnostic Gate
When the engine needs more information, it presents radio-button options with a status bar showing gate latency and protocol details. The original query is displayed for context.

### 3. Verified Results — Curated Resolution Sequence
Results display domain badges, a confidence anomaly box, numbered resolution stages, deep-link paths, and Samsung Source Attestation with verification stamps.

### 4. Escalation System — Unresolved Issue Panel
If the issue persists, a modal offers Contact Samsung Support (country-aware), Find a Nearby Service Centre (geolocation + manual entry), and Generate Troubleshooting Report (copy/download).

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
                                      │
                           ┌──────────┴──────────┐
                           ▼                     ▼
                    [Issue Resolved]     [Issue Persists]
                           │                     │
                           ▼                     ▼
                  Positive Telemetry     Escalation System
                     Confirmation       (Support / Service
                                         Centre / Report)
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

## Frontend — Diagnostic Precision Dark UI

The frontend implements the **PRISM Diagnostic Precision Dark** design system, a premium dark-themed UI built with React 18 and Vite.

### Design System

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#0f131d` | App canvas |
| Surface Lowest | `#0a0e18` | Deepest card backgrounds |
| Surface Container | `#1c1f2a` | Card panels |
| Primary | `#d2bbff` | Text accents, headings |
| Primary Container | `#7c3aed` | Buttons, active states |
| Tertiary | `#4cd7f6` | Status indicators, cyan accents |
| Secondary | `#aec6ff` | Complementary accents |
| Success | `#10B981` | Verified badges, positive states |
| Error | `#ffb4ab` | Error states, warnings |
| Font Sans | Inter | Body text, headings |
| Font Mono | JetBrains Mono | Code labels, badges, technical text |
| Icons | Material Symbols Outlined | All iconography |

### Component Architecture

```
App.jsx
├── Header.jsx .................. Fixed header (PRISM logo, stage tabs, system status)
├── HeroSection.jsx ............. "Troubleshoot Smarter. Fix Faster." hero
├── SearchBar.jsx ............... Console SYS.DIAG_PROMPT input + preset chips
├── PipelineSection.jsx ......... 94.2% first-pass match ring + pipeline metrics
├── FeatureCards.jsx ............ 3 feature cards (Local Engine, Laya AI, Verified Corpus)
├── FollowUpCard.jsx ............ Clarification flow with radio options + gate status
├── TroubleshootResult.jsx ...... Verified results (badges, steps, anomaly box)
│   └── EscalationPanel.jsx ..... Modal: Contact Support / Service Centre / Report
│       └── ServiceCentreFinder.jsx .. Geolocation + manual location search
├── NoMatchCard.jsx ............. No-match fallback card
└── Footer.jsx .................. Latency, corpus build, verification footer
```

### Key Features

- **Console-style diagnostic input** with `>` prompt, `Esc` to clear, `⌘+↵` to submit
- **Quick preset chips** with emojis for common Samsung device issues
- **Stage-aware navigation tabs** (Initial Input → Clarification → Analysis → Results → Architecture)
- **Animated loading state** with pipeline routing description
- **Radio-button clarification options** with "Suggested Match" tags
- **Numbered resolution stages** with domain badges and verified solution stamps
- **Glass-morphism cards** with ambient glow effects and backdrop blur

---

## Unresolved Issue Escalation System

When a user clicks **"Still experiencing the issue"** in the Resolution Verification panel, a comprehensive multi-channel escalation system activates, ensuring every user has a clear path to resolution:

### A. Contact Samsung Support & In-App Email Composer
- **Interactive In-App Email Composer:**
  - Displays an editable email draft with pre-filled fields:
    - **To (Official Support):** Defaults to official regional support email (`support.india@samsung.com` for India, `uk.customercare@samsung.com` for UK, `support@samsung.com` for US).
    - **Subject:** Pre-structured identifier: `[Samsung Support Request] <Issue Title> - Issue Persists`.
    - **Message Content:** Pre-formatted diagnostic summary including reported symptoms, One UI 6.1 specs, diagnosis confidence, all attempted troubleshooting stages, and persisting outcome.
- **Multi-Platform Dispatch Options:**
  - **Send via Gmail:** One-click launch into Gmail Web (`https://mail.google.com/mail/...`) with To, Subject, and Body fully pre-populated (no desktop email client required).
  - **Send via Outlook:** Launches Outlook Webmail (`https://outlook.live.com/owa/...`) pre-filled.
  - **Open System Mail:** Triggers default OS email client (`mailto:`) with URI-encoded parameters.
  - **Copy Full Draft:** Copies the entire structured draft to clipboard with instant visual feedback.
- **Regional Support Selector:**
  - Auto-detects region prioritizing **India (`🇮🇳`)** via Indian Standard Time (IST UTC+5:30) / timezone.
  - Interactive pill toggles for **India (`🇮🇳`)**, **United States (`🇺🇸`)**, **United Kingdom (`🇬🇧`)**, and **Global (`🌐`)**.
  - Direct links to official country support portals and live chat services.
- **Privacy & Safety Rules:**
  - **Zero automated sending:** Emails are never dispatched without explicit user review and action.
  - **No sensitive PII:** Strictly omits IMEI numbers, serial numbers, passwords, and tokens.

### B. Nearby Samsung Authorized Service Centre Locator
1. **Transparent Permission Request:** Explains why location is needed before requesting browser geolocation.
2. **GPS-Assisted Discovery:** On user consent, queries Google Maps for official Samsung Service Centres centered on the user's coordinates, alongside Samsung's official locator portal.
3. **Manual Search Fallback:** If GPS access is denied or unavailable, users can enter any city, locality, or 6-digit PIN code (e.g. `Hyderabad`, `560001`, `Koramangala Bangalore`).
4. **Anti-Hallucination Invariant:** The engine **never fabricates fictitious service centre names, addresses, or phone numbers**. It always directs users to verified Google Maps and Samsung official locator databases.
5. **Transient Privacy:** Geolocation coordinates are transient and held strictly in browser memory—never stored in databases or transmitted to backend servers.

### C. Structured Troubleshooting Report Generator
- Generates a human-readable, plain-text diagnostic dossier:
  - Technical summary: Issue description, domain category, title, confidence score.
  - Chronological runbook: All troubleshooting steps attempted by the user.
  - Session verification: Unique session reference ID, UTC timestamp, and engine version (PRISM v5.1).
  - Outcome attestation: Clearly marks outcome as `"Status: Issue persists after attempting recommended steps."`
- **Actions:** One-click **Copy to Clipboard** and **Download as .txt** file (`samsung-prism-report-<timestamp>.txt`).

---

## Interactive Stepper Runbook vs. Diagnostic Triage Gate

To provide an optimal UX, the interface strictly differentiates between **asking questions** (gathering evidence) and **executing steps** (taking physical hardware/software actions):

| Dimension | Question Asking UI (`FollowUpCard.jsx`) | Steps Execution Runbook (`TroubleshootResult.jsx`) |
| :--- | :--- | :--- |
| **Purpose** | Diagnostic Triage Inquiry Gate | Tactical Action Execution Runbook |
| **Interaction** | Radio selection (choose 1 condition to narrow scope) | Interactive checkboxes (mark stages completed as executed) |
| **Visual Track** | Inquiry hero card + selectable option cards | Connected vertical timeline stepper with glowing node rails |
| **Feedback** | "Suggested Match" chips, skip/back flow | Dynamic execution progress bar (`X of Y stages executed - Z%`) |
| **Procedural Guidance** | Query quote & symptom categorization | Breadcrumb navigation paths (`Settings > Battery > ...`) |
| **Hardware Sequences** | N/A (Categorical evaluation) | Android Recovery Hardware Terminal with numbered sequence |
| **Architecture Insights**| Local NPU & Laya AI evaluation status | Collapsible "Why this works (Kernel & OS Architecture)" drawers |
| **Toolbar Actions** | Back to query / Skip question | Copy All Steps to clipboard / Print technical runbook |


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
├── .env.example                        # Environment template
├── .gitignore                          # Secret & artifact exclusion rules
├── Dockerfile                          # Multi-stage container build (Node → Python)
├── docker-compose.yml                  # Service orchestration with health checks
├── README.md                           # Project documentation (this file)
├── requirements.txt                    # Root Python dependencies
│
├── backend/
│   ├── main.py                         # FastAPI service & request routing
│   ├── fast_gate.py                    # Deterministic local gate preprocessor (<1ms)
│   ├── decision_engine.py              # Laya AI System-1 Router & typed decisions
│   ├── sufficiency_gate.py             # Slot evaluation & diagnostic guards
│   ├── classifier.py                   # Exceptional Gemini LLM fallback
│   ├── diagnostic_flow.py              # Interactive diagnostic trees
│   ├── diagnostic_state.py             # Multi-turn diagnostic state machine
│   ├── knowledge_base.py              # Knowledge base retrieval
│   ├── schemas.py                      # Pydantic data contracts (API models)
│   ├── session.py                      # Diagnostic session manager
│   ├── config.py                       # Configuration & timeouts
│   ├── logger.py                       # Request tracing & logging
│   ├── perf.py                         # Performance timers & metrics
│   ├── serp_fallback.py                # External web search fallback
│   ├── seed_data.json                  # Canonical troubleshooting procedures
│   ├── requirements.txt                # Backend Python dependencies
│   ├── benchmark.py                    # Latency benchmark suite
│   ├── benchmark_refactor.py           # Scenario regression benchmarks
│   ├── test_engine.py                  # Pipeline integration tests (25)
│   ├── test_fast_gate.py               # Sub-millisecond gate unit tests (29)
│   ├── test_perf_optimizations.py      # Singleton, caching & timeout tests (34)
│   └── test_question_first_architecture.py  # Dynamic clarification tests (19)
│
├── frontend/
│   ├── index.html                      # HTML shell (Inter, JetBrains Mono, Material Symbols)
│   ├── package.json                    # NPM dependencies (React 18, Vite)
│   ├── vite.config.js                  # Vite config with /api proxy → localhost:8000
│   └── src/
│       ├── main.jsx                    # React entry point
│       ├── App.jsx                     # Root app — state, API calls, routing
│       ├── index.css                   # Complete Diagnostic Precision Dark CSS (2400+ lines)
│       └── components/
│           ├── Header.jsx              # Fixed header (logo, stage tabs, system status)
│           ├── Footer.jsx              # Latency, corpus build, verification footer
│           ├── HeroSection.jsx         # Hero headline with gradient text
│           ├── SearchBar.jsx           # Console SYS.DIAG_PROMPT with presets
│           ├── PipelineSection.jsx     # Pipeline ring chart + metrics
│           ├── FeatureCards.jsx        # 3 architecture feature cards
│           ├── FollowUpCard.jsx        # Clarification flow (radio options, gate status)
│           ├── TroubleshootResult.jsx  # Verified results (stages, badges, feedback)
│           ├── NoMatchCard.jsx         # No-match fallback card
│           ├── EscalationPanel.jsx     # Escalation modal (Support / Centre / Report)
│           └── ServiceCentreFinder.jsx # Geolocation + manual service centre search
│
├── docs/
│   ├── AI_DISCLOSURE.md                # AI transparency document
│   └── architecture.png               # System architecture diagram
├── demo/
│   └── README.md                       # Interactive demo walkthrough
└── presentation/
    └── PRISM_Theme2_Troubleshooting_Engine_Submission.pdf
```

---

## Getting Started

### Prerequisites
- **Python:** 3.10 or higher
- **Node.js:** 18.x or higher
- **npm:** 9.x or higher
- **Docker** (optional): 20.x or higher for containerized deployment

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
   The UI will launch at `http://localhost:3000` (Vite proxies `/api/*` to the backend at `localhost:8000`).

4. **Production Build:**
   ```bash
   npm run build
   ```
   Built assets are output to `frontend/dist/`.

---

### Docker Setup

To launch the entire stack (frontend + backend) in a single container:

```bash
# Build and start
docker-compose up --build

# Or build the image directly
docker build -t prism-engine .
docker run -p 8000:8000 --env-file .env prism-engine
```

The unified container:
1. Builds the React frontend via Node 20 Alpine
2. Serves the FastAPI backend on port 8000
3. Includes a health check (`/health` endpoint)
4. Architecture visualizations available at `/2d` and `/3d`

Access the application at `http://localhost:8000`.

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
5. **Escalation System Transparency:**
   - The Escalation System never fabricates service centre data, Samsung email addresses, or support ticket confirmations.
   - Location data is transient and not stored. No sensitive identifiers (IMEI, serial numbers) are included in reports by default.

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
