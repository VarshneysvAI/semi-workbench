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

- [📍 The Industrial Data Gap (Overview)](#-the-industrial-data-gap-overview)
- [👾 How SEMI Solves It](#-how-semi-solves-it)
- [🧬 Core Pipeline Architecture](#-core-pipeline-architecture)
- [📊 The 252-Column Unilog Format](#-the-252-column-unilog-format)
- [🧪 Live Demo & 100% Accuracy Validation](#-live-demo--100-accuracy-validation)
- [🚀 Getting Started](#-getting-started)
- [🗺 Roadmap](#-roadmap)
- [🏆 Team](#-team)

---

## 📍 The Industrial Data Gap (Overview)

In the industrial B2B commerce sector, distributors face a massive operational bottleneck: **inconsistent and incomplete product catalogs**. 
Manufacturers provide primitive spreadsheets containing just a Manufacturer name and a Part Number, missing up to **70%+ of crucial technical attributes** (dimensions, pressures, voltages, compatibilities, safety compliances). 

Distributors are forced to hire teams of humans to manually scour the internet, download 100-page PDF spec sheets, read through dense technical jargon, and transcribe the data into a standard format. This manual data enrichment process is slow, highly prone to human error, and costs millions of dollars annually.

**SEMI was built for UniHack 2026 to automate this exact workflow with zero human intervention.**

---

## 👾 How SEMI Solves It

Given a raw input catalog containing just a `Manufacturer` and a `Part Number`, SEMI autonomously executes a 5-stage pipeline:

|     | Feature               | Description                                                                                             |
| :-- | :-------------------- | :------------------------------------------------------------------------------------------------------ |
| ⚙️  | **Autonomous Search** | Bypasses e-commerce traps to find authoritative PDFs and spec sheets directly from the manufacturer using a hybrid DuckDuckGo/Exa/Firecrawl search engine. |
| 🧠  | **LLM Extraction**    | Extracts 40+ dynamic attributes in a single pass using structured JSON prompts via Google AI Studio (Gemini-2.5 / Gemma-4-31B). |
| 🛡️  | **Adversarial Audit** | Rejects LLM hallucinations using physics-based mathematics and cross-source contradiction detection. SEMI refuses to guess. |
| 📊  | **Unilog Compliance** | Automatically maps raw extracted attributes to the strict, industry-standard 252-column Unilog Delivery Format. |
| ⚡  | **Async Dashboard**   | A live, highly concurrent React/Vite dashboard built on FastAPI to process massive catalogs simultaneously with real-time websocket updates. |

---

## 🧬 Core Pipeline Architecture

### Stage 1: Ingestion & Inference
SEMI accepts messy CSV or Excel (`.xlsx`) files. It uses an LLM-assisted schema inference engine alongside strict alias tables (`make`, `company`, `brand` -> `manufacturer`) to figure out what data is already present, ensuring the LLM doesn't waste tokens extracting data the user already provided.

### Stage 2: Discovery & Source Validation
SEMI generates precise, spec-first search queries (`site:eaton.com "9PX1500RT" spec sheet pdf`). It then runs these URLs through a rigid **Source Validator** which instantly blacklists consumer marketplaces like Amazon, eBay, and Target to prevent scraping third-party garbage data. Only authoritative sources (weighted: PDF > Manual > Product Page) are passed to the next stage.

### Stage 3: Dynamic Extraction
Instead of searching for one attribute at a time, SEMI downloads the raw PDFs using Jina Reader and passes the entire document context to **Gemma 4-31B**. The LLM is instructed to find *every single attribute possible* and return it as a structured JSON object, alongside the exact evidence snippet it used to find the value.

### Stage 4: Adversarial Audit Engine
LLMs hallucinate. SEMI prevents this through an **Adversarial Audit**:
1. **Physics Constraints:** E.g., If the LLM says a valve operates at 10,000 PSI, but it's made of basic PVC, the audit flags it.
2. **Cross-Source Contradiction:** If the Manual PDF says `120V` but the Product Webpage says `240V`, SEMI halts and opens a "Conflict".
3. **Refusal Gate:** If the LLM's confidence falls below `0.85`, SEMI refuses to emit the value to the final sheet.

### Stage 5: Export & Assembly
The data is then mapped into a production-ready export file.

---

## 📊 The 252-Column Unilog Format

SEMI produces output that is immediately ready for B2B e-commerce ingestion, strictly adhering to the **Unilog Delivery Format specification**:

| Column Group | Examples | Max Count |
|---|---|---|
| **Identification** | `PART_NUMBER`, `Mfg_Part_Num`, `SKU - MY_PART_NUMBER` | 12 |
| **Manufacturer/Brand** | `MANUFACTURER_NAME`, `BRAND_NAME`, `E1_Brand` | 7 |
| **Descriptions** | `SHORT_DESC`, `LONG_DESC1`, `MARKETING_DESCRIPTION` | 8 |
| **Features** | `ITEM_FEATURES_1` through `ITEM_FEATURES_20` | 20 |
| **Attributes** | `ATTRIBUTE_LABEL`, `ATTRIBUTE_VALUE`, `ATTRIBUTE_UOM` | 150 |
| **Dimensions** | `LENGTH`, `HEIGHT`, `WIDTH`, `WEIGHT`, `VOLUME` | 10 |
| **Media/Docs** | `Product Image`, `Spec Sheet`, `Catalog`, `SDS` | 25 |

---

## 🧪 Live Demo & 100% Accuracy Validation

*(Insert Demo Video Here)*

During a live E2E extraction test of the **Eaton 9PX1500RT** (a highly complex industrial UPS system), SEMI successfully parsed a massive 50+ page manufacturer PDF and accurately mapped **over 40 distinct properties** to the Unilog format, including:

- **AC Mode Efficiency Rating:** `90.28%`
- **Output waveform:** `True sine wave`
- **Input frequency range:** `60 Hz: 50–70 Hz, 50 Hz: 40–60 Hz`
- **Battery Technology:** `ABM technology (3-stage charging)`
- **Heat Dissipation (BTU/Hr):** `512`
- **Network Management Cards:** `Network-M3; INDGW-M2`

All variables passed the Adversarial Physics constraints with **100% verified confidence**.

---

## 🚀 Getting Started

### ☑️ Prerequisites

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

## 🗺 Roadmap

- [X] **Multi-LLM Redundancy:** Fallback to NVIDIA NIM.
- [X] **Unilog Format Support:** Strict 252-column export mapping.
- [ ] **Self-Hosted Mode:** Integration with vLLM for local air-gapped Gemma 4-31B deployment.
- [ ] **Vision Parsing:** Direct CAD/Blueprint dimension extraction using multimodal vision models.

---

## 🏆 Team

**Team UNIT**  
*Track: AI-Powered Product Intelligence for Industrial Commerce*  
UniHack 2026

[**Return to Top**](#-table-of-contents)
