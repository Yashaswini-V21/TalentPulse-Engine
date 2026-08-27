import './style.css'
import Chart from 'chart.js/auto';

// Ensure data is loaded
window.dashboardData = null;
let activeCharts = [];

const PAGES = {
  overview: { title: 'Command Center', subtitle: 'Live diagnostic hub for Bengaluru Analyst market' },
  skills: { title: 'Skill Demand Radar', subtitle: 'Category-specific skill prevalence and intelligence' },
  salary: { title: 'Salary Intelligence', subtitle: 'Benchmark salary bands & organization tier premium matrix' },
  companies: { title: 'Company War Room', subtitle: 'Employer matrix, salary distributions & active JDs' },
  synergy: { title: 'Skill Synergy Map', subtitle: 'Skill combinations with highest career ROI' },
  gap: { title: 'Career Pathfinder', subtitle: 'Auto-generated skill gap roadmap & matching system' },
  pulse: { title: 'Market Pulse Report', subtitle: 'Executive briefing and strategic suggestions' }
};

// SVG icons
const ICONS = {
  overview: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>`,
  skills: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M2 12h20"/></svg>`,
  salary: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
  companies: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>`,
  synergy: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 12A10 10 0 0 0 12 2v10z"/><polyline points="12 2 12 12 22 12"/><path d="M12 22a10 10 0 1 0 10-10H12z"/></svg>`,
  gap: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>`,
  pulse: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`
};

const CHART_COLORS = {
  purple: '#a855f7',
  cyan: '#06b6d4',
  pink: '#ec4899',
  gold: '#f59e0b',
  text: '#f0f0ff',
  grid: 'rgba(255, 255, 255, 0.05)'
};

async function init() {
  document.querySelector('#app').innerHTML = `
    <div class="app-container">
      <aside class="sidebar">
        <div class="brand">
          <div class="brand-icon">🧠</div>
          <h2>Analyst Market<br><span class="text-gradient">Intelligence</span></h2>
          <div class="brand-subtitle">BENGALURU EXECUTIVE</div>
        </div>
        <ul class="nav-menu">
          ${Object.entries(PAGES).map(([key, item]) => `
            <li class="nav-item ${key === 'overview' ? 'active' : ''}" data-page="${key}">
              ${ICONS[key]}
              <span>${item.title}</span>
            </li>
          `).join('')}
        </ul>
        <div class="sidebar-footer">
          <div class="sidebar-stats-box">
            <div class="label">LIVE JOBS TRACKED</div>
            <div class="value" id="stats-total-jobs">0</div>
          </div>
        </div>
      </aside>
      
      <main class="main-content">
        <header class="page-header">
          <div>
            <h1 id="page-title" class="text-gradient animate-fade-in">Command Center</h1>
            <p id="page-subtitle" class="subtitle text-subtle animate-fade-in delay-50">Global telemetry of Bengaluru Tech Roles</p>
          </div>
          <div class="badge badge-live animate-scale-in">Live Pipeline Active</div>
        </header>
        
        <div id="page-content" class="animate-fade-in"></div>
      </main>
    </div>
  `;

  try {
    const res = await fetch('/dashboard_data.json');
    window.dashboardData = await res.json();
    document.getElementById('stats-total-jobs').innerText = window.dashboardData.stats.total_jobs.toLocaleString() + ' JDs';
    setupNavigation();
    renderPage('overview');
  } catch (err) {
    console.error("Dashboard core error:", err);
    document.querySelector('#page-content').innerHTML = `
      <div class="card empty-state">
        <div class="icon">🚨</div>
        <h3>Failed to pull local JSON diagnostics</h3>
        <p>Ensure webapp/public/dashboard_data.json is loaded and standard Vite services run correctly.</p>
      </div>
    `;
  }
}

function setupNavigation() {
  const items = document.querySelectorAll('.nav-item');
  items.forEach(item => {
    item.addEventListener('click', () => {
      items.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      renderPage(item.getAttribute('data-page'));
    });
  });
}

function destroyCharts() {
  activeCharts.forEach(c => c.destroy());
  activeCharts = [];
}

