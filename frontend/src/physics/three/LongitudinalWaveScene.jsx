import { useMemo, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { ParticleGrid, COLOR } from './primitives.jsx';

/**
 * `longitudinal-wave` — sound: particles oscillate ALONG the propagation axis
 * (never transverse), producing visible compressions/rarefactions that travel.
 * Params: { frequency, amplitude? }
 *
 * Physics (pure): displacement(x, t) = A * sin(k*x - omega*t), applied along the
 * SAME axis as x itself (x, not y) — that "along, not across" is the one fact
 * this scene exists to teach; see three/__checks__.md.
 *
 * `amplitude` is optional and discrete ("soft" | "loud", default "loud") — it
 * maps directly to loudness (amplitude, NOT frequency/pitch), so a lesson like
 * relate-loudness-to-amplitude can `manipulate` it: same frequency, only the
 * compressions/rarefactions get denser/sparser, never faster.
 */
const COUNT = 72;
const SPACING = 0.1;
const AMPLITUDES = { soft: 0.022, loud: 0.05 };

// eslint-disable-next-line react-refresh/only-export-components
export function computePhysics(params) {
  const frequency = Number(params?.frequency) > 0 ? Number(params.frequency) : 1;
  const omega = 2 * Math.PI * frequency;
  const wavelength = (COUNT * SPACING) / 3; // ~3 visible cycles across the lattice
  const k = (2 * Math.PI) / wavelength;
  const amplitude = AMPLITUDES[params?.amplitude] ?? AMPLITUDES.loud;
  return { omega, k, amplitude, count: COUNT, spacing: SPACING };
}

export default function LongitudinalWaveScene({ params, animate }) {
  const d = useMemo(() => computePhysics(params), [params]);
  // The true elapsed clock lives in a ref (only ever touched inside useFrame,
  // never read during render); `t` state is the throttled snapshot React
  // actually renders from.
  const clockRef = useRef(0);
  const accumRef = useRef(0);
  const [t, setT] = useState(0);

  useFrame((_, dt) => {
    if (!animate) return;
    clockRef.current += dt;
    // Throttled to ~30fps re-render — the sine motion still reads as smooth,
    // and this halves the React reconciliation cost of ~70 particle meshes.
    accumRef.current += dt;
    if (accumRef.current < 1 / 30) return;
    accumRef.current = 0;
    setT(clockRef.current);
  });

  const displacements = useMemo(() => {
    const start = -((d.count - 1) * d.spacing) / 2;
    const out = new Array(d.count);
    for (let i = 0; i < d.count; i++) {
      const x = start + i * d.spacing;
      out[i] = d.amplitude * Math.sin(d.k * x - d.omega * t);
    }
    return out;
  }, [d, t]);

  return <ParticleGrid count={d.count} spacing={d.spacing} axis="x" displacements={displacements} color={COLOR.computed} />;
}
