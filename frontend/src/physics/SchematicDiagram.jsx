import React from 'react';

/**
 * SchematicDiagram — dependency-free labeled-vector SVG for the `physics` kind.
 *
 * The conceptual-illustration counterpart to RayDiagram/GraphDiagram: the class
 * of physics pictures that are just bodies + force arrows + labels — "the Earth
 * pulls the Moon", Newton's third-law action/reaction pair, buoyant thrust on a
 * submerged block, the force on a current-carrying conductor. On-brand structured
 * SVG (crisp, themeable, no raster "AI-slop" images) rather than a bitmap.
 *
 * Spec (diagram.type === "schematic"):
 *   {
 *     "type": "schematic",
 *     "bodies": [                       // normalized coords, 0..100 x, 0..60 y
 *       { "id": "earth", "x": 24, "y": 30, "r": 15, "label": "Earth", "color": "#2563EB" },
 *       { "id": "moon",  "x": 78, "y": 30, "r": 7,  "label": "Moon" }
 *     ],
 *     "arrows": [                        // force/interaction vectors
 *       { "from": "moon", "to": "earth", "label": "F", "style": "force" }
 *     ],
 *     "distance": { "from": "earth", "to": "moon", "label": "r" },  // optional bracket
 *     "caption": "The Earth pulls the Moon with a gravitational force F over a distance r."
 *   }
 *
 * `arrows[].style`: "force" (solid cyan, the default) | "reaction" (amber) |
 * "motion" (slate, dashed). An arrow may also be free-standing via explicit
 * from/to points {x,y} instead of a body id.
 */

const AXIS = '#94A3B8';
const INK = '#0F172A';
const MUTED = '#64748B';
const FORCE = '#0891B2';   // solid cyan — matches RayDiagram's REAL
const REACT = '#B45309';   // amber — matches RayDiagram's VIRT
const MOTION = '#334155';

const VBW = 520, VBH = 312;
const SX = VBW / 100, SY = VBH / 60;
const px = (x) => x * SX;
const py = (y) => y * SY;

const STYLE = {
  force: { color: FORCE, dash: undefined },
  reaction: { color: REACT, dash: undefined },
  motion: { color: MOTION, dash: '5 4' },
};

export default function SchematicDiagram({ diagram }) {
  const d = diagram || {};
  const bodies = Array.isArray(d.bodies) ? d.bodies : [];
  if (!bodies.length) return null;
  const byId = Object.fromEntries(bodies.map((b) => [b.id, b]));
  const arrows = Array.isArray(d.arrows) ? d.arrows : [];

  // Resolve an endpoint that is either a body id (edge of the circle, toward the
  // other end) or an explicit {x, y} point.
  const resolve = (end, other) => {
    if (end && typeof end === 'object' && end.x != null) return { x: end.x, y: end.y };
    const b = byId[end];
    if (!b) return null;
    if (!other) return { x: b.x, y: b.y };
    const o = (other && typeof other === 'object' && other.x != null) ? other : byId[other];
    if (!o) return { x: b.x, y: b.y };
    const dx = o.x - b.x, dy = o.y - b.y;
    const L = Math.hypot(dx, dy) || 1;
    const r = (b.r || 6) + 1.5;
    return { x: b.x + (dx / L) * r, y: b.y + (dy / L) * r };
  };

  return (
    <div className="rounded-lg border border-[rgba(15,23,42,0.12)] bg-white overflow-hidden">
      <svg viewBox={`0 0 ${VBW} ${VBH}`} className="w-full" style={{ maxHeight: 320 }}>
        <defs>
          {Object.entries(STYLE).map(([k, v]) => (
            <marker key={k} id={`sch-arr-${k}`} markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6 Z" fill={v.color} />
            </marker>
          ))}
        </defs>

        {/* optional distance bracket between two bodies */}
        {d.distance && <DistanceBracket dist={d.distance} byId={byId} />}

        {/* interaction / force arrows */}
        {arrows.map((a, i) => {
          const st = STYLE[a.style] || STYLE.force;
          const p1 = resolve(a.from, a.to);
          const p2 = resolve(a.to, a.from);
          if (!p1 || !p2) return null;
          const mx = (p1.x + p2.x) / 2, my = (p1.y + p2.y) / 2;
          return (
            <g key={i}>
              <line x1={px(p1.x)} y1={py(p1.y)} x2={px(p2.x)} y2={py(p2.y)}
                stroke={st.color} strokeWidth="2.4" strokeDasharray={st.dash}
                markerEnd={`url(#sch-arr-${a.style || 'force'})`} strokeLinecap="round" />
              {a.label && (
                <text x={px(mx)} y={py(my) - 6} textAnchor="middle" fontSize="13"
                  fontFamily="ui-sans-serif, system-ui" fontWeight="700" fill={st.color}>{a.label}</text>
              )}
            </g>
          );
        })}

        {/* bodies */}
        {bodies.map((b, i) => (
          <g key={b.id || i}>
            <circle cx={px(b.x)} cy={py(b.y)} r={px(b.r || 6)}
              fill={b.color || '#E2E8F0'} stroke={INK} strokeWidth="1.4" fillOpacity={b.color ? 0.85 : 1} />
            {b.label && (
              <text x={px(b.x)} y={py(b.y) + px(b.r || 6) + 15} textAnchor="middle" fontSize="12.5"
                fontFamily="ui-sans-serif, system-ui" fontWeight="600" fill={INK}>{b.label}</text>
            )}
          </g>
        ))}
      </svg>
      {d.caption && (
        <div className="px-3 py-2.5 border-t border-[rgba(15,23,42,0.06)] bg-[#f9f9f6]">
          <span className="font-sans text-[12.5px] text-[#0F172A] leading-snug">{d.caption}</span>
        </div>
      )}
    </div>
  );
}

function DistanceBracket({ dist, byId }) {
  const a = byId[dist.from], b = byId[dist.to];
  if (!a || !b) return null;
  const y = py(Math.max(a.y, b.y)) + px(Math.max(a.r || 6, b.r || 6)) + 26;
  const x1 = px(a.x), x2 = px(b.x);
  return (
    <g stroke={AXIS} strokeWidth="1.2" fill="none">
      <line x1={x1} y1={y - 4} x2={x1} y2={y + 4} />
      <line x1={x2} y1={y - 4} x2={x2} y2={y + 4} />
      <line x1={x1} y1={y} x2={x2} y2={y} strokeDasharray="3 3" />
      {dist.label && (
        <text x={(x1 + x2) / 2} y={y - 6} textAnchor="middle" fontSize="12" strokeWidth="0"
          fontFamily="ui-sans-serif, system-ui" fontStyle="italic" fill={MUTED}>{dist.label}</text>
      )}
    </g>
  );
}
