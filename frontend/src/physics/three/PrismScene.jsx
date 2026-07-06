import { useMemo } from 'react';
import { Line } from '@react-three/drei';
import { COLOR } from './primitives.jsx';

/**
 * `dispersion-prism` — white light disperses into VIBGYOR, violet bends most.
 * No params beyond caption; the physics that matters here is ORDER, not exact
 * refractive indices (per PROMPT-physics-3d.md). `computePhysics` fixes the
 * deviation angle for each colour strictly decreasing from violet -> red.
 */
const SPECTRUM = [
  { name: 'violet', color: '#7C3AED' },
  { name: 'indigo', color: '#4338CA' },
  { name: 'blue', color: '#0891B2' },
  { name: 'green', color: '#0F766E' },
  { name: 'yellow', color: '#CA8A04' },
  { name: 'orange', color: '#EA580C' },
  { name: 'red', color: '#B91C1C' },
];

// eslint-disable-next-line react-refresh/only-export-components
export function computePhysics() {
  const maxDeviation = 0.55; // radians, violet
  const minDeviation = 0.28; // radians, red
  const step = (maxDeviation - minDeviation) / (SPECTRUM.length - 1);
  return {
    rays: SPECTRUM.map((s, i) => ({ ...s, deviation: maxDeviation - i * step })),
  };
}

export default function PrismScene() {
  const { rays } = useMemo(() => computePhysics(), []);
  const exitPoint = [0.35, 0, 0];
  const incident = [[-2.2, 0.9, 0], exitPoint];

  return (
    <group>
      {/* triangular prism: a 3-sided cylinder IS a triangular prism */}
      <mesh position={[0, 0, 0]} rotation={[0, Math.PI / 6, 0]}>
        <cylinderGeometry args={[0.85, 0.85, 1.4, 3]} />
        <meshStandardMaterial color={COLOR.faint} transparent opacity={0.28} roughness={0.1} />
      </mesh>

      {/* incident white ray */}
      <Line points={incident} color="#F8FAFC" lineWidth={2.5} />

      {/* dispersed rays fan out to the right, violet deviates most (steepest downward) */}
      {rays.map((r, i) => {
        const length = 2.4;
        const end = [exitPoint[0] + Math.cos(r.deviation) * length, exitPoint[1] - Math.sin(r.deviation) * length, 0];
        return <Line key={i} points={[exitPoint, end]} color={r.color} lineWidth={2} />;
      })}
    </group>
  );
}
