import { useMemo, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { FieldLine, Compass, Cylinder, Sphere, Label, COLOR } from './primitives.jsx';
import { cross, normalize, sub, dot, scale } from './physicsUtils.js';

/**
 * `magnetic-field` — bar magnet / straight wire / solenoid / circular loop.
 * Params: { source, current_direction, show_compass }
 *
 * Physics (both PURE, no Three.js):
 *  - dipole sources (bar-magnet, solenoid, circular-loop): field-line loops follow
 *    the classic dipole family r(theta) = L * sin^2(theta), theta measured from the
 *    pole axis (+y = N) — the standard analytic curve for a bar magnet / current
 *    loop's external field. `fieldDirectionAt` uses the exact dipole formula
 *    B ~ 3(m.r)r - m (direction only; magnitude/mu0 don't matter for a compass).
 *  - straight-wire: field lines are circles around the wire axis; direction is the
 *    Biot-Savart sense B ~ I x r-hat (I = current unit vector, r-hat = wire-to-point).
 */

const AZIMUTHS = 6; // curves per shell
const SHELLS = [0.9, 1.5]; // dipole "size" factors -> 6*2 = 12 curves (<=24 budget)

function dipoleLine(azimuth, shellL, poleAxis) {
  // poleAxis: unit vector, +1 along +y (N up) by convention for all dipole sources.
  const pts = [];
  const steps = 40;
  for (let i = 0; i <= steps; i++) {
    const theta = 0.06 + (i / steps) * (Math.PI - 0.12); // avoid the singular poles
    const r = shellL * Math.sin(theta) ** 2;
    const x = r * Math.sin(theta) * Math.cos(azimuth);
    const z = r * Math.sin(theta) * Math.sin(azimuth);
    const y = r * Math.cos(theta) * (poleAxis >= 0 ? 1 : -1);
    pts.push([x, y, z]);
  }
  return pts;
}

function wireCircles() {
  const radii = [0.5, 0.85, 1.2];
  const heights = [-0.7, 0, 0.7];
  const curves = [];
  for (const h of heights) {
    for (const r of radii) {
      const pts = [];
      const steps = 36;
      for (let i = 0; i <= steps; i++) {
        const a = (i / steps) * Math.PI * 2;
        pts.push([Math.cos(a) * r, h, Math.sin(a) * r]);
      }
      curves.push({ pts, radius: r });
    }
  }
  return curves;
}

// eslint-disable-next-line react-refresh/only-export-components
export function computePhysics(params) {
  const source = params?.source || 'bar-magnet';
  const currentSign = params?.current_direction === 'into' ? -1 : 1; // 'out' | 'n/a' -> +1

  if (source === 'straight-wire') {
    const circles = wireCircles().map(({ pts }) => pts);
    const fieldDirectionAt = (p) => {
      const rHat = normalize([p[0], 0, p[2]]);
      const iHat = [0, currentSign, 0];
      return normalize(cross(iHat, rHat));
    };
    return { source, lines: circles.slice(0, 24), fieldDirectionAt, currentSign };
  }

  // dipole family: bar-magnet, solenoid (external), circular-loop
  const lines = [];
  for (const shellL of SHELLS) {
    for (let i = 0; i < AZIMUTHS; i++) {
      lines.push(dipoleLine((i / AZIMUTHS) * Math.PI * 2, shellL, 1));
    }
  }
  const mHat = [0, 1, 0]; // N at +y for every dipole-family source
  const fieldDirectionAt = (p) => {
    const rHat = normalize(p);
    const term = sub(scale(rHat, 3 * dot(mHat, rHat)), mHat);
    return normalize(term);
  };
  const internal = source === 'solenoid'
    ? [[0, -0.9, 0], [0, 0.9, 0]] // uniform internal field endpoints, drawn as a straight core line
    : null;
  return { source, lines: lines.slice(0, 24), fieldDirectionAt, internal };
}

export default function MagneticFieldScene({ params, animate }) {
  const derived = useMemo(() => computePhysics(params), [params]);
  const accumRef = useRef(0); // only ever read/written inside useFrame — never during render
  const [phase, setPhase] = useState(0);

  useFrame((_, dt) => {
    if (!animate) return;
    // Throttled to ~12fps: the flow phase only needs to look "alive", and
    // re-rendering the field-line arrows at 60fps would burn the perf budget
    // for a cosmetic effect (see guardrail 1 in PROMPT-physics-3d.md).
    accumRef.current += dt;
    if (accumRef.current < 1 / 12) return;
    accumRef.current = 0;
    setPhase((p) => (p + 0.06) % 1);
  });

  const showCompass = params?.show_compass !== false;
  const compassPoints = useMemo(() => {
    if (derived.source === 'straight-wire') {
      return [[1.3, 0, 0], [-1.3, 0.4, 0], [0, -0.4, 1.3]];
    }
    return [[1.6, 0.5, 0], [-1.4, -0.3, 0.6], [0.3, 0, -1.6]];
  }, [derived.source]);

  return (
    <group>
      {derived.source === 'straight-wire' ? (
        <Cylinder position={[0, 0, 0]} radius={0.05} height={2.2} color={COLOR.structure} />
      ) : derived.source === 'solenoid' ? (
        <Cylinder position={[0, 0, 0]} radius={0.45} height={1.8} color={COLOR.structure} rotation={[0, 0, 0]} radialSegments={24} transparent opacity={0.25} />
      ) : derived.source === 'circular-loop' ? (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.6, 0.04, 12, 40]} />
          <meshStandardMaterial color={COLOR.structure} />
        </mesh>
      ) : (
        <group>
          <Cylinder position={[0, 0.5, 0]} radius={0.28} height={1} color={COLOR.reaction} />
          <Cylinder position={[0, -0.5, 0]} radius={0.28} height={1} color={COLOR.structure} />
          <Label position={[0, 1.1, 0]} text="N" fontSize={0.2} color={COLOR.reaction} />
          <Label position={[0, -1.1, 0]} text="S" fontSize={0.2} color={COLOR.structure} />
        </group>
      )}

      {derived.lines.map((pts, i) => (
        <FieldLine key={i} points={pts} color={COLOR.computed} phase={phase} />
      ))}

      {showCompass && compassPoints.map((p, i) => (
        <group key={i}>
          <Sphere position={p} radius={0.03} color={COLOR.faint} />
          <Compass position={p} direction={derived.fieldDirectionAt(p)} size={0.3} />
        </group>
      ))}
    </group>
  );
}
