"""
Bengaluru Tech Talent Intelligence — Complete Data Pipeline (v2.0 — TalentPulse)
Runs all steps: Load → Clean → NLP Extract → Salary Analysis → Company Analysis → Skill Gap
Generates all clean CSVs + data_quality.json metadata for the dashboard.

Data Integrity: salary_source column tracks 'disclosed' vs 'missing' from this step.
The enrich_salary.py script may later fill missing values and mark them as 'estimated'.
"""
import json
import pandas as pd
import numpy as np
import re
import os
import sys
from collections import Counter
from itertools import combinations
from collections import defaultdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nlp.skill_extractor import (
    extract_skills, extract_experience_range, get_company_tier,
    parse_salary_lpa, SKILL_CATEGORIES
)

CLEAN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'clean')
RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'raw')

os.makedirs(CLEAN_DIR, exist_ok=True)

# ======================================================================
# STEP 1: LOAD & MERGE DATASETS
# ======================================================================
print("=" * 60)
print("STEP 1: Loading datasets...")
print("=" * 60)

# Dataset 1: Naukri 30k general jobs
ds1_path = os.path.join(RAW_DIR, 'home', 'sdf',
                        'marketing_sample_for_naukri_com-jobs__20190701_20190830__30k_data.csv')
df1 = pd.read_csv(ds1_path)
print(f"  Dataset 1 (Naukri 30k): {len(df1)} rows, columns: {list(df1.columns)}")

# Rename to standard schema
df1 = df1.rename(columns={
    'Job Title': 'job_title',
    'Job Salary': 'salary_text',
    'Job Experience Required': 'experience_text',
    'Key Skills': 'job_description',   # Key Skills is the richest text field here
    'Role Category': 'role_category',
    'Location': 'location',
    'Functional Area': 'functional_area',
    'Industry': 'industry',
    'Role': 'role',
    'Uniq Id': 'id',
})

# Dataset 2: Naukri Data Science Jobs India (12k)
ds2_path = os.path.join(RAW_DIR, 'naukri_data_science_jobs_india.csv')
df2 = pd.read_csv(ds2_path)
print(f"  Dataset 2 (Naukri DS India): {len(df2)} rows, columns: {list(df2.columns)}")

df2 = df2.rename(columns={
    'Job_Role': 'job_title',
    'Company': 'company',
    'Location': 'location',
    'Job Experience': 'experience_text',
    'Skills/Description': 'job_description',
})

# Add source tags
df1['source'] = 'naukri_30k'
df2['source'] = 'naukri_ds_india'

# ======================================================================
# STEP 2: FILTER BENGALURU + DA/DS ROLES
# ======================================================================
print("\n" + "=" * 60)
print("STEP 2: Filtering Bengaluru + DA/DS roles...")
print("=" * 60)

# Filter Bengaluru from Dataset 1
mask_blr1 = df1['location'].str.contains('Bengaluru|Bangalore', case=False, na=False)
da_keywords = r'Data Analyst|Data Science|Data Scientist|Analytics|Business Analyst|BI Analyst|Business Intelligence|Machine Learning|Data Engineer|Big Data'
mask_da1 = df1['job_title'].str.contains(da_keywords, case=False, na=False)
df1_filtered = df1[mask_blr1 & mask_da1].copy()
print(f"  Dataset 1 → Bengaluru DA/DS: {len(df1_filtered)} rows")

# Filter Bengaluru from Dataset 2
mask_blr2 = df2['location'].str.contains('Bengaluru|Bangalore', case=False, na=False)
df2_filtered = df2[mask_blr2].copy()
print(f"  Dataset 2 → Bengaluru: {len(df2_filtered)} rows")

# Standardize columns for merge
common_cols = ['job_title', 'job_description', 'location', 'experience_text', 'source']
if 'company' not in df1_filtered.columns:
    df1_filtered['company'] = 'Unknown'
if 'salary_text' not in df2_filtered.columns:
    df2_filtered['salary_text'] = None

