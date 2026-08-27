CREATE TABLE IF NOT EXISTS jobs (
    job_id         INT PRIMARY KEY,
    company        VARCHAR(100),
    job_title      VARCHAR(200),
    location       VARCHAR(100),
    salary_lpa     DECIMAL(5,2),
    date_posted    DATE,
    experience_years INT,
    company_tier   VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id INT, skill VARCHAR(50),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

-- Query 1 — Avg salary by skill
SELECT js.skill,
    COUNT(DISTINCT j.job_id) AS job_count,
    ROUND(COUNT(DISTINCT j.job_id)*100.0/(SELECT COUNT(*) FROM jobs),1) AS pct_jobs,
    ROUND(AVG(j.salary_lpa),2) AS avg_salary
FROM job_skills js 
JOIN jobs j ON js.job_id = j.job_id
WHERE j.salary_lpa IS NOT NULL
GROUP BY js.skill 
ORDER BY avg_salary DESC;

-- Query 2 — Salary by company tier
SELECT company_tier,
    COUNT(*) AS jobs,
    ROUND(AVG(salary_lpa),2) AS avg_sal,
    ROUND(MIN(salary_lpa),2) AS min_sal,
    ROUND(MAX(salary_lpa),2) AS max_sal
FROM jobs 
WHERE salary_lpa IS NOT NULL
GROUP BY company_tier 
ORDER BY avg_sal DESC;

-- Query 3 — Top skill combinations by salary
SELECT a.skill AS s1, b.skill AS s2,
    COUNT(*) AS co_occur,
    ROUND(AVG(j.salary_lpa),2) AS avg_salary_combo
FROM job_skills a
JOIN job_skills b ON a.job_id = b.job_id AND a.skill < b.skill
JOIN jobs j ON a.job_id = j.job_id
WHERE j.salary_lpa IS NOT NULL
GROUP BY a.skill, b.skill 
HAVING COUNT(*) > 10
ORDER BY avg_salary_combo DESC 
LIMIT 20;
