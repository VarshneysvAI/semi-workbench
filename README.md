# SEMI — Self-Evolving Manufacturer Intelligence

<p align="center">
  <img src="dashboard/public/logo.png" width="180" alt="SEMI Logo">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18.0-61DAFB.svg?style=flat&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/Vite-5.0-646CFF.svg?style=flat&logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/SQLite-3.0-003B57.svg?style=flat&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat" alt="License">
</p>

---

### 🎯 The Hook
SEMI is an autonomous AI data intelligence engine that converts raw 2-column industrial catalog spreadsheets (Part Number + Manufacturer) into fully enriched, 252-column B2B Unilog delivery files in seconds—with zero human hallucination risks.

---

## 💡 The Problem & Solution

* **The Pain Point:** B2B industrial distributors receive raw catalog spreadsheets missing up to 70%+ of crucial technical attributes (voltage ratings, dimensions, pressure tolerances, and compliance standards). Hiring teams to manually read 100-page manufacturer PDF spec sheets costs millions of dollars annually and causes massive catalog onboarding delays.
* **Our Solution:** SEMI autonomously scours official manufacturer spec sheets, extracts 40+ dynamic attributes using LLMs, verifies every data point against physics constraints to prevent AI hallucinations, and emits standardized e-commerce delivery files instantly.

---

## ✨ Core Features

* **Autonomous Spec Sheet Discovery:** Automatically locates official manufacturer PDF spec sheets while filtering out third-party reseller noise.
* **LLM Extraction & Provenance Tracking:** Extracts technical specs in parallel with field-level evidence snippets, source URLs, and confidence intervals ($[0.85 - 0.99]$).
* **5-Tier Adversarial Audit Engine:** Validates data against physical boundaries, dimensional constraints, and unit consistency—refusing to emit hallucinated values.
* **Human-in-the-Loop Review Queue:** Features an interactive review interface with clickable source links for one-click conflict resolution (`Adopt A/B`).
* **252-Column Unilog Compliance:** Automatically maps extracted attributes directly into standard B2B e-commerce delivery formats.

---

## 📸 Visual Proof & Interactive Dashboard

<p align="center">
  <img src="output_mvp_demo/mvp_1.png" alt="SEMI Overview Dashboard" width="100%">
  <em>Fig 1 — SEMI Ingestion Dashboard: Batch catalog upload, streaming worker status, and active row metrics.</em>
</p>

<p align="center">
  <img src="output_mvp_demo/mvp_3.png" alt="Dynamic Attribute Inspector" width="100%">
  <em>Fig 2 — Dynamic Attribute Inspector: Click any SKU to inspect real extracted attributes, confidence intervals, and direct PDF citations.</em>
</p>

<p align="center">
  <img src="output_mvp_demo/mvp_6.png" alt="Human-in-the-Loop Review Queue" width="100%">
  <em>Fig 3 — Human-in-the-Loop Review Queue: One-click resolution for catalog vs. web inferred data conflicts.</em>
</p>

---

## 🛠️ Built With

* **Frontend:** React 18, Vite 5, TailwindCSS 3.4, Lucide Icons
* **Backend:** Python 3.11+, FastAPI, Uvicorn Async Server
* **AI & Web Scrapers:** Google Gemini 2.5 / NVIDIA NIM Router, Crawl4AI 0.9, Jina Reader
* **Database & Storage:** SQLite, Local Storage Persistence Engine

---

## 🚀 Getting Started

### 📋 Prerequisites
* **Python**: `3.11` or higher
* **Node.js**: `18.0` or higher (`npm` 9+)

### 🔧 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/VarshneysvAI/semi-workbench.git
   cd semi-workbench
   ```

2. **Set up the Backend environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file in the `backend/` directory:
   ```env
   PRIMARY_PROVIDER=nim
   FALLBACK_PROVIDERS=gemini
   LLM_API_KEY_NIM=your_nvidia_nim_key
   GOOGLE_API_KEY=your_gemini_key
   CONCURRENCY=3
   CACHE_ENABLED=true
   MAX_ROWS_PER_RUN=200
   ```

4. **Build and launch the application**
   ```bash
   # Build the production dashboard static bundle
   cd dashboard && npm install && npm run build && cd ..

   # Run the unified live web server
   python -m uvicorn backend.live_app:app --host 127.0.0.1 --port 8000
   ```
   Open **`http://127.0.0.1:8000`** in your browser.

---

## 🧪 Running Tests & Validation

Validate the pipeline and run edge-case verification tests:

```bash
# Run backend pytest suite
pytest backend/tests/

# Run CLI batch test on the MVP 5-row dataset
python -m backend.cli --input tests/data/mvp_5_rows.csv --output output_demo --max-rows 5
```

---

## 📜 License & Acknowledgments

Distributed under the **MIT License**. See `LICENSE` for more information.

Developed by **Team VarshneysvAI** for **UniHack 2026**.
*Track: AI-Powered Product Intelligence for Industrial Commerce*
