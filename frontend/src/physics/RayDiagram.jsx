import React from 'react';

/**
 * RayDiagram — dependency-free SVG ray diagram for the `physics` lesson kind.
 *
 * The physics is IN the renderer, not the content: the author supplies only the
 * scenario (optic + focal length + object distance/height) and this component
 * COMPUTES the image via the mirror/lens formula, then draws the two canonical
 * construction rays so their (real) intersection or (virtual) back-extension
 * lands exactly on the computed image tip. That guarantees every diagram is
 * physically correct and internally consistent — no hand-placed, possibly-wrong
 * ray coordinates in the JSON.
 *
 * Spec (diagram.type === "ray"):
 *   {
 *     "type": "ray",
 *     "optic": "concave-mirror" | "convex-mirror" | "convex-lens" | "concave-lens",
 *     "focal_length": 15,      // cm, MAGNITUDE (always positive)
 *     "object_distance": 25,   // cm, MAGNITUDE, object in front of the optic
 *     "object_height": 6,      // cm, MAGNITUDE (optional, default 6)
 *     "caption": "..."         // optional override; else auto-generated
 *   }
 *
 * Cartesian sign convention: optic at origin, incident light travels left→right,
 * distances left of the optic are negative, heights up are positive.
 */

const AXIS = '#94A3B8';
const OPTIC = '#334155';
const REAL = '#0891B2';   // real rays / real image — solid cyan
const VIRT = '#B45309';   // virtual rays / virtual image — dashed amber
const OBJECT = '#0F172A';
const INK = '#0F172A';

const OPTICS = {
  'concave-mirror': { lens: false, fSign: -1 }, // F in front (left)
  'convex-mirror':  { lens: false, fSign: +1 }, // F behind (right)
  'convex-lens':    { lens: true,  fSign: +1 },
  'concave-lens':   { lens: true,  fSign: -1 },
};

function solve(optic, F, objDist, objH) {
  const cfg = OPTICS[optic];
  if (!cfg) return null;
  const f = cfg.fSign * F;      // signed focal length
  const u = -Math.abs(objDist); // object always in front (left)
  // Mirror: 1/v + 1/u = 1/f  →  v = uf/(u - f)
  // Lens:   1/v - 1/u = 1/f  →  v = uf/(u + f)
  const denom = cfg.lens ? (u + f) : (u - f);
  const v = denom === 0 ? Infinity : (u * f) / denom;
  const m = cfg.lens ? (v / u) : (-v / u);
  const hi = m * objH;
  // Real image forms on the outgoing-light side: right (v>0) for a lens,
  // left (v<0, same side as object) for a mirror.
  const real = Number.isFinite(v) && (cfg.lens ? v > 0 : v < 0);
  return { cfg, f, u, v, m, objH, hi, real };
}