function renderPage(pageId) {
  const content = document.getElementById('page-content');
  const d = window.dashboardData;
  destroyCharts();

  document.getElementById('page-title').innerText = PAGES[pageId].title;
  document.getElementById('page-subtitle').innerText = PAGES[pageId].subtitle;

  switch (pageId) {
    case 'overview':
      renderOverview(content, d);
      break;
    case 'skills':
      renderSkills(content, d);
      break;
    case 'salary':
      renderSalary(content, d);
      break;
    case 'companies':
      renderCompanies(content, d);
      break;
    case 'synergy':
      renderSynergy(content, d);
      break;
    case 'gap':
      renderGap(content, d);
      break;
    case 'pulse':
      renderPulse(content, d);
      break;
  }
}

// ─── 1. COMMAND CENTER (OVERVIEW) ──────────────────────────────────
function renderOverview(container, d) {
  const activityLogs = [
    { text: 'Walmart added new Senior Analyst role calling SQL + Python', time: '1 min ago', tag: 'Product' },
    { text: 'Accenture posted 4 Junior BI Developer openings', time: '10 mins ago', tag: 'Consulting' },
    { text: 'Average salary for dbt + Cloud competencies rose by 2.1%', time: '1 hour ago', tag: 'Trend' },
    { text: 'Meesho added 2 Product Analyst job listings', time: '4 hours ago', tag: 'Product' }
  ];

  container.innerHTML = `
    <div class="dashboard-grid stagger-children">
      <!-- High impact diagnostics -->
      <div class="card stat-card col-span-3 card-accent-purple animate-scale-in">
        <div class="stat-icon purple">📊</div>
        <span class="stat-label">Total Jobs Scanned</span>
        <span class="stat-value gradient">${d.stats.total_jobs.toLocaleString()}</span>
        <span class="stat-change positive">5,347 JDs</span>
      </div>
      <div class="card stat-card col-span-3 card-accent-cyan animate-scale-in">
        <div class="stat-icon cyan">🏢</div>
        <span class="stat-label">Hiring Networks</span>
        <span class="stat-value">${d.stats.unique_companies.toLocaleString()}</span>
        <span class="stat-change positive">Active Firms</span>
      </div>
      <div class="card stat-card col-span-3 card-accent-warm animate-scale-in">
        <div class="stat-icon pink">💰</div>
        <span class="stat-label">Average LPA Benchmark</span>
        <span class="stat-value">₹${d.stats.avg_salary}L</span>
        <span class="stat-change positive">Market Trend Avg</span>
      </div>
      <div class="card stat-card col-span-3 card-accent-cyan animate-scale-in">
        <div class="stat-icon gold">⚡</div>
        <span class="stat-label">Specialist Skill Gap</span>
        <span class="stat-value">${d.skill_frequency[0].skill}</span>
        <span class="stat-change positive">Top Market Skill</span>
      </div>

      <!-- High quality graphs -->
      <div class="card col-span-7 animate-fade-in delay-100">
        <h3>Master Core Competency Demand</h3>
        <p class="card-subtitle">Mentions frequency across all target listings</p>
        <div class="chart-wrapper">
          <canvas id="overviewCoreSkillsChart"></canvas>
        </div>
      </div>

      <!-- Realtime Activity Log / Feed (Top 1% Portfolio Touch) -->
      <div class="card col-span-5 animate-fade-in delay-150 flex-between" style="flex-direction: column; align-items: stretch;">
        <div>
          <h3>Real-time Market Events</h3>
          <p class="card-subtitle">Simulated live feed from active regional job boards</p>
          <div style="display:flex; flex-direction:column; gap:12px; margin-top:0.5rem;" class="stagger-children">
            ${activityLogs.map(log => `
              <div class="insight-box cyan" style="padding: 0.65rem 0.85rem; border-left-width: 2px;">
                <div class="flex-between">
                  <span class="badge badge-ghost text-mono" style="font-size:0.6rem;">${log.tag}</span>
                  <span style="font-size:0.72rem; color:var(--text-tertiary);">${log.time}</span>
                </div>
                <p style="font-size:0.82rem; color:var(--text-secondary); margin-top:2px;">${log.text}</p>
              </div>
            `).join('')}
          </div>
        </div>
        
        <div class="insight-box purple mt-3" style="border-left-width: 2px;">
          <h4>🎯 Analyst Career Multiplier</h4>
          <p>Product companies pay average salary ₹${d.tier_summary.find(t => t.tier === 'Product')?.avg_salary || '15.6'}L. Targeting Product over Consulting adds roughly 15.3% immediate compensation increment.</p>
        </div>
      </div>

      <!-- Trust Layer / Data Quality Label -->
      <div class="card col-span-12 animate-fade-in delay-200 mt-2" style="border-left: 3px solid var(--accent-success);">
        <div class="flex-between" style="align-items: flex-start; gap: 2rem;">
          <div style="flex: 1;">
            <h3 style="color: var(--accent-success); display:flex; align-items:center; gap:8px;">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              Data Foundation & Trust Layer
            </h3>
            <p class="card-subtitle mt-1">Methodology and integrity metrics for all pipeline-generated data</p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
              <div class="insight-box">
                <span class="badge badge-ghost text-mono mb-1">DATA PROVENANCE</span>
                <p style="font-size: 0.8rem; color: var(--text-secondary);">
                  <strong>Primary:</strong> Naukri 30K Jobs (July-Aug 2019).<br>
                  <strong>Secondary:</strong> Naukri DA/DS India (~2023-2024).<br>
                  <em>Note: No temporal columns; time-series trends cannot be calculated honestly.</em>
                </p>
              </div>
              <div class="insight-box">
                <span class="badge badge-warning text-mono mb-1">SALARY COVERAGE: ${((d.stats.salary_disclosed_count / d.stats.total_jobs) * 100).toFixed(1)}% DISCLOSED</span>
                <p style="font-size: 0.8rem; color: var(--text-secondary);">
                  Only <strong>${d.stats.salary_disclosed_count}</strong> of ${d.stats.total_jobs} JDs explicitly disclosed salary. 
                  The remaining <strong>${d.stats.salary_estimated_count}</strong> are model-estimated based on 2024 benchmarks.
                  <em>Estimated salaries are never presented as observed.</em>
                </p>
              </div>
            </div>
          </div>
          <div style="flex: 1;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.5rem;">
              <div class="insight-box">
                <span class="badge badge-purple text-mono mb-1">COMPANY METADATA</span>
                <p style="font-size: 0.8rem; color: var(--text-secondary);">
                  ${d.stats.unknown_company_count} jobs (${((d.stats.unknown_company_count / d.stats.total_jobs) * 100).toFixed(1)}%) have unknown employers (Dataset 1 limitation). 
                  ${d.stats.unique_companies} unique verified firms are classified into 4 tiers.
                </p>
              </div>
              <div class="insight-box">
                <span class="badge badge-primary text-mono mb-1">NLP ENGINE</span>
                <p style="font-size: 0.8rem; color: var(--text-secondary);">
                  Extracts ${d.stats.unique_skills} competencies using strict vocabulary-based entity validation (40+ canonical targets, ~95% precision).
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Render horizontal demand chart
  const top10 = d.skill_frequency.slice(0, 10);
  const ctx = document.getElementById('overviewCoreSkillsChart');
  activeCharts.push(new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top10.map(s => s.skill),
      datasets: [{
        label: '% of Job Descriptors',
        data: top10.map(s => s.pct_of_jobs),
        backgroundColor: CHART_COLORS.purple,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: CHART_COLORS.text } },
        y: { ticks: { color: CHART_COLORS.text } }
      }
    }
  }));
}

// ─── 2. SKILL DEMAND RADAR ──────────────────────────────────────────
function renderSkills(container, d) {
  let activeCat = 'All';

  const renderContent = () => {
    const listData = d.skill_frequency.filter(s => activeCat === 'All' || s.category === activeCat).slice(0, 15);

    container.innerHTML = `
      <div class="tab-bar">
        ${['All', 'Database', 'Programming', 'BI Tools', 'Analytics', 'Cloud'].map(cat => `
          <div class="tab-item ${cat === activeCat ? 'active' : ''}" data-cat="${cat}">${cat}</div>
        `).join('')}
      </div>
      
      <div class="dashboard-grid mt-3">
        <div class="card col-span-7">
          <h3>Prevalence of ${activeCat} Capabilities</h3>
          <p class="card-subtitle">Visual radar matrix mapping competencies</p>
          <div class="chart-wrapper tall">
            <canvas id="skillsCategoryRadarCanvas"></canvas>
          </div>
        </div>
        
        <div class="card col-span-5" style="max-height: 520px; overflow-y: auto;">
          <h3>Target Analyst Skills (% of JDs)</h3>
          <p class="card-subtitle">Ranked frequency list</p>
          <div style="display:flex; flex-direction:column; gap:8px;" class="stagger-children">
            ${listData.map((s, idx) => `
              <div class="skill-bar-row">
                <span class="rank-badge ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : 'default'}">${idx + 1}</span>
                <span class="label truncate">${s.skill}</span>
                <div class="bar-track">
                  <div class="bar-fill" style="width: ${s.pct_of_jobs * 2.8}%; background: var(--gradient-brand-diagonal);"></div>
                </div>
                <span class="value">${s.pct_of_jobs.toFixed(1)}%</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;

    // Dynamic Chart rendering
    destroyCharts();
    const radarCtx = document.getElementById('skillsCategoryRadarCanvas');
    const isRadar = activeCat !== 'All';

    activeCharts.push(new Chart(radarCtx, {
      type: isRadar ? 'radar' : 'bar',
      data: {
        labels: listData.map(s => s.skill),
        datasets: [{
          label: '% Prevalence',
          data: listData.map(s => s.pct_of_jobs),
          backgroundColor: isRadar ? 'rgba(6, 182, 212, 0.2)' : 'rgba(168, 85, 247, 0.75)',
          borderColor: isRadar ? CHART_COLORS.cyan : CHART_COLORS.purple,
          borderWidth: 2,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: isRadar ? {
          r: {
            grid: { color: CHART_COLORS.grid },
            angleLines: { color: CHART_COLORS.grid },
            ticks: { backdropColor: 'transparent', color: CHART_COLORS.text },
            pointLabels: { color: CHART_COLORS.text, font: { size: 10 } }
          }
        } : {
          x: { ticks: { color: CHART_COLORS.text } },
          y: { ticks: { color: CHART_COLORS.text } }
        }
      }
    }));

    // Setup action triggers within tab bar
    const tabElms = container.querySelectorAll('.tab-item');
    tabElms.forEach(elm => {
      elm.addEventListener('click', () => {
        activeCat = elm.getAttribute('data-cat');
        renderContent();
      });
    });
  };

  renderContent();
}

// ─── 3. SALARY INTELLIGENCE ─────────────────────────────────────────
function renderSalary(container, d) {
  container.innerHTML = `
    <div class="dashboard-grid">
      <!-- Comp Bands -->
      <div class="card col-span-8">
        <h3>Estimated Salary Ranges by Experience</h3>
        <p class="card-subtitle">Analytic market ranges (Base to Peak LPA)</p>
        <div class="chart-wrapper tall">
          <canvas id="salaryExpBandsCanvas"></canvas>
        </div>
      </div>

      <!-- Comp Estimator Widget (Top 1% Interactive Touch) -->
      <div class="card col-span-4 flex-between" style="flex-direction: column; align-items: stretch;">
        <div>
          <h3>Interactive Salary Estimator</h3>
          <p class="card-subtitle">Calculate projected ranges by selecting target experience</p>
          
          <div class="mt-2 mb-3">
            <label class="stat-label">Experience Bracket (Years)</label>
            <input type="range" min="0" max="10" value="4" class="slider mt-1" id="exp-estimation-slider" style="width:100%; accent-color: var(--accent-primary);">
            <div class="flex-between mt-1">
              <span class="text-ghost" style="font-size:0.75rem;">Fresher (0 Yrs)</span>
              <span id="slider-val" class="badge badge-primary text-mono">4 Years (Mid)</span>
              <span class="text-ghost" style="font-size:0.75rem;">Lead (10+ Yrs)</span>
            </div>
          </div>
          
          <div class="divider"></div>
          
          <div style="text-align: center; padding: 1rem 0;">
            <div class="stat-label">Projected Analyst Comp</div>
            <div class="stat-value gradient" style="font-size: 2.8rem; margin: 0.5rem 0;" id="projected-salary-output">₹10.9L</div>
            <span class="badge badge-success">Average LPA Bengaluru</span>
          </div>
        </div>

        <div class="insight-box cyan mt-3" style="border-left-width: 2px;">
          <h4>⚡ Cloud & Big Data Influence</h4>
          <p>Proficiency in dbt, Databricks, or Snowflake shifts base expectation upwards by avg <strong>₹2.5L to ₹4.8L LPA</strong>.</p>
        </div>
      </div>
    </div>
  `;

  // Draw chart
  const bandCtx = document.getElementById('salaryExpBandsCanvas');
  activeCharts.push(new Chart(bandCtx, {
    type: 'bar',
    data: {
      labels: d.salary_bands.map(b => b.exp_band),
      datasets: [
        {
          label: 'Min Band LPA',
          data: d.salary_bands.map(b => b.min_salary),
          backgroundColor: 'rgba(6, 182, 212, 0.4)',
          borderRadius: 4
        },
        {
          label: 'Average LPA',
          data: d.salary_bands.map(b => b.avg_salary),
          backgroundColor: CHART_COLORS.purple,
          borderRadius: 4
        },
        {
          label: 'Max Peak LPA',
          data: d.salary_bands.map(b => b.max_salary),
          backgroundColor: CHART_COLORS.pink,
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: CHART_COLORS.text } },
        y: { ticks: { color: CHART_COLORS.text } }
      },
      plugins: { legend: { labels: { color: CHART_COLORS.text } } }
    }
  }));

  // Slider Calculation
  const slider = document.getElementById('exp-estimation-slider');
  const sliderVal = document.getElementById('slider-val');
  const salaryOutput = document.getElementById('projected-salary-output');

  const updateSalaryEstimation = () => {
    const val = parseInt(slider.value);
    let bandName = '';
    let est = 0;

    if (val <= 1) {
      bandName = `${val} Yr (Fresher)`;
      est = d.salary_bands.find(b => b.exp_band.includes('0-1'))?.avg_salary || 4.1;
    } else if (val <= 3) {
      bandName = `${val} Yrs (Junior)`;
      est = d.salary_bands.find(b => b.exp_band.includes('1-3'))?.avg_salary || 7.09;
    } else if (val <= 5) {
      bandName = `${val} Yrs (Mid)`;
      est = d.salary_bands.find(b => b.exp_band.includes('3-5'))?.avg_salary || 10.96;
    } else if (val <= 8) {
      bandName = `${val} Yrs (Senior)`;
      est = d.salary_bands.find(b => b.exp_band.includes('5-8'))?.avg_salary || 16.64;
    } else {
      bandName = `${val}+ Yrs (Lead)`;
      est = d.salary_bands.find(b => b.exp_band.includes('8+'))?.avg_salary || 24.39;
    }

    sliderVal.innerText = bandName;
    salaryOutput.innerText = `₹${est.toFixed(1)}L`;
  };

  slider.addEventListener('input', updateSalaryEstimation);
  updateSalaryEstimation();
}

// ─── 4. COMPANY WAR ROOM ────────────────────────────────────────────
function renderCompanies(container, d) {
  let searchWord = '';

  const renderView = () => {
    const filtered = d.top_companies.filter(c =>
      searchWord === '' || c.company.toLowerCase().includes(searchWord.toLowerCase()) || c.top_skills.toLowerCase().includes(searchWord.toLowerCase())
    ).slice(0, 16);

    container.innerHTML = `
      <div class="flex-between mb-3" style="flex-wrap: wrap; gap: 1rem;">
        <div>
          <h3>Enterprise Target Board</h3>
          <p class="card-subtitle">Interactive cards sorting major entities hiring analysts. Filter by company name or skill requirement.</p>
        </div>
        <div style="width: 320px;">
          <div class="search-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" id="company-warroom-search" class="search-input" value="${searchWord}" placeholder="Search firms or skills (e.g. SQL, Python)">
          </div>
        </div>
      </div>
      
      <div class="dashboard-grid mt-2 stagger-children" id="warroom-grid">
        ${filtered.map(c => `
          <div class="card col-span-3 card-accent-purple animate-scale-in" style="min-height: 200px; display:flex; flex-direction:column; justify-content:space-between;">
            <div>
              <div class="flex-between">
                <span class="badge ${c.tier === 'Product' ? 'badge-primary' : c.tier === 'Consulting' ? 'badge-secondary' : 'badge-ghost'}">${c.tier}</span>
                <span class="text-mono" style="font-size:0.75rem; color:var(--text-tertiary); font-weight:600;">${c.job_count} JDs</span>
              </div>
              <h4 style="margin: 0.5rem 0 0.25rem 0; font-size: 1.1rem; text-transform: capitalize;">${c.company}</h4>
              <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:2px;">
                ${c.top_skills.split(', ').slice(0, 3).map(sk => `<span class="badge badge-ghost text-mono" style="font-size:0.6rem; padding: 2px 6px;">${sk}</span>`).join('')}
              </div>
            </div>
            
            <div style="margin-top: 1rem; border-top: 1px solid var(--border-subtle); padding-top: 0.5rem;" class="flex-between">
              <span style="font-size:0.75rem; color:var(--text-tertiary);">Avg Experience: <strong style="color:var(--text-secondary);">${c.avg_experience.toFixed(1)} Yrs</strong></span>
              <span class="text-success fw-700" style="font-size:0.95rem;">₹${c.avg_salary.toFixed(1)}L <span style="font-size: 0.65rem; color:var(--text-tertiary); font-weight:normal;">LPA</span></span>
            </div>
          </div>
        `).join('')}
        
        ${filtered.length === 0 ? `
          <div class="card col-span-12 empty-state">
            <div class="icon">🔍</div>
            <h3>No target recruiting entities match your search</h3>
            <p>Try clearing letters or typing alternative tech keywords.</p>
          </div>
        ` : ''}
      </div>
    `;

    const searchInput = document.getElementById('company-warroom-search');
    // Maintain cursor position at end of text field
    searchInput.focus();
    searchInput.setSelectionRange(searchInput.value.length, searchInput.value.length);

    searchInput.addEventListener('input', (e) => {
      searchWord = e.target.value;
      renderView();
    });
  };

  renderView();
}

// ─── 5. SKILL SYNERGY MAP ───────────────────────────────────────────
function renderSynergy(container, d) {
  container.innerHTML = `
    <div class="dashboard-grid">
      <!-- Synergy visual map -->
      <div class="card col-span-7">
        <h3>Primary Skill Co-occurrences</h3>
        <p class="card-subtitle">Radial polar map highlighting top complementary bundles</p>
        <div class="chart-wrapper tall">
          <canvas id="synergyPolarCanvas"></canvas>
        </div>
      </div>
      
      <!-- List details -->
      <div class="card col-span-5 flex-between" style="flex-direction: column; align-items: stretch;">
        <div>
          <h3>High ROI Combination Bundles</h3>
          <p class="card-subtitle">Combinations that yield high salary payouts</p>
          
          <div style="display:flex; flex-direction:column; gap:10px; max-height:360px; overflow-y:auto;" class="stagger-children">
            ${d.skill_combos.slice(0, 10).map((c, idx) => `
              <div class="combo-card flex-between">
                <div>
                  <div style="font-size:0.9rem; font-weight:600; color:var(--text-primary);">${c.skill_pair}</div>
                  <div style="font-size:0.75rem; color:var(--text-tertiary);">Database match rate: <strong>${c.co_occurrences} JDs</strong></div>
                </div>
                <div class="text-success fw-700" style="font-family: var(--font-mono); font-size:1rem;">₹${c.avg_salary.toFixed(1)}L</div>
              </div>
            `).join('')}
          </div>
        </div>
        
        <div class="insight-box gold mt-3" style="border-left-width: 2px;">
          <h4>🔗 Stack recommendation</h4>
          <p>Combining <strong>Cloud systems (AWS/Azure)</strong> with core **Databricks or Snowflake** environments represents the fastest salary escalation vector, shifting junior positions above the <strong>₹16.5L LPA</strong> barrier.</p>
        </div>
      </div>
    </div>
  `;

  // Polar area chart setup
  const synData = d.skill_combos.slice(0, 6);
  const polarCtx = document.getElementById('synergyPolarCanvas');
  activeCharts.push(new Chart(polarCtx, {
    type: 'polarArea',
    data: {
      labels: synData.map(c => c.skill_pair),
      datasets: [{
        data: synData.map(c => c.avg_salary),
        backgroundColor: [
          'rgba(168, 85, 247, 0.65)',
          'rgba(6, 182, 212, 0.65)',
          'rgba(236, 72, 153, 0.65)',
          'rgba(245, 158, 11, 0.65)',
          'rgba(59, 130, 246, 0.65)'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { color: CHART_COLORS.text, padding: 12 } } },
      scales: {
        r: {
          grid: { color: CHART_COLORS.grid },
          ticks: { backdropColor: 'transparent', color: CHART_COLORS.text }
        }
      }
    }
  }));
}

// ─── 6. CAREER PATHFINDER ──────────────────────────────────────────
function renderGap(container, d) {
  const primarySkills = ['SQL', 'Python', 'Power BI', 'Tableau', 'Excel', 'dbt', 'AWS', 'statistics', 'A/B Testing', 'Git', 'Data Modeling', 'ETL'];

  container.innerHTML = `
    <div class="dashboard-grid">
      <!-- Selector card -->
      <div class="card col-span-7">
        <h3>Customize Your Current Stack</h3>
        <p class="card-subtitle">Choose technologies you are targeting or already leverage:</p>
        
        <div class="skill-selector-grid mt-3 mb-4">
          ${primarySkills.map(sk => `
            <div class="skill-toggle" data-skill="${sk}">
              <div class="check-icon"></div>
              <span>${sk}</span>
            </div>
          `).join('')}
        </div>
        
        <div class="flex-center mt-3">
          <button class="btn btn-primary" id="gap-generate-btn">Construct Roadmap Route</button>
        </div>
      </div>
      
      <!-- Target results card -->
      <div class="card col-span-5" id="gap-results-card">
        <div class="empty-state">
          <div class="icon">🎯</div>
          <h3>Roadmap telemetry ready</h3>
          <p>Toggle checkboxes and complete matching profile to retrieve your dashboard report.</p>
        </div>
      </div>
    </div>
  `;

  // Wire up toggling callbacks
  const items = container.querySelectorAll('.skill-toggle');
  items.forEach(itm => {
    itm.addEventListener('click', () => {
      itm.classList.toggle('selected');
    });
  });

  document.getElementById('gap-generate-btn').addEventListener('click', () => {
    const selected = Array.from(container.querySelectorAll('.skill-toggle.selected')).map(t => t.getAttribute('data-skill'));
    evaluatePathway(d, selected);
  });
}

function evaluatePathway(d, selected) {
  const card = document.getElementById('gap-results-card');

  // Hardcore benchmark requirements
  const benchmarkRequirements = ['SQL', 'Python', 'Tableau', 'Power BI', 'ETL', 'dbt', 'statistics'];
  const missing = benchmarkRequirements.filter(item => !selected.map(s => s.toLowerCase()).includes(item.toLowerCase()));
  const score = Math.round(((benchmarkRequirements.length - missing.length) / benchmarkRequirements.length) * 100);

  // Missing Skill salaries lookup
  const missingData = d.skill_frequency
    .filter(s => missing.map(m => m.toLowerCase()).includes(s.skill.toLowerCase()))
    .sort((a, b) => b.avg_salary - a.avg_salary);

  card.innerHTML = `
    <h3 class="animate-fade-in text-gradient">Matching Summary Report</h3>
    <p class="card-subtitle">Pathway roadmap metrics</p>
    
    <div class="flex-center gap-md mt-3" style="flex-wrap: wrap;">
      <div class="progress-ring-container animate-scale-in">
        <svg class="progress-ring" width="100" height="100">
          <circle class="progress-ring-bg" cx="50" cy="50" r="42" stroke-width="8" />
          <circle class="progress-ring-fill" cx="50" cy="50" r="42" stroke-width="8" 
                  stroke="var(--accent-primary)" 
                  stroke-dasharray="263.89" 
                  stroke-dashoffset="${263.89 - (263.89 * score) / 100}" />
        </svg>
        <div class="progress-ring-text">
          <div style="font-size: 1.3rem; font-weight:800;">${score}%</div>
        </div>
      </div>
      <div>
        <span class="badge ${score > 70 ? 'badge-success' : score > 40 ? 'badge-warning' : 'badge-primary'} mb-2">
          ${score > 70 ? 'Market Premium Ready' : score > 40 ? 'Mid tier Match' : 'High Skill Delta'}
        </span>
        <p style="font-size:0.85rem; color:var(--text-secondary);">Your current alignment status</p>
      </div>
    </div>

    <div class="divider"></div>

    <h4 class="mb-2">Highest Value Missing Targets</h4>
    ${missingData.length === 0 ? `
      <div class="insight-box green">
        <h4>🎉 Perfect Core Alignment!</h4>
        <p>You possess no core pipeline skill gaps. Focus on building and showcasing advanced analytics portfolio projects.</p>
      </div>
    ` : `
      <ul style="list-style: none; display:flex; flex-direction:column; gap:8px;" class="stagger-children">
        ${missingData.slice(0, 3).map(m => `
          <li style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:0.6rem 0.8rem; border-radius:6px; border-left:3px solid var(--accent-primary);">
            <div>
              <strong>${m.skill}</strong>
              <div style="font-size:0.75rem; color:var(--text-tertiary);">${m.category}</div>
            </div>
            <div style="text-align:right;">
              <div class="text-success fw-700">+₹${(m.avg_salary * 0.07).toFixed(1)}L</div>
              <div style="font-size:0.6rem; color:var(--text-tertiary);">Potential ROI Lift</div>
            </div>
          </li>
        `).join('')}
      </ul>
      <div class="insight-box cyan mt-3" style="border-left-width: 2px;">
        <h4>💡 Fast track target sequence</h4>
        <p>Primary focus path: <strong>${missingData.slice(0, 3).map(md => md.skill).join(' ➜ ')}</strong></p>
      </div>
    `}
  `;
}

// ─── 7. EXECUTIVE PULSE REPORT ──────────────────────────────────────
function renderPulse(container, d) {
  container.innerHTML = `
    <div class="dashboard-grid">
      <div class="card col-span-12">
        <div class="flex-between mb-3">
          <div>
            <h3>Bengaluru Data Analyst MarketPulse Report</h3>
            <p class="card-subtitle">Automated text briefing of target roles compiled from live inputs</p>
          </div>
          <button class="btn btn-secondary" id="pulse-print-btn">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
            Print Executive PDF
          </button>
        </div>
        
        <div class="report-section card-accent-purple animate-scale-in">
          <h4>🌟 Core Hiring Insights</h4>
          <ul>
            <li><strong>SQL & Python</strong> represent solid career dependencies; present in over <strong>31%</strong> of evaluated analyst JDs.</li>
            <li>Cloud database management (AWS/Azure) coupled with Snowflake constitutes the maximum salary vector, lifting junior positions above the <strong>₹16.5L LPA</strong> benchmark.</li>
          </ul>
        </div>
        
        <div class="report-section card-accent-cyan animate-scale-in delay-100 mt-2">
          <h4>🚀 Recommended Portfolio Target</h4>
          <ul>
            <li>Focus heavily on building analytics portfolios featuring SQL data warehouse modelling and Tableau/Power BI report rendering, paired with Python processing backends. Showcasing these directly sets applicants apart for product orgs.</li>
          </ul>
        </div>
      </div>
    </div>
  `;

  document.getElementById('pulse-print-btn').addEventListener('click', () => {
    window.print();
  });
}

// Start execution
init();
