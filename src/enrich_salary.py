"""
Salary Enrichment Script (v2.0 — TalentPulse)

Fills missing salaries using an experience-based estimation model.
CRITICAL: Preserves the original disclosed salary in 'salary_disclosed' column
and marks estimated values with salary_source = 'estimated'.

The dashboard should ALWAYS distinguish between:
  - 'disclosed': Original salary parsed from job posting text
  - 'estimated': Model-generated salary (not real data)
  - 'missing':   No salary available (should not exist after enrichment)

Estimation model: base_salary × skill_premium × tier_multiplier + noise
Based on AmbitionBox/Glassdoor Bengaluru DA/DS 2024 benchmarks.
"""
import pandas as pd
import numpy as np
import os, ast, json

CLEAN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'clean')

df = pd.read_csv(os.path.join(CLEAN_DIR, 'jobs_clean.csv'))

# Parse skills list from string
def safe_parse_list(x):
    try:
        return ast.literal_eval(x)
    except:
        return []

df['skills_extracted'] = df['skills_extracted'].apply(safe_parse_list)

# ---- PRESERVE ORIGINAL DISCLOSED SALARY ----
# Store the original disclosed salary in a separate column BEFORE any enrichment.
# This column will NEVER be overwritten.
df['salary_disclosed'] = df['salary_lpa'].copy()

# Ensure salary_source column exists (should be set by build_pipeline.py v2.0)
if 'salary_source' not in df.columns:
    df['salary_source'] = df['salary_lpa'].apply(lambda x: 'disclosed' if pd.notna(x) else 'missing')

print(f"Before enrichment:")
print(f"  Total jobs: {len(df)}")
print(f"  Disclosed salaries: {(df['salary_source'] == 'disclosed').sum()}")
print(f"  Missing salaries: {(df['salary_source'] == 'missing').sum()}")

# ---- MARKET BENCHMARK SALARY MODEL ----
# Based on AmbitionBox/Glassdoor Bengaluru DA/DS 2024 data
BENCHMARK_SALARY = {
    '0-1 yr (Fresher)': {'base': 4.0, 'range': (2.5, 6.0)},
    '1-3 yrs (Junior)': {'base': 6.5, 'range': (4.0, 10.0)},
    '3-5 yrs (Mid)':    {'base': 10.0, 'range': (7.0, 15.0)},
    '5-8 yrs (Senior)': {'base': 15.0, 'range': (10.0, 25.0)},
    '8+ yrs (Lead)':    {'base': 22.0, 'range': (15.0, 40.0)},
}

# Skill premium multipliers
SKILL_PREMIUMS = {
    'Python': 1.10, 'SQL': 1.05, 'Spark': 1.20, 'dbt': 1.25,
    'Machine Learning': 1.18, 'Airflow': 1.15, 'AWS': 1.12,
    'Azure': 1.10, 'GCP': 1.12, 'Snowflake': 1.15, 'Databricks': 1.20,
    'Kafka': 1.15, 'Docker': 1.12, 'NLP': 1.20, 'TensorFlow': 1.15,
    'Scikit-learn': 1.10, 'Data Modeling': 1.08, 'NoSQL': 1.05,
    'Scala': 1.12, 'Power BI': 1.05, 'Tableau': 1.08,
    'Statistics': 1.08, 'A/B Testing': 1.12, 'ETL': 1.05,
    'R': 1.05, 'Excel': 1.0, 'Git': 1.02, 'Communication': 1.0,
    'Agile': 1.02,
}

# Tier multipliers
TIER_MULT = {
    'Product': 1.25,
    'Consulting': 1.10,
    'MNC/IT Services': 0.95,
    'Startup/Other': 1.0,
}

np.random.seed(42)

def estimate_salary(row):
    """Estimate salary ONLY for rows with missing salary. Never touch disclosed."""
    # NEVER overwrite a disclosed salary
    if row['salary_source'] == 'disclosed':
        return row['salary_lpa']

    band = row.get('exp_band', '1-3 yrs (Junior)')
    bench = BENCHMARK_SALARY.get(band, BENCHMARK_SALARY['1-3 yrs (Junior)'])
    base = bench['base']
    lo, hi = bench['range']

    # Apply skill premium (top 3 highest-premium skills)
    skills = row.get('skills_extracted', [])
    if isinstance(skills, str):
        try:
            skills = ast.literal_eval(skills)
        except:
            skills = []
    premiums = sorted([SKILL_PREMIUMS.get(s, 1.0) for s in skills], reverse=True)[:3]
    premium = np.mean(premiums) if premiums else 1.0

    # Tier adjustment
    tier = row.get('tier', 'Startup/Other')
    tier_mult = TIER_MULT.get(tier, 1.0)

    est = base * premium * tier_mult
    noise = np.random.normal(0, (hi - lo) * 0.08)
    est = np.clip(est + noise, lo, hi)
    return round(est, 2)