for col in ['company', 'salary_text']:
    if col not in df1_filtered.columns:
        df1_filtered[col] = None
    if col not in df2_filtered.columns:
        df2_filtered[col] = None

merge_cols = common_cols + ['company', 'salary_text']
df = pd.concat([df1_filtered[merge_cols], df2_filtered[merge_cols]], ignore_index=True)
print(f"\n  ✅ Merged dataset: {len(df)} Bengaluru DA/DS job postings")

# ======================================================================
# STEP 3: CLEAN DATA
# ======================================================================
print("\n" + "=" * 60)
print("STEP 3: Cleaning data...")
print("=" * 60)

# Clean text fields
df['job_description'] = df['job_description'].fillna('').astype(str).str.lower().str.strip()
df['job_title'] = df['job_title'].fillna('').astype(str).str.strip()
df['company'] = df['company'].fillna('Unknown').astype(str).str.strip()
df['location'] = df['location'].fillna('Bengaluru').astype(str).str.strip()

# Parse salary — and immediately record provenance
df['salary_lpa'] = df['salary_text'].apply(parse_salary_lpa)
df['salary_source'] = df['salary_lpa'].apply(lambda x: 'disclosed' if pd.notna(x) else 'missing')

# Parse experience
df['exp_min'], df['exp_max'] = zip(*df['experience_text'].apply(extract_experience_range))
df['exp_mid'] = ((df['exp_min'] + df['exp_max']) / 2).round(1)

# Experience bands
def get_exp_band(mid):
    if mid <= 1:
        return '0-1 yr (Fresher)'
    elif mid <= 3:
        return '1-3 yrs (Junior)'
    elif mid <= 5:
        return '3-5 yrs (Mid)'
    elif mid <= 8:
        return '5-8 yrs (Senior)'
    else:
        return '8+ yrs (Lead)'

df['exp_band'] = df['exp_mid'].apply(get_exp_band)

# Company tier
df['tier'] = df['company'].apply(get_company_tier)

# Drop exact duplicates
before = len(df)
df = df.drop_duplicates(subset=['job_title', 'company', 'job_description'], keep='first')
print(f"  Removed {before - len(df)} duplicates → {len(df)} unique jobs")
print(f"  Rows with salary: {df['salary_lpa'].notna().sum()} / {len(df)}")
print(f"  Experience bands: {df['exp_band'].value_counts().to_dict()}")
print(f"  Company tiers: {df['tier'].value_counts().to_dict()}")

# ======================================================================
# STEP 4: NLP SKILL EXTRACTION
# ======================================================================
print("\n" + "=" * 60)
print("STEP 4: NLP Skill Extraction...")
print("=" * 60)

# Also combine job_title for extraction (e.g., "Data Analyst - SQL, Python")
df['text_for_nlp'] = df['job_title'].str.lower() + ' ' + df['job_description']
df['skills_extracted'] = df['text_for_nlp'].apply(extract_skills)
df['skill_count'] = df['skills_extracted'].apply(len)

print(f"  Avg skills per job: {df['skill_count'].mean():.1f}")
print(f"  Max skills in a job: {df['skill_count'].max()}")
print(f"  Jobs with 0 skills: {(df['skill_count'] == 0).sum()}")

# Save clean jobs
df.to_csv(os.path.join(CLEAN_DIR, 'jobs_clean.csv'), index=False)
print(f"  ✅ Saved jobs_clean.csv ({len(df)} rows)")

# ======================================================================
# STEP 5: BUILD SKILL FREQUENCY TABLE
# ======================================================================
print("\n" + "=" * 60)
print("STEP 5: Building skill frequency table...")
print("=" * 60)

all_skills = [s for skills in df['skills_extracted'] for s in skills]
counts = Counter(all_skills)

