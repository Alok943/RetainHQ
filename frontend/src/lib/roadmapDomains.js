export const DOMAINS = {
  'placement-prep': {
    title: 'Placement Prep',
    emoji: '🎯',
    blurb: 'The Round-1 gate for every role — SDE, Backend, even GenAI.',
    order: 1,
  },
  'software-engineering': {
    title: 'Software Engineering',
    emoji: '💼',
    blurb: 'Production skills that launch the GenAI pathway, plus full-stack foundations.',
    order: 2,
  },
  'ai-data': {
    title: 'AI & Data',
    emoji: '🤖',
    blurb: 'The highest-ROI transitions in 2026, from Data Engineering to LLMs.',
    order: 3,
  },
  'btech-core': {
    title: 'B.Tech Core',
    emoji: '🎓',
    blurb: 'OS, DBMS, networks + core math — the shared base under every engineering track.',
    order: 4,
    isDefault: true,
  }
};

export const ROADMAP_REGISTRY = {
  // Placement Prep
  'dsa': { domain: 'placement-prep', flagship: true },
  'striver-a2z': { domain: 'placement-prep' },
  'neetcode-150': { domain: 'placement-prep' },
  'blind-75': { domain: 'placement-prep' },
  'aptitude': { domain: 'placement-prep', flagship: true },
  'system-design': { domain: 'placement-prep' },
  'lld': { domain: 'placement-prep' },
  'behavioral': { domain: 'placement-prep' },

  // Software Engineering
  'python-swe': { domain: 'software-engineering', flagship: true },
  'web-dev': { domain: 'software-engineering' },
  'python-backend': { domain: 'software-engineering' },
  'sql': { domain: 'software-engineering', flagship: true },
  'git-github': { domain: 'software-engineering' },
  'linux-shell': { domain: 'software-engineering' },
  'devops-cloud': { domain: 'software-engineering' },
  'java-swe': { domain: 'software-engineering' },
  'cpp-swe': { domain: 'software-engineering' },
  'testing': { domain: 'software-engineering' },
  'cyber-security': { domain: 'software-engineering' },
  'api-design': { domain: 'software-engineering' },

  // AI & Data
  'ai-engineering': { domain: 'ai-data', flagship: true },
  'machine-learning': { domain: 'ai-data' },
  'deep-learning': { domain: 'ai-data' },
  'data-engineering': { domain: 'ai-data' },
  'mlops': { domain: 'ai-data' },
  'math-ml': { domain: 'ai-data' },

  // B.Tech Core
  'core-cs': { domain: 'btech-core', flagship: true },
  'discrete-math': { domain: 'btech-core' },
  'computer-architecture': { domain: 'btech-core' },
};

export function getRoadmapMeta(slug) {
  const meta = ROADMAP_REGISTRY[slug] || { domain: 'btech-core' };
  const domainInfo = DOMAINS[meta.domain];
  return { ...meta, domainInfo };
}
