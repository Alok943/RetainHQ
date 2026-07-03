import {
  Map, Binary, Database, Server, CircuitBoard, ScatterChart,
  Layers, AppWindow, Cpu, Calculator, Handshake, CloudCog, Terminal, Network
} from 'lucide-react';
import { siPython, siLeetcode, siCplusplus, siGit, siLinux } from 'simple-icons';

// Custom icons for brands not in simple-icons or requiring specific viewboxes
const siNeetcode = {
  title: 'NeetCode',
  viewBox: '0 0 24 24',
  paths: ['M4 4h4.5l7 10V4h4.5v16h-4.5l-7-10v10H4V4z'] // Clean stylized N
};

const siJava = {
  title: 'Java',
  viewBox: '0 0 128 128',
  paths: [
    "M47.617 98.12s-4.767 2.774 3.397 3.71c9.892 1.13 14.947.968 25.845-1.092 0 0 2.871 1.795 6.873 3.351-24.439 10.47-55.308-.607-36.115-5.969zm-2.988-13.665s-5.348 3.959 2.823 4.805c10.567 1.091 18.91 1.18 33.354-1.6 0 0 1.993 2.025 5.132 3.131-29.542 8.64-62.446.68-41.309-6.336z",
    "M69.802 61.271c6.025 6.935-1.58 13.17-1.58 13.17s15.289-7.891 8.269-17.777c-6.559-9.215-11.587-13.792 15.635-29.58 0 .001-42.731 10.67-22.324 34.187z",
    "M102.123 108.229s3.529 2.91-3.888 5.159c-14.102 4.272-58.706 5.56-71.094.171-4.451-1.938 3.899-4.625 6.526-5.192 2.739-.593 4.303-.485 4.303-.485-4.953-3.487-32.013 6.85-13.743 9.815 49.821 8.076 90.817-3.637 77.896-9.468zM49.912 70.294s-22.686 5.389-8.033 7.348c6.188.828 18.518.638 30.011-.326 9.39-.789 18.813-2.474 18.813-2.474s-3.308 1.419-5.704 3.053c-23.042 6.061-67.544 3.238-54.731-2.958 10.832-5.239 19.644-4.643 19.644-4.643zm40.697 22.747c23.421-12.167 12.591-23.86 5.032-22.285-1.848.385-2.677.72-2.677.72s.688-1.079 2-1.543c14.953-5.255 26.451 15.503-4.823 23.725 0-.002.359-.327.468-.617z",
    "M76.491 1.587S89.459 14.563 64.188 34.51c-20.266 16.006-4.621 25.13-.007 35.559-11.831-10.673-20.509-20.07-14.688-28.815C58.041 28.42 81.722 22.195 76.491 1.587z",
    "M52.214 126.021c22.476 1.437 57-.8 57.817-11.436 0 0-1.571 4.032-18.577 7.231-19.186 3.612-42.854 3.191-56.887.874 0 .001 2.875 2.381 17.647 3.331z"
  ]
};

// Per-roadmap visual identity (themed glyph + accent), matched by title keyword.
export const STYLE_RULES = [
  // DSA variants
  { match: ['neetcode'], Icon: Binary, accent: '#7C3AED' },
  { match: ['striver'], Icon: Binary, accent: '#7C3AED' },
  { match: ['leetcode'], Icon: Binary, accent: '#7C3AED' },
  { match: ['blind', 'patterns'], Icon: Network, accent: '#7C3AED' },
  { match: ['visualize', 'algorithms visualized'], Icon: Network, accent: '#7C3AED' },
  { match: ['dsa', 'algorithm', 'data structure'], Icon: Binary, accent: '#7C3AED' },

  // Engineering Disciplines
  { match: ['system design'], Icon: Server, accent: '#0F766E' },
  { match: ['sql', 'database'], Icon: Database, accent: '#4F46E5' },
  { match: ['machine learning'], Icon: ScatterChart, accent: '#C026D3' },
  { match: ['deep learning'], Icon: Layers, accent: '#C026D3' },
  { match: ['ai eng', 'llm', 'rag', 'agent'], Icon: CircuitBoard, accent: '#C026D3' },
  
  // Software Engineering
  { match: ['devops', 'cloud'], Icon: CloudCog, accent: '#0F766E' },
  { match: ['python backend', 'backend'], Icon: Server, accent: '#059669' },
  { match: ['web'], Icon: AppWindow, accent: '#0891B2' },
  
  // Languages & Tools
  { match: ['python'], Icon: Server, accent: '#2563EB' },
  { match: ['java'], Icon: Server, accent: '#B45309' },
  { match: ['c++'], Icon: Server, accent: '#2563EB' },
  { match: ['git', 'github'], Icon: Network, accent: '#475569' },
  { match: ['linux', 'shell'], Icon: Terminal, accent: '#475569' },
  
  // Core / Behavioral
  { match: ['core cs', 'operating system', 'dbms', 'network'], Icon: Cpu, accent: '#475569' },
  { match: ['aptitude', 'quant', 'reasoning'], Icon: Calculator, accent: '#B45309' },
  { match: ['behavioral', 'hr', 'interview'], Icon: Handshake, accent: '#B45309' },
];

export function getRoadmapStyle(title = '') {
  const t = title.toLowerCase();
  for (const rule of STYLE_RULES) {
    if (rule.match.some((m) => t.includes(m))) return rule;
  }
  return { Icon: Map, accent: '#0891B2' };
}

// Official brand logos for courses centered around a brand, language, or tool.
const BRAND_LOGOS = [
  { match: ['python'], icon: siPython },
  { match: ['java'], icon: siJava },
  { match: ['c++'], icon: siCplusplus },
  { match: ['neetcode'], icon: siNeetcode },
  { match: ['leetcode'], icon: siLeetcode },
  { match: ['git'], icon: siGit },
  { match: ['linux'], icon: siLinux },
];

function brandLogo(title = '') {
  const t = title.toLowerCase();
  for (const b of BRAND_LOGOS) {
    if (b.match.some((m) => t.includes(m))) return b.icon;
  }
  return null;
}

// Render official brand logo if matched, otherwise fallback to the conceptual Lucide icon.
// All icons inherit the cohesive accent color of their track.
export function RoadmapLogo({ title, Icon, accent, size = 22 }) {
  const logo = brandLogo(title);
  if (logo) {
    const vBox = logo.viewBox || "0 0 24 24";
    return (
      <svg role="img" aria-label={logo.title} viewBox={vBox}
        width={size} height={size} fill={accent}>
        {logo.paths ? (
          logo.paths.map((p, i) => <path key={i} d={p} />)
        ) : (
          <path d={logo.path} />
        )}
      </svg>
    );
  }
  return <Icon size={size} color={accent} strokeWidth={2} />;
}
