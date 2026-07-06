import React from 'react';

/**
 * GraphDiagram — dependency-free SVG graph renderer for the `physics` lesson kind.
 *
 * Renders a `diagram` of type "graph": axes with labels, auto-scaled to the data
 * range (with padding), either a polyline from `curve` data points or a straight
 * line from `line:{slope,intercept}`, small dot markers, and optional annotations.
 *
 * Spec (diagram.type === "graph"):
 *   {
 *     "type": "graph",
 *     "axes": { "x": "time (s)", "y": "velocity (m/s)" },
 *     "curve": [{ "x": 0, "y": 0 }, { "x": 5, "y": 10 }, ...]   // OR
 *     "line":  { "slope": 2, "intercept": 0 },
 *     "annotations": [{ "x": 3, "y": 6, "label": "t = 3 s" }],   // optional
 *     "caption": "Velocity-time graph for uniform acceleration."   // optional
 *   }
 *
 * Matches card chrome of RayDiagram: rounded-lg border + caption row.
 * Colors: #0891B2 cyan accent, #94A3B8 axes, #0F172A ink.
 * No external dependencies — pure SVG.
 */

const ACCENT = '#0891B2';  // cyan — line, dots
const AXIS   = '#94A3B8';  // slate — axis lines, ticks, labels
const INK    = '#0F172A';  // dark — axis titles, annotation labels

const VBW = 520, VBH = 300;
// Layout margins (SVG units): top, right, bottom (label area), left (label area)
const MT = 18, MR = 20, MB = 60, ML = 62;

/** Map a data value to SVG pixel space. */
function makeMappers(minX, maxX, minY, maxY) {
  const plotW = VBW - ML - MR;
  const plotH = VBH - MT - MB;
  const mx = (x) => ML + ((x - minX) / (maxX - minX)) * plotW;
  const my = (y) => MT + plotH - ((y - minY) / (maxY - minY)) * plotH;
  return { mx, my, plotW, plotH };
}

/** Generate ~4-6 nice tick values covering [min, max]. */
function niceTicks(min, max, targetCount = 5) {
  if (max === min) return [min];
  const range = max - min;
  const rawStep = range / (targetCount - 1);
  const mag = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const norm = rawStep / mag;
  const nice = norm < 1.5 ? 1 : norm < 3.5 ? 2 : norm < 7.5 ? 5 : 10;
  const step = nice * mag;
  const start = Math.ceil(min / step) * step;
  const ticks = [];
  for (let t = start; t <= max + step * 0.01; t += step) {
    ticks.push(Math.round(t * 1e9) / 1e9);
  }
  return ticks;
}

/** Format a tick label without unnecessary trailing zeros. */
function fmt(v) {
  if (Number.isInteger(v)) return String(v);
  return v.toFixed(2).replace(/\.?0+$/, '');
}

