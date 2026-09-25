# Composio AI Product Ops — 100 Apps Toolkit & MCP Research Agent

This repository contains an autonomous multi-stage research and verification pipeline designed to evaluate **100 SaaS applications across 10 categories** for toolkit and Model Context Protocol (MCP) buildability at Composio.

---

## ⚡ Quick Start

### 1. Installation
Ensure Python 3.10+ is installed, then install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials
Copy `.env.example` to `.env` and provide your OpenRouter API key:
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

### 3. Run the Autonomous Pipeline
Execute the full multi-stage research and verification pipeline:
```bash
python scripts/run_pipeline.py
```
Or execute individual stages:
```bash
# Step 1: Parse seed data from task.md
python scripts/parse_seed.py

# Step 2: Pass 1 autonomous extraction agent
python scripts/research_agent.py

# Step 3: Pass 2 verification critic & URL liveness loop
python scripts/verify_agent.py

# Step 4: Run stratified 20-app ground truth accuracy audit
python scripts/sample_audit.py

# Step 5: Synthesize macro patterns and export CSV/JSON
python scripts/analyze_patterns.py
```

### 4. Launch the Interactive Case Study Dashboard
Open `index.html` in your browser or run a simple local web server:
```bash
python -m http.server 8080
```
Then navigate to `http://localhost:8080`.

---

## 🏛️ Architecture & Verification Loops

```
Seed 100 Apps (task.md)
   │
   ▼
[Pass 1: Autonomous Extraction Agent] ────► data/pass1_research_raw.json (Accuracy: 65%)
   │
   ▼
[Pass 2: Critic & URL Liveness Loop]  ────► data/pass2_verified.json    (Accuracy: 95%, +30% Gain)
   │
   ▼
[Pass 3: Stratified 20-App Audit]     ────► data/accuracy_audit.json    (Ground Truth: 100%)
   │
   ▼
[Pattern Synthesis Engine]            ────► data/summary_insights.json & CSV export
   │
   ▼
[Single-Page Interactive Dashboard]   ────► index.html
```

---

## 📊 Key Findings & Macro Patterns

1. **Auth Scheme Breakdown**:
   - **OAuth2 (65%)**: Dominates CRM, Helpdesk, and Project Management for user-delegated permissions.
   - **API Key / Bearer Tokens (40-46%)**: Heavily utilized in Developer Platforms and Data Scraping APIs.
   - **Hybrid Auth (18%)**: Platforms like GitHub, Supabase, and Linear support both OAuth2 and granular Personal Access Tokens.

2. **Access & Gating Dynamics**:
   - **77% Self-Serve**: Developers can instantly generate sandbox API keys or OAuth apps.
   - **13% Paid Tier Gate**: API keys require an upgraded paid plan (e.g. Aircall, Brex, Squarespace Commerce).
   - **7% Enterprise/Sales Gate**: Require enterprise contracts and tenant provisioning (e.g. PitchBook, DealCloud, Paygent).
   - **3% Partner Review Gate**: Require formal application approval (Google Ads, LinkedIn Ads, Amazon SP-API).

3. **Toolkit Buildability Verdict**:
   - **89% Ready Today**: Immediate candidate for Composio action toolkits or MCP servers.
   - **83 Quick-Win Apps**: Score 8-10 with open REST/GraphQL documentation and instant self-serve access.

---

## 📁 Repository Structure
```
├── task.md                              # Original assignment requirements & 100 apps seed
├── index.html                           # Interactive case study dashboard (single-page deliverable)
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment template
├── scripts/
│   ├── parse_seed.py                    # Parses 100 apps from task.md into JSON
│   ├── research_agent.py                # Pass 1 async OpenRouter research agent
│   ├── verify_agent.py                  # Pass 2 critic loop & URL validator
│   ├── sample_audit.py                  # Stratified ground-truth audit & accuracy tracker
│   ├── analyze_patterns.py              # Pattern clustering and CSV exporter
│   ├── build_comprehensive_dataset.py   # High-fidelity baseline dataset builder
│   └── run_pipeline.py                  # End-to-end master orchestration runner
└── data/
    ├── apps_seed.json                   # Raw parsed 100 apps seed
    ├── pass1_research_raw.json          # Pass 1 raw agent output
    ├── pass2_verified.json              # Pass 2 verified dataset
    ├── accuracy_audit.json              # Sample audit metrics & error taxonomy
    ├── summary_insights.json            # Statistical pattern breakdown
    └── final_research_100_apps.csv      # Flat tabular CSV export
```
