<p align="center">
  <img src="dashboard/public/logo.png" width="200" alt="SEMI Logo"/>
</p>
<p align="center">
    <h1 align="center">SEMI — Self-Evolving Manufacturer Intelligence</h1>
</p>
<p align="center">
    <em>An AI-Powered Autonomous Product Data Extraction Engine for Industrial Commerce</em>
</p>
<p align="center">
    <img src="https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-009688.svg?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
    <img src="https://img.shields.io/badge/React-61DAFB.svg?style=flat&logo=react&logoColor=black" alt="React">
    <img src="https://img.shields.io/badge/Vite-646CFF.svg?style=flat&logo=vite&logoColor=white" alt="Vite">
    <img src="https://img.shields.io/badge/SQLite-003B57.svg?style=flat&logo=sqlite&logoColor=white" alt="SQLite">
    <img src="https://img.shields.io/badge/Google_AI-4285F4.svg?style=flat&logo=google&logoColor=white" alt="Google AI">
</p>
<br>

## 🔗 Table of Contents

- [📍 Overview](#-overview)
- [👾 Features](#-features)
- [📂 Project Structure](#-project-structure)
- [🧩 Modules](#-modules)
- [🚀 Getting Started](#-getting-started)
  - [☑️ Prerequisites](#-prerequisites)
  - [⚙️ Installation](#-installation)
  - [🤖 Usage](#-usage)
- [🧪 Demo & Accuracy](#-demo--accuracy)
- [🗺 Roadmap](#-roadmap)
- [🏆 Team](#-team)

---

## 📍 Overview

**SEMI** addresses the critical "industrial data gap" where 70%+ of manufacturer catalogs lack vital technical attributes. Built for **UniHack 2026**, SEMI takes raw CSVs containing just a Manufacturer and Part Number and autonomously discovers, extracts, and audits the data using Google's Gemma 4-31B. It exports a perfect **252-column Unilog Delivery Format CSV** with zero human intervention and 100% source provenance.

---

## 👾 Features

|     | Feature               | Description                                                                                             |
| :-- | :-------------------- | :------------------------------------------------------------------------------------------------------ |
| ⚙️  | **Autonomous Search** | Bypasses e-commerce traps to find authoritative PDFs and spec sheets via Agent-Reach and DuckDuckGo.    |
| 🧠  | **LLM Extraction**    | Extracts 40+ dynamic attributes in a single pass using Google AI Studio (Gemini/Gemma).                 |
| 🛡️  | **Adversarial Audit** | Rejects hallucinations using physics-based mathematics and cross-source contradiction detection.        |
| 📊  | **Unilog Compliance** | Automatically maps raw extracted attributes to the strict 252-column Unilog Delivery Format standard.   |
| ⚡  | **Async Backend**     | High-concurrency architecture built on FastAPI to process massive catalogs simultaneously.              |

---

## 📂 Project Structure

```sh
└── hackproject new/
    ├── backend/
    │   ├── audit/
    │   ├── discover/
    │   ├── extract/
    │   ├── ingest/
    │   ├── ledger/
    │   ├── llm/
    │   ├── schema_inference/
    │   ├── schemas/
    │   └── server.py
    ├── dashboard/
    │   ├── public/
    │   ├── src/
    │   ├── package.json
    │   └── vite.config.ts
    ├── deployment/
    ├── docs/
    └── README.md
```

---

## 🧩 Modules

<details closed><summary>Backend Core</summary>

| File | Summary |
| --- | --- |
| `server.py` | The main FastAPI entry point orchestrating ingestion, extraction, and REST/WebSocket communication. |
| `sqlite_store.py` | Manages the persistent state graphs, ledgers, and conflict records. |
| `graph.py` | The async pipeline orchestrator routing data through the discovery and extraction agents. |

</details>

<details closed><summary>Ingest & Export</summary>

| File | Summary |
| --- | --- |
| `excel_input.py` | Parses raw `.csv` and `.xlsx` inputs using advanced alias matching. |
| `unilog_export.py` | Transforms internal state graphs into the 252-column Unilog Delivery Format. |
| `source_validator.py` | Rejects non-authoritative e-commerce URLs (Amazon, eBay, Walmart). |

</details>

<details closed><summary>Discovery & LLM</summary>

| File | Summary |
| --- | --- |
| `search.py` | The hybrid web search chain utilizing DuckDuckGo, Firecrawl, Exa, and Agent-Reach. |
| `gemma.py` | Connects to Google AI Studio to execute structured JSON extraction tasks. |

</details>

---

## 🚀 Getting Started

### ☑️ Prerequisites

Ensure you have the following installed:
- **Python:** `3.11+`
- **Node.js:** `18+`
- **Google AI API Key:** [Get one here](https://aistudio.google.com/apikey)

### ⚙️ Installation

1. **Clone the repository and set up the Backend:**
```sh
git clone https://github.com/VarshneysvAI/semi-workbench.git
cd semi-workbench/backend
python -m venv .venv
# Activate: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux)
pip install -r requirements.txt
cp .env.example .env
# Edit .env and insert your GOOGLE_API_KEY
```

2. **Set up the Dashboard:**
```sh
cd ../dashboard
npm install
```

### 🤖 Usage

1. **Start the API Server:**
```sh
cd backend
uvicorn backend.server:app --port 8000
```
2. **Start the Frontend Dashboard:**
```sh
cd dashboard
npm run dev
```
3. Open `http://localhost:5173`, upload your CSV, and watch SEMI autonomously build your catalog.

---

## 🧪 Demo & Accuracy

*(Insert Demo Video Here)*

During live extraction of the `Eaton 9PX1500RT` industrial UPS, SEMI parsed a 50+ page PDF and accurately mapped the following properties to the Unilog format:
- **AC Mode Efficiency Rating:** `90.28%`
- **Output waveform:** `True sine wave`
- **Input frequency range:** `60 Hz: 50–70 Hz, 50 Hz: 40–60 Hz`
- **Battery Technology:** `ABM technology (3-stage charging)`
- **Heat Dissipation (BTU/Hr):** `512`

All variables passed the **Adversarial Physics constraints** with `100% confidence`.

---

## 🗺 Roadmap

- [X] **Multi-LLM Redundancy:** Fallback to NVIDIA NIM.
- [X] **Unilog Format Support:** Strict 252-column export.
- [ ] **Self-Hosted Mode:** Integration with vLLM for local air-gapped Gemma 4-31B deployment.
- [ ] **Vision Parsing:** Direct CAD/Blueprint dimension extraction using multimodal models.

---

## 🏆 Team

**Team VarshneysvAI**  
*Track: AI-Powered Product Intelligence for Industrial Commerce*  
UniHack 2026

[**Return to Top**](#-table-of-contents)