rows = []
for skill, count in counts.most_common():
    jobs_with_skill = df[df['skills_extracted'].apply(lambda x: skill in x)]
    avg_sal = jobs_with_skill['salary_lpa'].mean()
    med_sal = jobs_with_skill['salary_lpa'].median()
    avg_exp = jobs_with_skill['exp_mid'].mean()
    category = SKILL_CATEGORIES.get(skill, 'Other')
    rows.append({
        'skill': skill,
        'count': count,
        'pct_of_jobs': round(count / len(df) * 100, 1),
        'avg_salary': round(avg_sal, 2) if not pd.isna(avg_sal) else None,
        'median_salary': round(med_sal, 2) if not pd.isna(med_sal) else None,
        'avg_experience': round(avg_exp, 1) if not pd.isna(avg_exp) else None,
        'category': category,
    })

skill_freq = pd.DataFrame(rows)
skill_freq.to_csv(os.path.join(CLEAN_DIR, 'skill_frequency.csv'), index=False)
print(f"  ✅ Saved skill_frequency.csv ({len(skill_freq)} skills)")
print(f"\n  Top 15 Skills:")
print(skill_freq.head(15)[['skill', 'count', 'pct_of_jobs', 'avg_salary']].to_string(index=False))

# ======================================================================
# STEP 6: SKILL COMBINATIONS SALARY ANALYSIS
# ======================================================================
print("\n" + "=" * 60)
print("STEP 6: Skill combination analysis...")
print("=" * 60)

combo_salary = defaultdict(list)
for _, row in df.iterrows():
    if pd.isna(row['salary_lpa']):
        continue
    skills = row['skills_extracted']
    if len(skills) < 2:
        continue
    for s1, s2 in combinations(sorted(skills), 2):
        combo_salary[f"{s1} + {s2}"].append(row['salary_lpa'])

combo_rows = [
    {
        'skill_pair': pair,
        'co_occurrences': len(sals),
        'avg_salary': round(sum(sals) / len(sals), 2),
        'min_salary': round(min(sals), 2),
        'max_salary': round(max(sals), 2),
    }
    for pair, sals in combo_salary.items() if len(sals) >= 3
]

combo_df = pd.DataFrame(combo_rows).sort_values('avg_salary', ascending=False)
combo_df.to_csv(os.path.join(CLEAN_DIR, 'skill_combos.csv'), index=False)
print(f"  ✅ Saved skill_combos.csv ({len(combo_df)} skill pairs)")
if len(combo_df) > 0:
    print(f"\n  Top 10 highest-paying combos:")
    print(combo_df.head(10)[['skill_pair', 'co_occurrences', 'avg_salary']].to_string(index=False))

# ======================================================================
# STEP 7: COMPANY ANALYSIS
# ======================================================================
print("\n" + "=" * 60)
print("STEP 7: Company analysis & tier classification...")
print("=" * 60)

company_df = df.groupby('company').agg(
    tier=('tier', 'first'),
    job_count=('job_title', 'count'),
    avg_salary=('salary_lpa', 'mean'),
    median_salary=('salary_lpa', 'median'),
    avg_experience=('exp_mid', 'mean'),
    top_skills=('skills_extracted', lambda x: ', '.join(
        [s for s, _ in Counter([sk for skills in x for sk in skills]).most_common(5)]
    )),
).reset_index()

company_df['avg_salary'] = company_df['avg_salary'].round(2)
company_df['median_salary'] = company_df['median_salary'].round(2)
company_df['avg_experience'] = company_df['avg_experience'].round(1)
company_df = company_df.sort_values('job_count', ascending=False)

company_df.to_csv(os.path.join(CLEAN_DIR, 'company_analysis.csv'), index=False)
print(f"  ✅ Saved company_analysis.csv ({len(company_df)} companies)")
print(f"\n  Top 15 hiring companies:")
print(company_df.head(15)[['company', 'tier', 'job_count', 'avg_salary']].to_string(index=False))

# Tier summary
tier_summary = df.groupby('tier').agg(
    total_jobs=('job_title', 'count'),
    avg_salary=('salary_lpa', 'mean'),
    median_salary=('salary_lpa', 'median'),
    unique_companies=('company', 'nunique'),
).reset_index()
tier_summary['avg_salary'] = tier_summary['avg_salary'].round(2)
tier_summary['median_salary'] = tier_summary['median_salary'].round(2)
tier_summary.to_csv(os.path.join(CLEAN_DIR, 'tier_summary.csv'), index=False)
print(f"\n  Tier Summary:")
print(tier_summary.to_string(index=False))

