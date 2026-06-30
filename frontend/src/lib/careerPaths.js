// Career-path data — the 10 role transitions from JD Research Run 3 (docs/jd-research-run3.md).
// Pure reference data (no backend): timeline / ROI / blocker / skill-delta per transition, plus the
// RetainHQ roadmaps that build each one. A roadmap ref is matched against the live roadmap list by
// `match` (substring of the lowercased title); refs that don't resolve render as "coming soon".

export const ROLES = [
  'SDE',
  'Backend Engineer',
  'Data Analyst',
  'Data Scientist',
  'ML Engineer',
  'Data Engineer',
];

// status: 'common' (well-trodden) | 'possible' (open but harder)
export const CAREER_PATHS = [
  {
    id: 'sde-backend',
    from: 'SDE', to: 'Backend Engineer', status: 'common', timeline: '1–3 months',
    roi: 'Near friction-free — mostly a title + depth clarification; roles overlap heavily.',
    blocker: 'Almost none. Go deeper on distributed systems, DB internals and API design.',
    skillDelta: ['System design depth', 'Distributed systems', 'DB internals', 'API design patterns', 'Observability'],
    roadmaps: [
      { match: 'system design', label: 'System Design' },
      { match: 'backend', label: 'Python Backend' },
      { match: 'sql', label: 'SQL' },
      { match: 'core cs', label: 'Core CS' },
    ],
  },
  {
    id: 'backend-genai',
    from: 'Backend Engineer', to: 'GenAI / LLM Engineer', status: 'common', timeline: '6–12 months',
    roi: 'The #1 ROI move in 2026 — "the largest single pathway in GCC AI hiring today" (Zinnov). Your production skills are the edge data-side candidates lack.',
    blocker: 'The DSA round still gates product-co pipelines; portfolio must be deployed + original.',
    skillDelta: ['Foundation-model APIs', 'RAG pipelines', 'Vector DBs', 'LangChain / orchestration', 'Prompt engineering'],
    roadmaps: [
      { match: 'ai engineering', label: 'AI Engineering' },
      { match: 'dsa', label: 'DSA', note: 'the interview gate' },
    ],
  },
  {
    id: 'sde-genai',
    from: 'SDE', to: 'GenAI / LLM Engineer', status: 'possible', timeline: '6–12 months',
    roi: 'Strong demand; production tooling (Docker, CI/CD, REST) transfers directly.',
    blocker: 'DSA-round gatekeeping at product cos (Razorpay/Zomato/PhonePe) filters before AI work is seen. GCC applications bypass it most reliably.',
    skillDelta: ['Foundation-model APIs', 'RAG / LangChain / LlamaIndex', 'Vector DBs', 'Prompt engineering', 'LLMOps'],
    roadmaps: [
      { match: 'ai engineering', label: 'AI Engineering' },
      { match: 'dsa', label: 'DSA', note: 'the interview gate' },
    ],
  },
  {
    id: 'sde-mle',
    from: 'SDE', to: 'ML Engineer', status: 'possible', timeline: '6–12 months',
    roi: 'Open pathway, but a harder math lift than the GenAI route.',
    blocker: 'Math gap; no ML work at the current company; DSA gatekeeping at product cos.',
    skillDelta: ['Statistics / linear algebra', 'ML algorithms', 'Python ML stack (scikit-learn / PyTorch)', 'Model evaluation', 'MLOps basics'],
    roadmaps: [
      { match: 'dsa', label: 'DSA', note: 'the interview gate' },
      { match: 'python for', label: 'Python' },
      { match: '__ml__', label: 'ML Fundamentals' },
    ],
  },
  {
    id: 'da-de',
    from: 'Data Analyst', to: 'Data Engineer', status: 'common', timeline: '3–5 months (focused)',
    roi: 'Underrated + faster than DA→DS. 230k+ open roles; SQL — your natural strength — is the #1 DE filter.',
    blocker: 'SQL depth is the first-round filter (200-line production queries, not textbook). Skipping Airflow/Docker fails the technical screen.',
    skillDelta: ['Production Python ETL', 'Apache Airflow', 'Data-warehouse modeling (star/snowflake)', 'One cloud deep (S3/BigQuery/Redshift)', 'dbt'],
    roadmaps: [
      { match: 'sql', label: 'SQL', note: 'the #1 DE filter' },
      { match: 'backend', label: 'Python Backend' },
      { match: '__de__', label: 'Data Engineering' },
    ],
  },
  {
    id: 'da-ds',
    from: 'Data Analyst', to: 'Data Scientist', status: 'common', timeline: '9–12 months',
    roi: 'The most-trodden DA path: SQL + business intuition transfer directly.',
    blocker: 'Weak portfolio; generic DA profiles losing ground to specialized DS. Python-to-production + ML algorithms are the climb.',
    skillDelta: ['Python beyond notebooks (OOP, packaging, tests)', 'ML algorithms (scikit-learn/XGBoost)', 'Linear algebra', 'Model evaluation (AUC, PR)', '3–5 GitHub projects'],
    roadmaps: [
      { match: 'sql', label: 'SQL' },
      { match: 'python for', label: 'Python' },
      { match: '__ml__', label: 'ML Fundamentals' },
    ],
  },
  {
    id: 'ds-mle',
    from: 'Data Scientist', to: 'ML Engineer', status: 'common', timeline: '2–4 months',
    roi: 'The market is actively pushing this way — 28% of switching Indian DSes go MLE. The gap is pure engineering depth, not more theory.',
    blocker: 'Basic ML + Python no longer differentiates; must show LLM integration or model-serving-at-scale.',
    skillDelta: ['Production Python (packaged, tested)', 'Docker / Kubernetes basics', 'CI/CD for models', 'Cloud ML platforms (SageMaker/Vertex)', 'Model monitoring / retraining'],
    roadmaps: [
      { match: 'backend', label: 'Python Backend' },
      { match: 'system design', label: 'System Design' },
      { match: '__mlops__', label: 'MLOps' },
    ],
  },
  {
    id: 'mle-genai',
    from: 'ML Engineer', to: 'GenAI / LLM Engineer', status: 'possible', timeline: '3–6 months',
    roi: 'Adjacent move — the underlying engineering is similar.',
    blocker: 'GCCs treat classical-ML and LLM-integration as separate talent pools; needs explicit LLM project work in the portfolio, not just ML credentials.',
    skillDelta: ['LLM APIs (OpenAI/Anthropic/Groq)', 'RAG system design', 'Vector DBs', 'LangChain / orchestration', 'Fine-tuning basics'],
    roadmaps: [
      { match: 'ai engineering', label: 'AI Engineering' },
    ],
  },
  {
    id: 'de-mle',
    from: 'Data Engineer', to: 'ML Engineer', status: 'possible', timeline: '6–12 months',
    roi: 'The most structurally efficient unrecognized path — DEs already hold the production/cloud/orchestration depth most MLEs lack.',
    blocker: 'Pigeonholed in infrastructure; no ML project portfolio = hard to pass DS/MLE screens.',
    skillDelta: ['ML theory (supervised/unsupervised)', 'Statistics / probability', 'Feature engineering', 'Model training loops', 'ML project portfolio'],
    roadmaps: [
      { match: 'dsa', label: 'DSA', note: 'the interview gate' },
      { match: '__ml__', label: 'ML Fundamentals' },
    ],
  },
  {
    id: 'de-ds',
    from: 'Data Engineer', to: 'Data Scientist', status: 'possible', timeline: '6–18 months',
    roi: 'Feasible — you hold the engineering half already.',
    blocker: "DE's engineering-certainty mindset vs DS's research/ambiguity culture; DS roles under more market pressure than MLE.",
    skillDelta: ['ML fundamentals', 'Statistics depth', 'Feature engineering', 'Business framing of prediction problems', 'Ambiguity tolerance'],
    roadmaps: [
      { match: '__ml__', label: 'ML Fundamentals' },
    ],
  },
];