export default function GraphDiagram({ diagram }) {
  const d = diagram || {};
  const axes = (typeof d.axes === 'object' && d.axes) ? d.axes : {};
  const annotations = Array.isArray(d.annotations) ? d.annotations : [];
  const caption = d.caption || null;

  // --- Collect data points ---
  let points = [];
  if (Array.isArray(d.curve) && d.curve.length >= 2) {
    points = d.curve
      .filter((p) => typeof p.x === 'number' && typeof p.y === 'number')
      .sort((a, b) => a.x - b.x);
  }

  // --- Determine data domain ---
  let allX, allY;
  if (points.length >= 2) {
    allX = points.map((p) => p.x);
    allY = points.map((p) => p.y);
  } else if (d.line && typeof d.line.slope === 'number') {
    // Pick a sensible domain for the line; use 0–10 as fallback.
    allX = [0, 10];
    const y0 = d.line.slope * 0 + (d.line.intercept || 0);
    const y1 = d.line.slope * 10 + (d.line.intercept || 0);
    allY = [y0, y1];
  } else {
    // Nothing to draw — return null so the parent shows nothing.
    return null;
  }

  // Add annotation coords into domain for correct auto-scaling.
  annotations.forEach((a) => {
    if (typeof a.x === 'number') allX.push(a.x);
    if (typeof a.y === 'number') allY.push(a.y);
  });

  const rawMinX = Math.min(...allX), rawMaxX = Math.max(...allX);
  const rawMinY = Math.min(...allY), rawMaxY = Math.max(...allY);

  // Always include zero in Y if the data is close to it (physics graphs usually start at 0).
  const minY = Math.min(0, rawMinY);
  const maxY = rawMaxY === minY ? rawMaxY + 1 : rawMaxY;

  // Pad X a little so points aren't flush to the axes.
  const padX = (rawMaxX - rawMinX) * 0.08 || 0.5;
  const minX = rawMinX - padX;
  const maxX = rawMaxX + padX;

  const { mx, my, plotW, plotH } = makeMappers(minX, maxX, minY, maxY);

  // --- Build path data for curve or line ---
  let pathD = '';
  if (points.length >= 2) {
    pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${mx(p.x).toFixed(1)} ${my(p.y).toFixed(1)}`).join(' ');
  } else if (d.line) {
    const intercept = d.line.intercept || 0;
    const y0 = d.line.slope * rawMinX + intercept;
    const y1 = d.line.slope * rawMaxX + intercept;
    pathD = `M ${mx(rawMinX).toFixed(1)} ${my(y0).toFixed(1)} L ${mx(rawMaxX).toFixed(1)} ${my(y1).toFixed(1)}`;
  }

  const xTicks = niceTicks(rawMinX, rawMaxX, 6);
  const yTicks = niceTicks(minY, maxY, 6);

  const plotBottom = MT + plotH;
  const plotRight = ML + plotW;

  return (
    <div className="rounded-lg border border-[rgba(15,23,42,0.12)] bg-white overflow-hidden">
      <svg viewBox={`0 0 ${VBW} ${VBH}`} className="w-full" style={{ maxHeight: 320 }}>

        {/* ── Plot area background (subtle) ── */}
        <rect x={ML} y={MT} width={plotW} height={plotH}
          fill="#f8fafc" stroke={AXIS} strokeWidth="0.8" />

        {/* ── X grid lines + ticks + labels ── */}
        {xTicks.map((t) => {
          const sx = mx(t);
          return (
            <g key={`xt-${t}`}>
              <line x1={sx} y1={MT} x2={sx} y2={plotBottom}
                stroke={AXIS} strokeWidth="0.5" strokeDasharray="3 3" opacity="0.5" />
              <line x1={sx} y1={plotBottom} x2={sx} y2={plotBottom + 5}
                stroke={AXIS} strokeWidth="1" />
              <text x={sx} y={plotBottom + 16} textAnchor="middle"
                fontSize="11" fontFamily="ui-sans-serif, system-ui" fill={AXIS}>
                {fmt(t)}
              </text>
            </g>
          );
        })}

        {/* ── Y grid lines + ticks + labels ── */}
        {yTicks.map((t) => {
          const sy = my(t);
          return (
            <g key={`yt-${t}`}>
              <line x1={ML} y1={sy} x2={plotRight} y2={sy}
                stroke={AXIS} strokeWidth="0.5" strokeDasharray="3 3" opacity="0.5" />
              <line x1={ML - 5} y1={sy} x2={ML} y2={sy}
                stroke={AXIS} strokeWidth="1" />
              <text x={ML - 8} y={sy + 4} textAnchor="end"
                fontSize="11" fontFamily="ui-sans-serif, system-ui" fill={AXIS}>
                {fmt(t)}
              </text>
            </g>
          );
        })}

        {/* ── Axes (drawn on top of grid) ── */}
        {/* X axis */}
        <line x1={ML} y1={plotBottom} x2={plotRight} y2={plotBottom}
          stroke={AXIS} strokeWidth="1.5" />
        {/* Y axis */}
        <line x1={ML} y1={MT} x2={ML} y2={plotBottom}
          stroke={AXIS} strokeWidth="1.5" />

        {/* ── Zero line (Y = 0) if inside range ── */}
        {minY < 0 && maxY > 0 && (
          <line x1={ML} y1={my(0)} x2={plotRight} y2={my(0)}
            stroke={AXIS} strokeWidth="1" strokeDasharray="5 3" opacity="0.7" />
        )}

        {/* ── The curve / line ── */}
        {pathD && (
          <path d={pathD} fill="none" stroke={ACCENT} strokeWidth="2.4"
            strokeLinecap="round" strokeLinejoin="round" />
        )}

        {/* ── Data point dots (curve only) ── */}
        {points.map((p, i) => (
          <circle key={i} cx={mx(p.x)} cy={my(p.y)} r="4"
            fill="white" stroke={ACCENT} strokeWidth="2" />
        ))}

        {/* ── Annotations ── */}
        {annotations.map((a, i) => {
          if (typeof a.x !== 'number' || typeof a.y !== 'number') return null;
          const ax = mx(a.x), ay = my(a.y);
          return (
            <g key={i}>
              <line x1={ax} y1={ay} x2={ax} y2={my(minY)}
                stroke={INK} strokeWidth="0.8" strokeDasharray="3 2" opacity="0.5" />
              <circle cx={ax} cy={ay} r="4.5"
                fill={ACCENT} stroke="white" strokeWidth="1.5" />
              {a.label && (
                <text x={ax} y={ay - 10} textAnchor="middle"
                  fontSize="10" fontFamily="ui-sans-serif, system-ui"
                  fontWeight="600" fill={INK}>
                  {a.label}
                </text>
              )}
            </g>
          );
        })}

        {/* ── Axis titles ── */}
        {axes.x && (
          <text
            x={ML + plotW / 2}
            y={plotBottom + 42}
            textAnchor="middle"
            fontSize="12"
            fontFamily="ui-sans-serif, system-ui"
            fontWeight="600"
            fill={INK}
          >
            {axes.x}
          </text>
        )}
        {axes.y && (
          <text
            x={14}
            y={MT + plotH / 2}
            textAnchor="middle"
            fontSize="12"
            fontFamily="ui-sans-serif, system-ui"
            fontWeight="600"
            fill={INK}
            transform={`rotate(-90, 14, ${MT + plotH / 2})`}
          >
            {axes.y}
          </text>
        )}
      </svg>

      {/* Caption row */}
      {caption && (
        <div className="px-3 py-2.5 border-t border-[rgba(15,23,42,0.06)] bg-[#f9f9f6]">
          <span className="font-sans text-[12.5px] text-[#0F172A] leading-snug">{caption}</span>
        </div>
      )}
    </div>
  );
}