# ======================================================================
# STEP 8: SALARY BANDS BY EXPERIENCE
# ======================================================================
print("\n" + "=" * 60)
print("STEP 8: Salary bands by experience...")
print("=" * 60)

salary_df = df[df['salary_lpa'].notna()].copy()
if len(salary_df) > 0:
    bands = salary_df.groupby('exp_band')['salary_lpa'].agg(
        ['count', 'min', 'max', 'mean', 'median']
    ).reset_index()
    bands.columns = ['exp_band', 'job_count', 'min_salary', 'max_salary', 'avg_salary', 'median_salary']
    bands = bands.round(2)

    # Add percentage
    bands['pct_of_total'] = (bands['job_count'] / bands['job_count'].sum() * 100).round(1)

    bands.to_csv(os.path.join(CLEAN_DIR, 'salary_bands.csv'), index=False)
    print(f"  ✅ Saved salary_bands.csv")
    print(bands.to_string(index=False))
else:
    print("  ⚠️ No salary data available for bands")

# ======================================================================
# STEP 9: SKILL-TIER MATRIX
# ======================================================================
print("\n" + "=" * 60)
print("STEP 9: Skill-Tier matrix...")
print("=" * 60)

tier_skill_rows = []
for tier in df['tier'].unique():
    tier_jobs = df[df['tier'] == tier]
    tier_skills = [s for skills in tier_jobs['skills_extracted'] for s in skills]
    tier_counts = Counter(tier_skills)
    for skill, count in tier_counts.most_common(20):
        tier_skill_rows.append({
            'tier': tier,
            'skill': skill,
            'count': count,
            'pct_in_tier': round(count / len(tier_jobs) * 100, 1),
        })

tier_skill_df = pd.DataFrame(tier_skill_rows)
tier_skill_df.to_csv(os.path.join(CLEAN_DIR, 'tier_skill_matrix.csv'), index=False)
print(f"  ✅ Saved tier_skill_matrix.csv")

# ======================================================================
# STEP 10: DATA QUALITY METADATA
# ======================================================================
print("\n" + "=" * 60)
print("STEP 10: Generating data quality metadata...")
print("=" * 60)

total_jobs = len(df)
salary_disclosed = int((df['salary_source'] == 'disclosed').sum())
salary_missing = int((df['salary_source'] == 'missing').sum())
company_known = int((df['company'] != 'Unknown').sum())
company_unknown = int((df['company'] == 'Unknown').sum())
exp_parsed = int((df['exp_mid'] > 0).sum())
skills_nonzero = int((df['skill_count'] > 0).sum())

