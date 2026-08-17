<p align="center">
  <img src="dashboard/public/logo.png" width="200" alt="SEMI Logo"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/UniHack-2026-blueviolet?style=for-the-badge" alt="UniHack 2026"/>
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react" alt="React"/>
  <img src="https://img.shields.io/badge/Gemma_4--31B-Google_AI-4285F4?style=for-the-badge&logo=google" alt="Gemma"/>
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
</p>

<h1 align="center">🧠 SEMI — Self-Evolving Manufacturer Intelligence</h1>

<p align="center">
  <strong>An AI-Powered Autonomous Product Data Extraction Engine for Industrial Commerce</strong>
</p>

<p align="center">
  <em>Transforming incomplete, fragmented manufacturer catalogs into fully enriched, audit-traceable, and Unilog-compliant product datasets with zero human intervention.</em>
</p>

---

## 🎯 The Problem: The Industrial Data Gap

In the industrial commerce sector, distributors constantly face a critical bottleneck: **inconsistent and incomplete product catalogs**. 
Manufacturers provide CSVs or spreadsheets that are missing up to 70%+ of crucial technical attributes (dimensions, pressures, voltages, compatibilities). Distributors are forced to hire teams to manually read dense, 100-page PDF spec sheets and manufacturer websites to find this data, leading to massive operational costs and delayed time-to-market.

## 💡 The Solution: SEMI

SEMI is a production-grade, autonomous data extraction pipeline built for **UniHack 2026**. Given a raw input catalog with just a `Manufacturer` and a `Part Number`, SEMI autonomously:

1. **Discovers** authoritative sources across the web using a priority-ranked search chain (bypassing e-commerce traps like Amazon/eBay).
2. **Extracts** every available technical attribute in a single pass using structured LLM calls via Google's Gemini / Gemma 4-31B.
3. **Audits** the extracted data using adversarial physics constraints and cross-source contradiction detection.
4. **Exports** a complete **252-column Unilog Delivery Format CSV** with full source provenance for every single attribute.

---

## 🚀 Demo & Accuracy Validation

*(Insert Video Link Here)*

In a live validation test against the `Eaton 9PX1500RT` (a complex industrial UPS system), SEMI accurately extracted **over 40 distinct attributes** straight from manufacturer PDFs, identifying details such as:
- **Output waveform**: True sine wave
- **Efficiency Rating**: 90.28%
- **Input frequency range**: 60 Hz: 50–70 Hz, 50 Hz: 40–60 Hz
- **Battery Technology**: ABM technology (3-stage charging)
- **Heat Dissipation**: 512 BTU/Hr

The system correctly bypassed all third-party reseller sites, validated the specs against physics constraints, and flagged the extracted attributes with **100% confidence**.

---

## 🏗️ Architecture & Core Technologies

SEMI utilizes a modern, async-first microservice architecture.

- **Frontend:** React 18, Vite, and TailwindCSS (Interactive Command Dashboard & Conflict Resolver)
- **Backend Orchestration:** FastAPI, Python 3.13, SQLite (Persistent State Graphs)
- **Discovery Chain:** Agent-Reach, DuckDuckGo, Exa, Firecrawl
- **Extraction Engine:** Google AI Studio (Gemini-2.5-Flash / Gemma-4-31B), Jina Reader for PDF parsing

### The Extraction Pipeline
1. **Ingestion**: Parses raw CSVs using LLM-assisted schema inference.
2. **Discovery**: Executes precise `site:manufacturer.com "SKU" spec` queries.
3. **Extraction**: Dynamically populates a JSON schema from parsed HTML/PDFs.
4. **Adversarial Audit**: Runs deterministic physics checks and split-conformal prediction intervals to reject hallucinations.
5. **Conflict Resolution**: Employs a Precedent KB to auto-resolve recurring data conflicts.

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Google AI Studio API Key](https://aistudio.google.com/apikey)

### Backend Setup
```bash
cd backend
python -m venv .venv
# Activate: .venv\Scripts\activate (Windows) or source .venv/bin/activate (Mac/Linux)
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env to set GOOGLE_API_KEY=your_key_here

# Start the FastApi Server
uvicorn backend.server:app --port 8000
```

### Dashboard Setup
```bash
cd dashboard
npm install
npm run dev
# The UI will be available at http://localhost:5173
```

---

## 🗺️ Roadmap & Future Improvements

- **Self-Hosted LLMs**: Transition from the Google AI Studio API to a fully localized vLLM deployment of Gemma 4-31B for air-gapped environments.
- **Active Learning**: Implement an active feedback loop where the Human-in-the-Loop resolutions fine-tune the extraction model dynamically.
- **Multi-Modal Parsing**: Integrate vision models to extract dimensional data directly from CAD diagrams and isometric product blueprints.

---

## 🏆 Team

**Team VarshneysvAI**  
*Track: AI-Powered Product Intelligence for Industrial Commerce*  

Built with ❤️ for UniHack 2026.