export default function RayDiagram({ diagram }) {
  const d = diagram || {};
  const F = Math.abs(Number(d.focal_length));
  const objDist = Math.abs(Number(d.object_distance));
  const objH = Math.abs(Number(d.object_height)) || 6;
  const s = solve(d.optic, F, objDist, objH);
  if (!s || !F || !objDist) return null;

  const { cfg, f, u, v, m, hi, real } = s;

  // --- world → SVG mapping -------------------------------------------------
  const VBW = 560, VBH = 280, OX = 280, AY = 150;
  const halfW = 232, maxH = 96;
  const finiteV = Number.isFinite(v) ? v : u; // image at infinity → don't let it blow up scale
  const spanX = Math.max(Math.abs(u), Math.abs(finiteV), 2 * F) * 1.18;
  const spanY = Math.max(objH, Math.abs(hi)) * 1.25 || 1;
  const sx = halfW / spanX;
  const sy = maxH / spanY;
  const sc = Math.min(sx, sy); // uniform scale so magnification reads true
  const X = (xc) => OX + xc * sc;
  const Y = (yc) => AY - yc * sc;

  const objTip = { x: u, y: objH };
  const imgTip = { x: finiteV, y: hi };

  // Two construction rays. Each: incident P→hit on optic, then outgoing whose
  // line passes through the image tip (real → forward, virtual → back-extension).
  const rays = [];
  // Ray A — parallel to axis, hits optic at the object's height.
  rays.push(buildRay({ x: 0, y: objH }, objTip, imgTip, real));
  // Ray B — through the pole/optical centre (0,0).
  rays.push(buildRay({ x: 0, y: 0 }, objTip, imgTip, real));

  const caption = d.caption || autoCaption(d.optic, s);

  return (
    <div className="rounded-lg border border-[rgba(15,23,42,0.12)] bg-white overflow-hidden">
      <svg viewBox={`0 0 ${VBW} ${VBH}`} className="w-full" style={{ maxHeight: 300 }}>
        {/* principal axis */}
        <line x1="16" y1={AY} x2={VBW - 16} y2={AY} stroke={AXIS} strokeWidth="1" />

        {/* optic */}
        {cfg.lens ? <Lens x={OX} ay={AY} converging={cfg.fSign > 0} />
                  : <Mirror x={OX} ay={AY} concave={cfg.fSign < 0} />}

        {/* F and 2F / C markers on the axis (both sides for a lens) */}
        {markerX([f, 2 * f, -f, -2 * f], cfg, X, AY)}

        {/* rays */}
        {rays.map((r, i) => (
          <g key={i}>
            <line x1={X(r.p.x)} y1={Y(r.p.y)} x2={X(r.hit.x)} y2={Y(r.hit.y)}
              stroke={REAL} strokeWidth="1.6" markerEnd="url(#rd-arr)" />
            <line x1={X(r.hit.x)} y1={Y(r.hit.y)} x2={X(r.out.x)} y2={Y(r.out.y)}
              stroke={REAL} strokeWidth="1.6" />
            {r.dashed && (
              <line x1={X(r.hit.x)} y1={Y(r.hit.y)} x2={X(imgTip.x)} y2={Y(imgTip.y)}
                stroke={VIRT} strokeWidth="1.3" strokeDasharray="4 3" />
            )}
          </g>
        ))}

        {/* object arrow (up, solid) */}
        <Arrow x1={X(objTip.x)} y1={AY} x2={X(objTip.x)} y2={Y(objTip.y)} color={OBJECT} head="up" />
        <text x={X(objTip.x)} y={Y(objTip.y) - 6} textAnchor="middle" fontSize="11"
          fontFamily="ui-sans-serif, system-ui" fontWeight="600" fill={OBJECT}>O</text>

        {/* image arrow — solid cyan if real, dashed amber if virtual */}
        {Number.isFinite(v) && Math.abs(hi) > 0.01 && (
          <>
            <Arrow x1={X(imgTip.x)} y1={AY} x2={X(imgTip.x)} y2={Y(imgTip.y)}
              color={real ? REAL : VIRT} head={hi >= 0 ? 'up' : 'down'} dashed={!real} />
            <text x={X(imgTip.x)} y={hi >= 0 ? Y(imgTip.y) - 6 : Y(imgTip.y) + 14} textAnchor="middle"
              fontSize="11" fontFamily="ui-sans-serif, system-ui" fontWeight="600"
              fill={real ? REAL : VIRT}>I</text>
          </>
        )}

        <defs>
          <marker id="rd-arr" markerWidth="7" markerHeight="7" refX="5.5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill={REAL} />
          </marker>
        </defs>
      </svg>
      <div className="px-3 py-2.5 border-t border-[rgba(15,23,42,0.06)] bg-[#f9f9f6]">
        <span className="font-sans text-[12.5px] text-[#0F172A] leading-snug">{caption}</span>
      </div>
    </div>
  );
}

// Build one construction ray. `hit` on the optic (x=0). Outgoing line passes
// through the image tip: real → segment toward the tip and a little past;
// virtual → a physical diverging segment plus a dashed back-extension to the tip.
function buildRay(hit, p, imgTip, real) {
  if (real && Number.isFinite(imgTip.x)) {
    const dx = imgTip.x - hit.x, dy = imgTip.y - hit.y;
    const out = { x: imgTip.x + dx * 0.18, y: imgTip.y + dy * 0.18 };
    return { p, hit, out, dashed: false };
  }
  // virtual (or image at infinity): outgoing physical ray = continue AWAY from
  // the tip through the hit point; back-extension (dashed) reaches the tip.
  if (!Number.isFinite(imgTip.x)) {
    // parallel emergent (object at focus) — send it straight out to the right.
    return { p, hit, out: { x: hit.x + 40, y: hit.y }, dashed: false };
  }
  const dx = hit.x - imgTip.x, dy = hit.y - imgTip.y;
  const L = Math.hypot(dx, dy) || 1;
  const out = { x: hit.x + (dx / L) * 60, y: hit.y + (dy / L) * 60 };
  return { p, hit, out, dashed: true };
}

