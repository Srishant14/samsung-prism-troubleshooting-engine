# AI Disclosure Document

**Project:** Smart Guided Troubleshooting Engine (Samsung PRISM – Theme 2)  
**Submission Event:** Samsung PRISM GenAI Hackathon 2026  
**Date:** September 2026  

---

## 1. Executive Summary

The **Smart Guided Troubleshooting Engine** combines deterministic fast routing, discrete System-1 AI decision making, and dynamic question-first clarification. This document transparently outlines all AI models, third-party AI services, and AI development assistants used in this project, in compliance with the hackathon submission guidelines.

---

## 2. Production AI Models & Services Used

### A. Laya AI Decision Engine
- **Library & Version:** `laya` (v0.3.20)
- **Model Checkpoint:** `convaiinnovations/laya` (specifically `typed-decisions` subfolder/task)
- **Developer / Provider:** ConvAI Innovations
- **Role in Application:**
  - Serves as the **System-1 Primary Decision Engine** (<12ms) for structured routing when queries are ambiguous or lack clear deterministic keywords.
  - Executes discrete typed primitives:
    - `choice`: Resolves canonical domain (`battery`, `display`, `camera`, `performance`) and matches specific issues within domain criteria.
    - `score`: Evaluates whether the collected evidence satisfies criteria thresholds.
    - `action`: Arbitrates next-step decisions (`ASK_USER`, `LOOKUP_KNOWLEDGE`, `RESOLVE`, `NO_MATCH`).
- **Critical Architectural Boundary:**
  - Laya is strictly used for **categorical classification and decision arbitration**.
  - Laya **never generates open-ended text or troubleshooting instructions**.
- **Model Verification Note Regarding "Jev":**
  - **Audit Finding:** A full audit of the codebase, imports, and dependencies confirms that **no model named "Jev" is used, loaded, or integrated**.
  - **Technical Reality:** Laya AI utilizes ConvAI Innovations' proprietary decision transformers (`convaiinnovations/laya`). Any previous mention of "Jev" was an unverified assumption or naming confusion; our implementation uses the authentic `convaiinnovations/laya` checkpoint.

---

### B. Google Gemini API (Exceptional Fallback Classifier)
- **Library & Model:** `google-genai` / `gemini-1.5-flash` (or `gemini-2.0-flash`)
- **Developer / Provider:** Google Cloud / Google AI
- **Role in Application:**
  - Functions strictly as a **late-stage, exceptional fallback classifier** in [`backend/classifier.py`](../backend/classifier.py).
  - Invoked **only** when both the Fast Local Gate and the Laya Decision Engine fail to categorize a highly vague query.
  - Returns structured JSON containing domain and issue classification candidates.
  - **Exclusion from the Critical Path:** Gemini is never invoked for clear queries, ensuring 0 LLM calls for over 80% of common troubleshooting interactions.
- **Safety Restriction:**
  - Gemini is strictly restricted to diagnostic classification. It is never permitted to synthesize or draft repair procedures.

---

### C. Knowledge Brain (Strict Zero-Hallucination Source of Truth)
- **Implementation:** In-memory indexed store with Supabase / JSON backup ([`backend/seed_data.json`](../backend/seed_data.json)).
- **Role:** Every single troubleshooting procedure, step-by-step resolution, and action link returned to the user originates from human-verified, canonical technical documentation. No generative model drafts procedural advice.

---

## 3. AI Coding Assistants Used During Development

- **Tool:** Google Antigravity IDE & Claude Code CLI
- **Usage:**
  - Architecture refinement and refactoring (implementing the Question-First diagnostic pipeline).
  - Test suite generation and regression testing (107 unit and integration tests across 4 test suites).
  - Codebase auditing, benchmark profiling, and submission documentation preparation.
- **Human Verification & Team Review:**
  - All code generated or suggested by AI assistants underwent manual review, static analysis, and automated test validation (`pytest` 107/107 passed, Vite production build verified).

---

## 4. Implementation Transparency Matrix

| Subsystem / Component | Implementation Type | Verification Method |
| :--- | :--- | :--- |
| **Fast Local Gate** | 100% Deterministic (Regex / KB Indexing) | 29 Unit Tests in `test_fast_gate.py` (<1ms execution) |
| **Domain & Issue Arbitration** | AI-Powered (`convaiinnovations/laya`) | 34 Tests in `test_perf_optimizations.py` (Singleton & fallback verified) |
| **Sufficiency Gate & Invariant Guard** | Deterministic Slot & State Machine | 19 Tests in `test_question_first_architecture.py` |
| **Late-Stage Query Classification** | AI-Powered (Google Gemini Fallback) | Isolated mock & fallback verification in `test_engine.py` |
| **Troubleshooting Procedures** | Verified Canonical Knowledge Base | Exact-match validation; Zero neural generation |

---

## 5. Ethical & Safety Considerations

1. **User Safety First:** Mobile troubleshooting can involve dangerous situations (e.g. swollen lithium batteries, charging port moisture). Generative hallucination in this domain presents physical risks. By delegating all procedures to verified knowledge files and utilizing AI strictly for categorical routing, the system guarantees 100% verified advice.
2. **Transparent Follow-Up:** Rather than guessing when information is vague, the engine prompts the user with targeted questions, respecting user agency and accuracy.
3. **Data Privacy:** Queries are pre-processed locally; no Personally Identifiable Information (PII) is transmitted to external models.

---

## 6. Escalation, Service Centre Locator & Draft Mail Transparency Guarantees

1. **Zero Automated Email Dispatch:** The escalation system never automatically sends an email on the user's behalf. It prepares an editable draft and provides explicit webmail (Gmail / Outlook) and mailto dispatch buttons so the user has 100% agency over what information is transmitted.
2. **No Sensitive PII by Default:** Draft emails and diagnostic reports strictly omit IMEI numbers, device serial numbers, passwords, and authentication tokens. Only reported symptoms, diagnostic session ID, and attempted technical steps are included.
3. **Verified Service Centre Data:** The engine never fabricates fictitious service centre names, addresses, or telephone numbers. If local GPS is permitted, it queries Google Maps and Samsung's official locator; if denied, it allows manual city/PIN entry without storing location coordinates.
4. **Transient Geolocation:** Browser coordinates requested for the service centre finder are strictly transient, held in browser memory for the immediate search action, and never transmitted to or logged on any server.

