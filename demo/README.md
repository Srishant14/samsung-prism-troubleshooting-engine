# Prototype Demo & Walkthrough

**Project:** Smart Guided Troubleshooting Engine (Samsung PRISM – Theme 2)  
**Submission Event:** Samsung PRISM GenAI Hackathon 2026  

---

## Demo Video Links

- **Primary Demo Video:** [Watch Demo Video on Google Drive](https://drive.google.com/file/d/1yRhIrKIaWLcY29jd7rWb7kP4la5DJ4gP/view?usp=sharing&t=1.931)
- **Direct Video URL:** `https://drive.google.com/file/d/1yRhIrKIaWLcY29jd7rWb7kP4la5DJ4gP/view?usp=sharing&t=1.931`

> **Judge Notice:** The demo video is publicly accessible on Google Drive.

---

## Live Interactive Walkthrough Guide

To evaluate the prototype locally, follow these steps to experience all 4 tiers of the diagnostic engine and the escalation workflow:

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
- Open `http://localhost:3000` in your browser (or `http://localhost:8000` for full-stack unified mode).

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
  - Output: Triage inquiry gate prompting the user with options to narrow down the issue before retrieving repair procedures.

#### Scenario D: Late-Stage Fallback for Out-of-Scope Queries
- **Input Query:** `"My device has a peculiar smell coming from the port"`
- **Expected Behavior:**
  - Status: `NO_MATCH` / Safety Warning
  - Output: The engine recognizes an anomalous hardware risk, advises immediate disconnection from power, and directs the user to an authorized Samsung Service Center.

#### Scenario E: Interactive Stepper Runbook & Escalation Workflow
- **Perform Steps:**
  - Click on the interactive checkboxes for each stage in the **Resolution Stepper Runbook**.
  - Notice the **Execution Progress Bar** advance dynamically (`X of Y stages executed`).
  - Expand the **Why this works** drawer to inspect system architecture details.
- **Trigger Escalation:**
  - Click the **"Still experiencing the issue"** button.
  - The **Escalation Panel** appears with 3 verified paths:
    1. **Contact Samsung Support:**
       - Select Region (`🇮🇳 India`, `🇺🇸 US`, `🇬🇧 UK`, `🌐 Global`).
       - Click **"Compose & Send Email"** to launch the interactive In-App Email Composer.
       - Click **"Send via Gmail"** or **"Send via Outlook"** to pre-fill webmail with recipient, subject, and diagnostic steps.
       - Use **"Copy Full Draft"** to copy formatted text with one click.
    2. **Find a Nearby Service Centre:**
       - Review the permission explanation, then click **"Use My Location"** to query nearest centres.
       - Test the fallback by typing a city or PIN code (e.g. `Hyderabad`, `560001`) to search via Google Maps and Samsung's official locator.
    3. **Generate Troubleshooting Report:**
       - Review session metadata, copy to clipboard, or click **"Download as .txt"**.