# Apply estimation — only fills missing, never touches disclosed
df['salary_lpa'] = df.apply(estimate_salary, axis=1)

# Mark estimated rows — CRITICAL: only change 'missing' → 'estimated', never touch 'disclosed'
df.loc[df['salary_source'] == 'missing', 'salary_source'] = 'estimated'

estimated_count = (df['salary_source'] == 'estimated').sum()
disclosed_count = (df['salary_source'] == 'disclosed').sum()

print(f"\nAfter enrichment:")
print(f"  Disclosed salaries: {disclosed_count} (preserved, untouched)")
print(f"  Estimated salaries: {estimated_count} (model-generated)")
print(f"  Salary stats (all): mean={df['salary_lpa'].mean():.2f}, median={df['salary_lpa'].median():.2f}")
print(f"  Salary stats (disclosed only): mean={df[df['salary_source']=='disclosed']['salary_lpa'].mean():.2f}")

# ---- REBUILD ALL ANALYTICS WITH ENRICHED DATA ----
from collections import Counter, defaultdict
from itertools import combinations
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nlp.skill_extractor import SKILL_CATEGORIES

# Rebuild skill_frequency.csv — compute both disclosed-only and all-data salary stats
all_skills = [s for skills in df['skills_extracted'] for s in skills]
counts = Counter(all_skills)

rows = []
for skill, count in counts.most_common():
    jobs_with_skill = df[df['skills_extracted'].apply(lambda x: skill in x)]
    disclosed_jobs = jobs_with_skill[jobs_with_skill['salary_source'] == 'disclosed']

    avg_sal_all = jobs_with_skill['salary_lpa'].mean()
    avg_sal_disclosed = disclosed_jobs['salary_lpa'].mean() if len(disclosed_jobs) > 0 else None
    med_sal_disclosed = disclosed_jobs['salary_lpa'].median() if len(disclosed_jobs) > 0 else None
    avg_exp = jobs_with_skill['exp_mid'].mean()
    category = SKILL_CATEGORIES.get(skill, 'Other')

    rows.append({
        'skill': skill,
        'count': count,
        'pct_of_jobs': round(count / len(df) * 100, 1),
        'avg_salary': round(avg_sal_all, 2) if not pd.isna(avg_sal_all) else None,
        'avg_salary_disclosed': round(avg_sal_disclosed, 2) if avg_sal_disclosed and not pd.isna(avg_sal_disclosed) else None,
        'median_salary': round(med_sal_disclosed, 2) if med_sal_disclosed and not pd.isna(med_sal_disclosed) else None,
        'salary_sample_size': int(len(disclosed_jobs)),
        'avg_experience': round(avg_exp, 1),
        'category': category,
    })

skill_freq = pd.DataFrame(rows)
skill_freq.to_csv(os.path.join(CLEAN_DIR, 'skill_frequency.csv'), index=False)
print(f"\n✅ Rebuilt skill_frequency.csv ({len(skill_freq)} skills)")
print(skill_freq.head(15).to_string(index=False))

# Rebuild skill_combos.csv — use ONLY disclosed salary data
combo_salary = defaultdict(list)
for _, row in df.iterrows():
    if row['salary_source'] != 'disclosed':
        continue
    skills = row['skills_extracted']
    if len(skills) < 2:
        continue
    for s1, s2 in combinations(sorted(skills), 2):
        combo_salary[f"{s1} + {s2}"].append(row['salary_lpa'])

combo_rows = [
    {'skill_pair': pair, 'co_occurrences': len(sals),
     'avg_salary': round(sum(sals)/len(sals), 2),
     'salary_source': 'disclosed_only'}
    for pair, sals in combo_salary.items() if len(sals) >= 3
]

# Also compute combos using ALL data (including estimated) — clearly labeled
combo_salary_all = defaultdict(list)
for _, row in df.iterrows():
    skills = row['skills_extracted']
    if len(skills) < 2:
        continue
    for s1, s2 in combinations(sorted(skills), 2):
        combo_salary_all[f"{s1} + {s2}"].append(row['salary_lpa'])

combo_rows_all = [
    {'skill_pair': pair, 'co_occurrences': len(sals),
     'avg_salary': round(sum(sals)/len(sals), 2),
     'salary_source': 'all_including_estimated'}
    for pair, sals in combo_salary_all.items() if len(sals) >= 5
]

combo_rows.extend(combo_rows_all)
combo_df = pd.DataFrame(combo_rows)
if len(combo_df) > 0:
    combo_df = combo_df.sort_values('avg_salary', ascending=False)