function autoCaption(optic, { v, m, real, hi, objH }) {
  if (!Number.isFinite(v)) return 'Object at the focus — reflected/refracted rays emerge parallel; no image forms.';
  const nature = real ? 'real' : 'virtual';
  const orient = hi >= 0 ? 'erect' : 'inverted';
  const size = Math.abs(m) > 1.02 ? 'magnified' : Math.abs(m) < 0.98 ? 'diminished' : 'same size';
  const name = optic.replace('-', ' ');
  return `${cap(name)}: ${nature}, ${orient}, ${size} image  (m = ${m.toFixed(2)}, v = ${v.toFixed(1)} cm).`;
}

const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

// Draw F and 2F ticks. Mirrors: only the front (reflecting) side; lens: both
// sides. Nearer tick = F, farther = 2F (that's C, the centre of curvature, for
// a mirror — labelled 2F here to stay consistent with the numericals).
function markerX(xs, cfg, X, AY) {
  const seen = new Set();
  const marks = xs.filter((x) => {
    if (x === 0) return false;
    if (!cfg.lens && Math.sign(x) !== cfg.fSign) return false;
    const key = x.toFixed(2);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  const minMag = Math.min(...marks.map((x) => Math.abs(x)));
  return marks.map((x, i) => (
    <g key={i}>
      <line x1={X(x)} y1={AY - 5} x2={X(x)} y2={AY + 5} stroke={AXIS} strokeWidth="1.4" />
      <text x={X(x)} y={AY + 18} textAnchor="middle" fontSize="10"
        fontFamily="ui-sans-serif, system-ui" fill="#64748B">
        {Math.abs(Math.abs(x) - minMag) < 1e-6 ? 'F' : '2F'}
      </text>
    </g>
  ));
}

function Mirror({ x, ay, concave }) {
  // concave opens toward the object (left) → arc bulges right; convex bulges left.
  const h = 84, k = 18;
  const dir = concave ? -1 : 1; // control-point x offset
  const d = `M ${x + dir * k} ${ay - h} Q ${x - dir * k} ${ay} ${x + dir * k} ${ay + h}`;
  return <path d={d} fill="none" stroke={OPTIC} strokeWidth="2.4" strokeLinecap="round" />;
}

function Lens({ x, ay, converging }) {
  const h = 84;
  // vertical body + textbook cap arrows (out = converging/convex, in = diverging/concave)
  const tip = converging ? 7 : -7;
  return (
    <g stroke={OPTIC} strokeWidth="2.2" fill="none" strokeLinecap="round">
      <line x1={x} y1={ay - h} x2={x} y2={ay + h} />
      <path d={`M ${x - 6} ${ay - h + Math.abs(tip)} L ${x} ${ay - h} L ${x + 6} ${ay - h + Math.abs(tip)}`}
        transform={converging ? '' : `rotate(180 ${x} ${ay - h})`} />
      <path d={`M ${x - 6} ${ay + h - Math.abs(tip)} L ${x} ${ay + h} L ${x + 6} ${ay + h - Math.abs(tip)}`}
        transform={converging ? '' : `rotate(180 ${x} ${ay + h})`} />
    </g>
  );
}

function Arrow({ x1, y1, x2, y2, color, head, dashed }) {
  const up = head === 'up';
  const hy = up ? y2 + 7 : y2 - 7;
  return (
    <g stroke={color} strokeWidth="2" fill="none" strokeLinecap="round"
      strokeDasharray={dashed ? '4 3' : undefined}>
      <line x1={x1} y1={y1} x2={x2} y2={y2} />
      <path d={`M ${x2 - 5} ${hy} L ${x2} ${y2} L ${x2 + 5} ${hy}`} strokeDasharray="none" />
    </g>
  );
}