data_quality = {
    'pipeline_version': '2.0',
    'generated_at': pd.Timestamp.now().isoformat(),
    'dataset_sources': [
        {
            'name': 'Naukri 30K General Jobs',
            'file': 'marketing_sample_for_naukri_com-jobs__20190701_20190830__30k_data.csv',
            'period': 'July–August 2019',
            'original_rows': int(len(df1)),
            'after_filter': int(len(df1_filtered)),
            'has_company_field': False,
            'has_salary_field': True,
            'note': 'Skills extracted from Key Skills column, not full job description'
        },
        {
            'name': 'Naukri Data Science Jobs India',
            'file': 'naukri_data_science_jobs_india.csv',
            'period': 'Undated (likely 2023–2024)',
            'original_rows': int(len(df2)),
            'after_filter': int(len(df2_filtered)),
            'has_company_field': True,
            'has_salary_field': False,
            'note': 'Skills extracted from Skills/Description column'
        }
    ],
    'total_jobs_after_merge': total_jobs,
    'duplicates_removed': before - total_jobs,
    'coverage': {
        'salary': {
            'disclosed': salary_disclosed,
            'missing': salary_missing,
            'disclosed_pct': round(salary_disclosed / total_jobs * 100, 1),
            'note': 'Only disclosed salaries are used for salary statistics unless explicitly labeled as estimated'
        },
        'company': {
            'known': company_known,
            'unknown': company_unknown,
            'known_pct': round(company_known / total_jobs * 100, 1),
            'unique_known': int(df[df['company'] != 'Unknown']['company'].nunique()),
            'note': 'Dataset 1 lacks a company column; those rows are marked Unknown'
        },
        'experience': {
            'parsed': exp_parsed,
            'unparsed': total_jobs - exp_parsed,
            'parsed_pct': round(exp_parsed / total_jobs * 100, 1)
        },
        'skills': {
            'jobs_with_skills': skills_nonzero,
            'jobs_without_skills': total_jobs - skills_nonzero,
            'skills_coverage_pct': round(skills_nonzero / total_jobs * 100, 1),
            'unique_skills_detected': int(len(skill_freq)),
            'avg_skills_per_job': round(df['skill_count'].mean(), 1)
        }
    },
    'limitations': [
        'Dataset 1 is from July–August 2019 — salary benchmarks may not reflect current market rates.',
        'Dataset 2 has no date column — temporal trend analysis is not possible with this data.',
        f'{company_unknown} of {total_jobs} jobs ({round(company_unknown/total_jobs*100,1)}%) have unknown company names.',
        f'Only {salary_disclosed} of {total_jobs} jobs ({round(salary_disclosed/total_jobs*100,1)}%) have disclosed salary information.',
        'Salary parsing uses regex on unstructured text — some salaries may be misread or missed.',
        'Skill extraction uses keyword matching, not contextual NLP — accuracy ~90-95% for known DA/DS tools.',
        'Company tier classification uses substring matching against curated lists — unlisted companies default to Startup/Other.'
    ],
    'methodology': {
        'salary_parsing': 'Regex extraction from salary_text field. Patterns: X-Y LPA (midpoint), X LPA (direct), Indian format X,XX,XXX PA (converted to LPA), Rs/INR/₹ prefix (converted).',
        'skill_extraction': 'Vocabulary-based entity matching with 40+ canonical skills and 200+ keyword variants. Each job description is lowercased and checked for keyword presence.',
        'company_tiering': 'Substring match against curated lists: 43 Product companies, 19 Consulting firms, 21 MNC/IT Services. Default: Startup/Other.',
        'experience_parsing': 'Regex extraction of X-Y, X+, or single number patterns from experience text field.'
    },
    'tier_distribution': df['tier'].value_counts().to_dict(),
    'exp_band_distribution': df['exp_band'].value_counts().to_dict(),
    'salary_source_distribution': df['salary_source'].value_counts().to_dict()
}

with open(os.path.join(CLEAN_DIR, 'data_quality.json'), 'w') as f:
    json.dump(data_quality, f, indent=2, default=str)
print(f"  ✅ Saved data_quality.json")
print(f"  Salary coverage: {salary_disclosed}/{total_jobs} disclosed ({round(salary_disclosed/total_jobs*100,1)}%)")
print(f"  Company coverage: {company_known}/{total_jobs} known ({round(company_known/total_jobs*100,1)}%)")

# ======================================================================
# DONE
# ======================================================================
print("\n" + "=" * 60)
print("🎉 PIPELINE COMPLETE!")
print("=" * 60)
print(f"\nGenerated files in {CLEAN_DIR}:")
for f in sorted(os.listdir(CLEAN_DIR)):
    size = os.path.getsize(os.path.join(CLEAN_DIR, f))
    print(f"  📄 {f} ({size:,} bytes)")

print(f"\n📊 Summary:")
print(f"  Total Bengaluru DA/DS jobs: {len(df):,}")
print(f"  Skills extracted: {len(skill_freq)}")
print(f"  Companies analyzed: {len(company_df):,}")
print(f"  Skill pairs found: {len(combo_df):,}")
print(f"  Jobs with disclosed salary: {salary_disclosed:,} / {total_jobs:,}")
print(f"  Jobs with known company: {company_known:,} / {total_jobs:,}")
