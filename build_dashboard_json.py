"""
Build Dashboard JSON (v2.0 — TalentPulse)

Reads all clean CSVs + data_quality.json from the pipeline and
generates webapp/public/dashboard_data.json with:
  - Full data quality metadata embedded
  - Salary source labels on every salary metric
  - Coverage indicators per section
"""
import pandas as pd
import json
import os
import ast

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR = os.path.join(BASE_DIR, 'data', 'clean')
OUTPUT_PATH = os.path.join(BASE_DIR, 'webapp', 'public', 'dashboard_data.json')

# ---- Load all data ----
df = pd.read_csv(os.path.join(CLEAN_DIR, 'jobs_clean.csv'))
df['skills_extracted'] = df['skills_extracted'].apply(
    lambda x: ast.literal_eval(x) if isinstance(x, str) else []
)

skill_freq = pd.read_csv(os.path.join(CLEAN_DIR, 'skill_frequency.csv'))
company_df = pd.read_csv(os.path.join(CLEAN_DIR, 'company_analysis.csv'))
tier_summary = pd.read_csv(os.path.join(CLEAN_DIR, 'tier_summary.csv'))

# Load salary bands (both versions if available)
salary_bands_all = pd.read_csv(os.path.join(CLEAN_DIR, 'salary_bands.csv'))
salary_bands_disclosed_path = os.path.join(CLEAN_DIR, 'salary_bands_disclosed.csv')
salary_bands_disclosed = pd.read_csv(salary_bands_disclosed_path) if os.path.exists(salary_bands_disclosed_path) else pd.DataFrame()

combo_df_path = os.path.join(CLEAN_DIR, 'skill_combos.csv')
combo_df = pd.read_csv(combo_df_path) if os.path.exists(combo_df_path) else pd.DataFrame()

dq_path = os.path.join(CLEAN_DIR, 'data_quality.json')
data_quality = json.load(open(dq_path)) if os.path.exists(dq_path) else {}

# ---- Build stats ----
total_jobs = len(df)
disclosed_count = int((df['salary_source'] == 'disclosed').sum()) if 'salary_source' in df.columns else 0
estimated_count = int((df['salary_source'] == 'estimated').sum()) if 'salary_source' in df.columns else 0

# Salary stats — compute from disclosed only
disclosed_df = df[df['salary_source'] == 'disclosed'] if 'salary_source' in df.columns else df[df['salary_lpa'].notna()]
avg_salary_disclosed = round(disclosed_df['salary_lpa'].mean(), 2) if len(disclosed_df) > 0 else None
avg_salary_all = round(df['salary_lpa'].mean(), 2) if df['salary_lpa'].notna().any() else None

stats = {
    'total_jobs': total_jobs,
    'unique_companies': int(df[df['company'] != 'Unknown']['company'].nunique()),
    'unknown_company_count': int((df['company'] == 'Unknown').sum()),
    'avg_salary': avg_salary_all,
    'avg_salary_disclosed': avg_salary_disclosed,
    'salary_disclosed_count': disclosed_count,
    'salary_estimated_count': estimated_count,
    'salary_coverage_pct': round(disclosed_count / total_jobs * 100, 1) if total_jobs > 0 else 0,
    'salary_source_note': f'Only {disclosed_count} of {total_jobs} jobs ({round(disclosed_count/total_jobs*100, 1)}%) have employer-disclosed salary. Remaining salaries are model-estimated.',
    'unique_skills': int(len(skill_freq)),
    'avg_skills_per_job': round(df['skills_extracted'].apply(len).mean(), 1)
}

# ---- Build tier distribution ----
tier_dist = df['tier'].value_counts().to_dict()

# ---- Build tier summary ----
tier_summary_list = []
for _, row in tier_summary.iterrows():
    entry = row.to_dict()
    # Convert numpy types to native Python
    for k, v in entry.items():
        if hasattr(v, 'item'):
            entry[k] = v.item()
        if pd.isna(v):
            entry[k] = None
    tier_summary_list.append(entry)

# ---- Build skill frequency ----
skill_freq_list = []
for _, row in skill_freq.iterrows():
    entry = row.to_dict()
    for k, v in entry.items():
        if hasattr(v, 'item'):
            entry[k] = v.item()
        if isinstance(v, float) and pd.isna(v):
            entry[k] = None
    skill_freq_list.append(entry)

# ---- Build salary bands ----
def df_to_list(frame):
    result = []
    for _, row in frame.iterrows():
        entry = row.to_dict()
        for k, v in entry.items():
            if hasattr(v, 'item'):
                entry[k] = v.item()
            if isinstance(v, float) and pd.isna(v):
                entry[k] = None
        result.append(entry)
    return result

salary_bands_list = df_to_list(salary_bands_all)
salary_bands_disclosed_list = df_to_list(salary_bands_disclosed) if len(salary_bands_disclosed) > 0 else []

# ---- Build company data ----
top_companies_list = []
for _, row in company_df[company_df['company'] != 'Unknown'].head(50).iterrows():
    entry = row.to_dict()
    for k, v in entry.items():
        if hasattr(v, 'item'):
            entry[k] = v.item()
        if isinstance(v, float) and pd.isna(v):
            entry[k] = None
    top_companies_list.append(entry)

# ---- Build skill combos ----
combo_list = []
for _, row in combo_df.iterrows():
    entry = row.to_dict()
    for k, v in entry.items():
        if hasattr(v, 'item'):
            entry[k] = v.item()
        if isinstance(v, float) and pd.isna(v):
            entry[k] = None
    combo_list.append(entry)

# ---- Assemble final JSON ----
dashboard_data = {
    'stats': stats,
    'data_quality': data_quality,
    'tier_distribution': tier_dist,
    'tier_summary': tier_summary_list,
    'skill_frequency': skill_freq_list,
    'salary_bands': salary_bands_list,
    'salary_bands_disclosed': salary_bands_disclosed_list,
    'top_companies': top_companies_list,
    'skill_combos': combo_list,
}

with open(OUTPUT_PATH, 'w') as f:
    json.dump(dashboard_data, f, indent=2, default=str)

file_size = os.path.getsize(OUTPUT_PATH)
print(f"✅ Generated {OUTPUT_PATH}")
print(f"   Size: {file_size:,} bytes")
print(f"   Stats: {total_jobs} jobs, {disclosed_count} disclosed salaries, {len(skill_freq)} skills")
print(f"   Companies: {len(top_companies_list)} top companies included")
print(f"   Combos: {len(combo_list)} skill combos")
print(f"   Data quality metadata: {'included' if data_quality else 'missing'}")
