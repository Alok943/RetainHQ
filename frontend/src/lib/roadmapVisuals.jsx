import {
  Map, Binary, Database, Globe, Server, BrainCircuit, Code2, Cpu, Calculator,
} from 'lucide-react';
import { siPython, siLeetcode, siHtml5, siPostgresql } from 'simple-icons';

// Per-roadmap visual identity (themed glyph + accent), matched by title keyword.
// Shared by the roadmap list cards and the roadmap detail header.
export const STYLE_RULES = [
  { match: ['neetcode', 'striver', 'dsa', 'algorithm', 'data structure'], Icon: Binary, accent: '#7C3AED' },
  { match: ['sql'], Icon: Database, accent: '#4F46E5' },
  { match: ['web'], Icon: Globe, accent: '#0891B2' },
  { match: ['system design'], Icon: Server, accent: '#0F766E' },
  { match: ['ai eng', 'machine learning', 'deep learning'], Icon: BrainCircuit, accent: '#C026D3' },
  { match: ['backend'], Icon: Server, accent: '#059669' },
  { match: ['python'], Icon: Code2, accent: '#2563EB' },
  { match: ['core cs', 'operating system', 'dbms', 'network'], Icon: Cpu, accent: '#475569' },
  { match: ['aptitude', 'quant', 'reasoning'], Icon: Calculator, accent: '#B45309' },
];

export function getRoadmapStyle(title = '') {
  const t = title.toLowerCase();
  for (const rule of STYLE_RULES) {
    if (rule.match.some((m) => t.includes(m))) return rule;
  }
  return { Icon: Map, accent: '#0891B2' };
}

// Official brand logos (Simple Icons, bundled — no network dependency) for the
// roadmaps that map to a real brand. Concept roadmaps (DSA/Striver, System Design,
// Core CS, Aptitude, AI Eng) have no official mark — they fall back to the themed
// lucide glyph from STYLE_RULES.
const BRAND_LOGOS = [
  { match: ['python'], icon: siPython },     // Python for SWE, Python Backend
  { match: ['neetcode'], icon: siLeetcode }, // NeetCode 150 = LeetCode problems
  { match: ['web'], icon: siHtml5 },         // Web Dev → the universal web mark
  { match: ['sql'], icon: siPostgresql },    // SQL → Postgres, the engine the lessons run on (PGlite)
];

function brandLogo(title = '') {
  const t = title.toLowerCase();
  for (const b of BRAND_LOGOS) {
    if (b.match.some((m) => t.includes(m))) return b.icon;
  }
  return null;
}

// Official brand-colored logo where one exists, else the themed glyph.
export function RoadmapLogo({ title, Icon, accent, size = 22 }) {
  const logo = brandLogo(title);
  if (logo) {
    return (
      <svg role="img" aria-label={logo.title} viewBox="0 0 24 24"
        width={size} height={size} fill={`#${logo.hex}`}>
        <path d={logo.path} />
      </svg>
    );
  }
  return <Icon size={size} style={{ color: accent }} />;
}
