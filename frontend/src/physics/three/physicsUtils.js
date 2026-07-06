/**
 * Pure math helpers for `diagram3d` scene `computePhysics()` functions.
 * NO Three.js / React imports here — this is the half of every scene that a
 * reviewer (or a future test) can read without touching graphics at all.
 */

export const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

export const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

export const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];

export const length = (a) => Math.sqrt(dot(a, a));

export const normalize = (a) => {
  const l = length(a) || 1;
  return [a[0] / l, a[1] / l, a[2] / l];
};

export const scale = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
export const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
export const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];

/** '+x' | '-y' | '+z' | ... -> unit vector. Falls back to +x on garbage input
 *  so a malformed lesson JSON degrades to *a* direction instead of NaNs. */
const AXES = {
  '+x': [1, 0, 0], '-x': [-1, 0, 0],
  '+y': [0, 1, 0], '-y': [0, -1, 0],
  '+z': [0, 0, 1], '-z': [0, 0, -1],
};
export const axisToVector = (s) => AXES[s] || AXES['+x'];

export const vectorToAxisLabel = (v) => {
  const abs = v.map(Math.abs);
  const i = abs.indexOf(Math.max(...abs));
  const axis = ['x', 'y', 'z'][i];
  return `${v[i] >= 0 ? '+' : '-'}${axis}`;
};
