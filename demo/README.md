# Prototype Demo & Walkthrough

**Project:** Smart Guided Troubleshooting Engine (Samsung PRISM – Theme 2)  
**Submission Event:** Samsung PRISM GenAI Hackathon 2026  

---

## Demo Video Links

- **Primary Demo Video:** [Click to Watch Demo on YouTube / Google Drive](https://youtu.be/placeholder-demo-link) *(replace with your public viewing link)*
- **Alternative Video Mirror:** *(Optional Google Drive link if YouTube is restricted)*

> **Judge Notice:** Please ensure public read access is enabled on the shared drive link if uploading to Google Drive.

---

## Live Interactive Walkthrough Guide

To evaluate the prototype locally, follow these steps to experience all 4 tiers of the diagnostic engine:

### 1. Launch the Stack
- **Backend:**
  ```bash
  cd backend
  uvicorn main:app --reload --port 8000
  ```
- **Frontend:**
  ```bash
  cd frontend
  npm run dev
  ```
- Open `http://localhost:5173` in your browser.

---

### 2. Test Scenarios to Try

#### Scenario A: Fast Local Gate Instant Resolution (< 1ms)
- **Input Query:** `"My Galaxy S24 battery is draining very fast"`
- **Expected Behavior:**
  - Status: `CLEAR` (Fast Path)
  - Latency: `< 1ms` (zero LLM calls, zero Laya calls)
  - Output: Immediate verified battery calibration and background app optimization steps retrieved directly from the canonical Knowledge Base.

#### Scenario B: Laya Decision Engine Ambiguous Arbitration (< 12ms)
- **Input Query:** `"My phone is overheating and lagging"`
- **Expected Behavior:**
  - Status: `PARTIAL` or Multi-issue detection
  - Decision: Laya Router arbitrates between performance throttling and battery thermal limits using typed primitives (`choice`, `score`).
  - Output: Guided follow-up card asking the user whether the overheating occurs during heavy gaming/fast charging or normal idle usage.

#### Scenario C: Dynamic Question-First Clarification
- **Input Query:** `"My screen keeps flickering"`
- **Expected Behavior:**
  - Status: `PARTIAL`
  - Invariant Check: The Sufficiency Gate identifies missing diagnostic slots (adaptive refresh rate setting vs. physical hardware drop).
  - Output: Follow-up question prompting the user with options to narrow down the issue before retrieving repair procedures.

#### Scenario D: Late-Stage Fallback for Out-of-Scope Queries
- **Input Query:** `"My device has a peculiar smell coming from the port"`
- **Expected Behavior:**
  - Status: `NO_MATCH` / Safety Warning
  - Output: The engine recognizes an anomalous hardware risk, advises immediate disconnection from power, and directs the user to an authorized Samsung Service Center.