combo_df.to_csv(os.path.join(CLEAN_DIR, 'skill_combos.csv'), index=False)
print(f"\n✅ Rebuilt skill_combos.csv ({len(combo_df)} pairs, disclosed salary only)")

# Rebuild salary_bands.csv — separate disclosed vs all
for suffix, subset in [('', df), ('_disclosed', df[df['salary_source'] == 'disclosed'])]:
    if len(subset) == 0:
        continue
    bands = subset.groupby('exp_band')['salary_lpa'].agg(
        ['count', 'min', 'max', 'mean', 'median']
    ).reset_index()
    bands.columns = ['exp_band', 'job_count', 'min_salary', 'max_salary', 'avg_salary', 'median_salary']
    bands = bands.round(2)
    bands['pct_of_total'] = (bands['job_count'] / bands['job_count'].sum() * 100).round(1)
    bands['salary_source'] = 'disclosed_only' if suffix else 'all_including_estimated'
    bands.to_csv(os.path.join(CLEAN_DIR, f'salary_bands{suffix}.csv'), index=False)
    print(f"\n✅ Rebuilt salary_bands{suffix}.csv")
    print(bands.to_string(index=False))

# Rebuild company_analysis.csv
company_df = df.groupby('company').agg(
    tier=('tier', 'first'),
    job_count=('job_title', 'count'),
    avg_salary=('salary_lpa', 'mean'),
    median_salary=('salary_lpa', 'median'),
    avg_experience=('exp_mid', 'mean'),
    disclosed_salary_count=('salary_source', lambda x: (x == 'disclosed').sum()),
    top_skills=('skills_extracted', lambda x: ', '.join(
        [s for s, _ in Counter([sk for skills in x for sk in skills]).most_common(5)]
    )),
).reset_index()
company_df['avg_salary'] = company_df['avg_salary'].round(2)
company_df['median_salary'] = company_df['median_salary'].round(2)
company_df['avg_experience'] = company_df['avg_experience'].round(1)
company_df['salary_data_note'] = company_df['disclosed_salary_count'].apply(
    lambda x: 'disclosed' if x > 0 else 'estimated_only'
)
company_df = company_df.sort_values('job_count', ascending=False)
company_df.to_csv(os.path.join(CLEAN_DIR, 'company_analysis.csv'), index=False)
print(f"\n✅ Rebuilt company_analysis.csv")

# Rebuild tier_summary.csv
tier_summary = df.groupby('tier').agg(
    total_jobs=('job_title', 'count'),
    avg_salary=('salary_lpa', 'mean'),
    median_salary=('salary_lpa', 'median'),
    unique_companies=('company', 'nunique'),
    disclosed_salary_count=('salary_source', lambda x: (x == 'disclosed').sum()),
).reset_index()
tier_summary['avg_salary'] = tier_summary['avg_salary'].round(2)
tier_summary['median_salary'] = tier_summary['median_salary'].round(2)
tier_summary['salary_note'] = tier_summary.apply(
    lambda r: f"{r['disclosed_salary_count']}/{r['total_jobs']} disclosed", axis=1
)
tier_summary.to_csv(os.path.join(CLEAN_DIR, 'tier_summary.csv'), index=False)
print(f"\n✅ Rebuilt tier_summary.csv")
print(tier_summary.to_string(index=False))

# Save final jobs CSV with explicit salary_source preserved
df['skills_extracted'] = df['skills_extracted'].apply(str)
df.to_csv(os.path.join(CLEAN_DIR, 'jobs_clean.csv'), index=False)

# Update data_quality.json with post-enrichment stats
dq_path = os.path.join(CLEAN_DIR, 'data_quality.json')
if os.path.exists(dq_path):
    with open(dq_path) as f:
        dq = json.load(f)
    dq['enrichment'] = {
        'model': 'base_salary × skill_premium × tier_multiplier + noise',
        'disclosed_count': int(disclosed_count),
        'estimated_count': int(estimated_count),
        'total': int(len(df)),
        'disclosed_pct': round(disclosed_count / len(df) * 100, 1),
        'benchmarks_source': 'AmbitionBox/Glassdoor Bengaluru DA/DS 2024',
        'note': 'Estimated salaries are model-generated and should never be presented as observed data.'
    }
    dq['salary_source_distribution'] = df['salary_source'].value_counts().to_dict()
    with open(dq_path, 'w') as f:
        json.dump(dq, f, indent=2, default=str)
    print(f"\n✅ Updated data_quality.json with enrichment metadata")

print("\n🎉 ALL DATA ENRICHED AND READY FOR DASHBOARD!")
print("⚠️  REMINDER: salary_source column distinguishes 'disclosed' from 'estimated'.")
print("    Dashboard must clearly label any metric that includes estimated data.")
