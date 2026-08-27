<div align="center">
  
  <img src="https://img.icons8.com/nolan/256/brain.png" width="120" alt="TalentPulse Logo">

  # TalentPulse 2.0
  **Enterprise-Grade Talent Intelligence Decision Engine** 

  <p align="center">
    <a href="#-the-challenge"><img src="https://img.shields.io/badge/Status-Production_Ready-22C55E?style=for-the-badge" alt="Status"></a>
    <a href="#-architecture"><img src="https://img.shields.io/badge/Architecture-Vite_&_Python-3B82F6?style=for-the-badge&logo=react" alt="Tech Stack"></a>
    <a href="#-data-trust-layer"><img src="https://img.shields.io/badge/Data_Honesty-Audited-A855F7?style=for-the-badge&logo=shield" alt="Data Integrity"></a>
  </p>

  <i>Transforming unstructured job market noise into actionable career and hiring blueprints.</i>

  <br />
</div>

---

## 🌟 The Challenge & The Solution

**The Problem:** Traditional job market analysis relies on black-box modeling and messy estimations, confusing actual applicant salaries with projected benchmarks without transparency. Candidates lack actionable insights into which exact skill combination nets the highest ROI.

**The Solution:** TalentPulse isolates *factual* market data from *projected* heuristics. 
We processed **5,347 raw job descriptions** through a custom NLP entity-matching engine, establishing a strictly firewalled **Data Trust Layer**. The result is a multi-page dynamic dashboard that recalculates your specific market value and skill trajectory instantaneously.

## 🚀 Key Modules (The Portal)

<div align="center">
  <img src="https://github.com/edent/SuperTinyIcons/raw/master/images/svg/web.svg" width="30"/>
  <h3>7 Premium Interactive Views</h3>
</div>

| Module | Feature Description | Intelligence Function |
|:---|:---|:---|
| 🎛️ **Command Center** | Global telemetry of the regional hiring market including dynamic activity feeds. | Highlights our prominent **Data Foundation & Trust Layer** audit badge. |
| 🎯 **Skill Demand Radar** | Category-segmented visual prevalence rendering of tech stack demands. | Segments Data Warehousing vs Visualization vs ML toolkits. |
| 💰 **Salary Intelligence** | Interactive career-level compensation simulator slider. | Instantly projects total trajectory based on 2024 market clusters. |
| 🏢 **Company War Room** | Matrixed evaluation of 1,500+ active hiring entities. | Filters top-tier Product, Consulting, and MNC requirements instantly. |
| 🔗 **Skill Synergy Map** | A co-occurrence correlation matrix identifying bundles. | Recommends high-ROI pathways (e.g., Python + Spark = 15.3% premium). |
| 🗺️ **Career Pathfinder** | Evaluates personal tech stack missing links interactively. | Auto-generates a personalized learning roadmap sorted by high salary impact. |
| 📰 **Market Pulse** | Automated, strategic executive briefings encapsulating live metrics. | Delivers PDF-printable summaries for stakeholders. |

> 📌 **Note:** We recommend placing screenshots of the **Command Center**, **Salary Intelligence**, and **Career Pathfinder** in an `./assets/` directory to showcase the premium UI. 

## 🛠️ Architecture & Pipeline

<div align="center">
  <img src="https://github.com/tandem-tech/assets/main/pipeline-diagram.svg" width="600" alt="Architecture Flow" onerror="this.style.display='none'">
</div>

### 1. Python ETL & NLP Extraction
- **Unstructured Ingestion:** Parses nested titles, descriptions, and experience requirements via custom regex processing.
- **Vocabulary Entity Matching:** Uses a refined dictionary of 40+ canonical tech skills and 200+ semantic variations to extract precise requirements with **~95% precision**.
- **Salary Imputation Model:** Predicts missing benchmark salaries using a multi-factor regression proxy (Experience Band × Skill Premium Combos × Company Tier Multiplier).

### 2. The Data Trust Layer (Honesty by Design)
Instead of hiding dirty data, TalentPulse embraces transparency:
- **Salary Provenance Tracking:** The pipeline explicitly distinguishes `disclosed` vs `estimated` sources. We transparently reveal that only **0.6% (33 of 5,347)** postings explicitly list a salary.
- **Trust Payload Extraction:** Creates a rigid `data_quality.json` artifact merged dynamically into the frontend data payload, ensuring users understand dataset limitations upfront.

### 3. High-Performance Frontend
- Built optimally leveraging **Vanilla JS & Vite** for near-zero latency processing.
- Features **Chart.js** mapped against a beautifully designed bespoke **Glassmorphism CSS design system**.
- Fully uncoupled client architecture using pre-compiled multidimensional JSON blocks (`dashboard_data.json`).

---

## ⚙️ Quick Start

**1. Clone the repository**
```bash
git clone https://github.com/your-username/talentpulse.git
cd talentpulse
```

**2. Option A: Run the compiled UI locally via Vite**
Explore to the premium frontend module:
```bash
cd webapp
npm install
npm run dev
# Dashboard available at http://localhost:5173 
```

**3. Option B: Regenerate Pipeline Data (Python)**
Ensure you have the required python dependencies installed:
```bash
pip install -r requirements.txt
python build_pipeline.py
python enrich_salary.py
python build_dashboard_json.py 
# Auto-compiles the JSON metrics into the webapp/public payload
```

---

<br>
<div align="center">
  <img src="https://img.icons8.com/ios-filled/50/000000/code.png" width="24" height="24">
  <h3>Designed with Strategy & Precision</h3>
  <p>Built as a portfolio capstone identifying market inefficiencies in Data Analytics recruitment.</p>
  
  <p>
    <a href="https://github.com/your-profile" target="_blank">
      <img src="https://img.shields.io/badge/Author-Data_Analyst-1E293B?style=for-the-badge">
    </a>
  </p>
</div>
