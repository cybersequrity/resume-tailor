# Resume Tailor 🎯

An open-source, AI-powered ATS resume optimization engine with a modular master experience bank, anti-hallucination verification, and high-fidelity PDF compilation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)](https://streamlit.io)
[![Playwright](https://img.shields.io/badge/Playwright-Headless_Scraper-2EAD33.svg)](https://playwright.dev)
[![WeasyPrint](https://img.shields.io/badge/WeasyPrint-Print--Ready_PDF-38B2AC.svg)](https://weasyprint.org)

---

## 🔒 Privacy-First Architecture

Resume Tailor is engineered so you can freely clone, version-control, and contribute to this repository **without ever leaking your personal data or active job search history**:
- **Zero Cloud Storage**: All processing is local to your machine or self-hosted instance.
- **Git-Ignored Personal Data**: Your personal experience bank (`app/master_resume.json`), uploaded resumes (`uploads/`), and application history (`data/applications/`) are ignored by git by default.
- **Example Template Included**: A sanitized baseline (`app/master_resume.example.json`) is included so the tool runs out of the box.

---

## 🌟 Key Features

1. **Modular Master Experience Bank**
   - Stores your career accomplishments as structured, verified metric bullets.
   - Built on proven frameworks: **Google XYZ** (*Accomplished [X] as measured by [Y], by doing [Z]*) and **CAR** (*Context, Action, Result*).
   - Pre-populates **4 strategic wording variations per accomplishment metric**:
     - *Executive & Strategic Impact* (risk reduction, business enablement, leadership)
     - *Technical & Engineering Precision* (systems, controls, architecture, scripting)
     - *Governance & Regulatory Rigor* (NIST 800-53, RMF, ISO 27001, audit defensibility)
     - *Metric-First Google XYZ* (quantitative metric leading the bullet)

2. **Target Job Ingestion & Headless Scraper**
   - 1-click URL scraping powered by Playwright headless browser (supports LinkedIn, Indeed, Greenhouse, Lever, Workday, SmartRecruiters, and company career portals).
   - Automatically cleans boilerplates and extracts role titles, company names, and requirements.

3. **Anti-Hallucination Tailoring Studio**
   - Analyzes target JDs against your master experience bank.
   - Recommends the highest-relevance accomplishment bullets.
   - **Role-Level & Bullet-Level Checkboxes**: Include or exclude entire roles or individual bullets with 1 click.
   - **Dual-Engine Architecture**: Powered by Gemini 2.5 Flash for deep semantic reasoning, with a built-in **100% offline heuristic engine** that works with zero API keys.

4. **Application Version Archive**
   - Automatically archives tailored resumes, match scores, keyword analytics, and compiled PDFs for every application you submit.

5. **Print-Ready PDF & Markdown Export**
   - Compiles ATS-optimized, high-fidelity PDFs via **WeasyPrint** using clean CSS paged media standards.
   - Exports formatted Markdown for copy-pasting directly into online application portals.

---

## 🚀 Quickstart Guide

### 1. Prerequisites & System Dependencies

WeasyPrint requires standard system font and rendering libraries:

**Debian / Ubuntu / Docker:**
```bash
sudo apt-get update && sudo apt-get install -y \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info
```

**macOS (Homebrew):**
```bash
brew install pango cairo gdk-pixbuf libffi
```

**Windows:**
Follow the [WeasyPrint Windows installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).

### 2. Clone & Install Python Dependencies

```bash
git clone https://github.com/cybersequrity/resume-tailor.git
cd resume-tailor

python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium
```

### 3. (Optional) Configure Gemini API Key

Resume Tailor runs **100% offline** out of the box using its built-in heuristic optimization engine. To enable Gemini 2.5 Flash for semantic matching:

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 4. Launch the Studio

```bash
streamlit run app/main.py --server.port=8501
```

Open your browser to `http://localhost:8501`.

---

## 📂 Project Structure

```
├── app/
│   ├── main.py                     # Streamlit application UI & interaction logic
│   ├── tailor_engine.py            # Dual-engine tailoring (Gemini + Offline Heuristic)
│   ├── pdf_generator.py            # Jinja2 & WeasyPrint PDF generation pipeline
│   ├── pdf_parser.py               # PDF resume text extraction & deduplication
│   ├── job_scraper.py              # Playwright headless browser job posting scraper
│   ├── history_manager.py          # Application archive & version history manager
│   ├── master_resume_schema.json   # JSON Schema validation for experience banks
│   ├── master_resume.example.json  # Sanitized public baseline template
│   ├── master_resume.json          # Your private experience bank (git-ignored)
│   └── templates/
│       └── resume.html             # High-fidelity, ATS-compliant Jinja2 resume template
├── data/
│   └── applications/               # Local job application history (git-ignored)
├── uploads/                        # Resume PDFs for extraction (git-ignored)
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── .gitignore                      # Privacy-first git ignore rules
└── LICENSE                         # MIT License
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
