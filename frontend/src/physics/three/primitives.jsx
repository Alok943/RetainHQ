import { useMemo } from 'react';
import * as THREE from 'three';
import { Line, Text } from '@react-three/drei';

/**
 * Shared primitive library for `diagram3d` scenes (see content/PROMPT-physics-3d.md).
 *
 * Every primitive takes PHYSICAL/SEMANTIC props (a direction + magnitude + colour,
 * not raw vertex arrays) and owns its own labelling. Scenes compose these instead of
 * building geometry ad hoc — this is what keeps a scene file to "params -> physics ->
 * primitives" instead of a pile of hand-tuned meshes.
 *
 * Palette (matches the rest of RetainHQ / RayDiagram): cyan #0891B2 = the computed/
 * "answer" element, slate #64748B = structure, amber #B45309 = reaction/secondary.
 */

// This is a primitive/constant library, not a component module — HMR granularity doesn't apply.
// eslint-disable-next-line react-refresh/only-export-components
export const COLOR = {
  computed: '#0891B2',
  structure: '#64748B',
  reaction: '#B45309',
  ink: '#0F172A',
  faint: '#94A3B8',
};

const v3 = (a) => (Array.isArray(a) ? new THREE.Vector3(...a) : a instanceof THREE.Vector3 ? a : new THREE.Vector3(0, 0, 0));

// ---------------------------------------------------------------- Geometry --

export function Sphere({ position = [0, 0, 0], radius = 1, color = COLOR.structure, emissive, wireframe = false }) {
  return (
    <mesh position={position}>
      <sphereGeometry args={[radius, 24, 16]} />
      <meshStandardMaterial color={color} emissive={emissive || color} emissiveIntensity={emissive ? 0.35 : 0} wireframe={wireframe} roughness={0.55} metalness={0.05} />
    </mesh>
  );
}

export function Cube({ position = [0, 0, 0], size = [1, 1, 1], color = COLOR.structure, rotation = [0, 0, 0] }) {
  return (
    <mesh position={position} rotation={rotation}>
      <boxGeometry args={size} />
      <meshStandardMaterial color={color} roughness={0.6} metalness={0.05} />
    </mesh>
  );
}

export function Cylinder({ position = [0, 0, 0], radius = 0.5, height = 1, color = COLOR.structure, rotation = [0, 0, 0], radialSegments = 20, transparent = false, opacity = 1 }) {
  return (
    <mesh position={position} rotation={rotation}>
      <cylinderGeometry args={[radius, radius, height, radialSegments]} />
      <meshStandardMaterial color={color} roughness={0.6} metalness={0.05} transparent={transparent} opacity={opacity} />
    </mesh>
  );
}

export function Plane({ position = [0, 0, 0], size = [4, 4], color = COLOR.faint, rotation = [-Math.PI / 2, 0, 0], opacity = 0.15 }) {
  return (
    <mesh position={position} rotation={rotation}>
      <planeGeometry args={size} />
      <meshStandardMaterial color={color} transparent opacity={opacity} side={THREE.DoubleSide} />
    </mesh>
  );
}

// ----------------------------------------------------------------- Physics --

/** A single arrow: origin + direction (auto-normalised) + physical magnitude
 *  mapped to a visual length via `scale` (keeps the JSON free of pixel/world
 *  units — callers pass real magnitudes, this does the cosmetic clamp). */
export function Vector({ origin = [0, 0, 0], direction = [0, 1, 0], length = 1, color = COLOR.computed, label, labelColor }) {
  const o = v3(origin);
  const dir = v3(direction).normalize();
  const end = o.clone().addScaledVector(dir, length);
  const headLength = Math.min(0.22, length * 0.35);
  const headWidth = headLength * 0.6;
  // Deps are the primitive scalar components, not `o`/`dir` themselves — those
  // are fresh Vector3 instances every render, so including them would defeat
  // the memo entirely.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const arrow = useMemo(() => new THREE.ArrowHelper(dir, o, Math.max(length, 0.001), color, headLength, headWidth), [o.x, o.y, o.z, dir.x, dir.y, dir.z, length, color, headLength, headWidth]);
  return (
    <group>
      <primitive object={arrow} />
      {label && (
        <Text position={[end.x + dir.x * 0.15, end.y + dir.y * 0.15, end.z + dir.z * 0.15]} fontSize={0.16} color={labelColor || color} anchorX="center" anchorY="middle">
          {label}
        </Text>
      )}
    </group>
  );
}

/** Alias kept distinct in name for scenes that want to be explicit about intent
 *  (a force, as opposed to a generic vector like B or I). Same primitive. */
export const ForceArrow = Vector;

/** A circular orbit path (just the ring, not the moving body). */
export function Orbit({ radius = 2, color = COLOR.faint, segments = 96, plane = 'xz' }) {
  const points = useMemo(() => {
    const pts = [];
    for (let i = 0; i <= segments; i++) {
      const t = (i / segments) * Math.PI * 2;
      const a = Math.cos(t) * radius;
      const b = Math.sin(t) * radius;
      pts.push(plane === 'xz' ? [a, 0, b] : plane === 'xy' ? [a, b, 0] : [0, a, b]);
    }
    return pts;
  }, [radius, segments, plane]);
  return <Line points={points} color={color} lineWidth={1} dashed dashSize={0.08} gapSize={0.08} transparent opacity={0.5} />;
}

/** One magnetic/electric field line — an ordered list of [x,y,z] points, with an
 *  optional flow direction (drawn as small arrowheads along the curve, animated
 *  by nudging a phase, not by moving geometry — cheap and deterministic). */
export function FieldLine({ points, color = COLOR.computed, flow = 1, phase = 0, lineWidth = 1.2 }) {
  const valid = !!points && points.length >= 2;
  const arrowCount = valid ? Math.min(3, Math.max(1, Math.floor(points.length / 12))) : 0;
  // Hooks must run unconditionally every render — the `valid` guard lives
  // INSIDE the memo body (and the early return comes after), not before it.
  const arrows = useMemo(() => {
    if (!valid) return [];
    const out = [];
    for (let i = 0; i < arrowCount; i++) {
      const f = ((i / arrowCount) + phase) % 1;
      const idx = Math.min(points.length - 2, Math.max(0, Math.floor(f * (points.length - 1))));
      const a = new THREE.Vector3(...points[idx]);
      const b = new THREE.Vector3(...points[idx + 1]);
      const dir = b.clone().sub(a).normalize();
      if (dir.lengthSq() === 0) continue;
      out.push({ pos: a, dir });
    }
    return out;
  }, [valid, points, arrowCount, phase]);
  if (!valid) return null;
  return (
    <group>
      <Line points={points} color={color} lineWidth={lineWidth} transparent opacity={0.75} />
      {flow !== 0 && arrows.map((a, i) => (
        <mesh key={i} position={a.pos} quaternion={new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), flow > 0 ? a.dir : a.dir.clone().negate())}>
          <coneGeometry args={[0.045, 0.13, 8]} />
          <meshStandardMaterial color={color} />
        </mesh>
      ))}
    </group>
  );
}

/** A compass needle that aligns to a local field direction (projected onto the
 *  needle's rotation plane). `direction` is the field vector at the needle's spot. */
export function Compass({ position = [0, 0, 0], direction = [1, 0, 0], size = 0.35 }) {
  const dir = v3(direction).normalize();
  // eslint-disable-next-line react-hooks/exhaustive-deps -- deps are dir's scalar components, see Vector above
  const quat = useMemo(() => new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), dir), [dir.x, dir.y, dir.z]);
  return (
    <group position={position} quaternion={quat}>
      <mesh position={[0, 0, size * 0.25]}>
        <coneGeometry args={[size * 0.16, size * 0.5, 8]} />
        <meshStandardMaterial color={COLOR.computed} />
      </mesh>
      <mesh position={[0, 0, -size * 0.25]} rotation={[Math.PI, 0, 0]}>
        <coneGeometry args={[size * 0.16, size * 0.5, 8]} />
        <meshStandardMaterial color={COLOR.reaction} />
      </mesh>
      <mesh>
        <cylinderGeometry args={[0.02, 0.02, size * 0.1, 8]} />
        <meshStandardMaterial color={COLOR.ink} />
      </mesh>
    </group>
  );
}

/** A dashed bracket + label between two points, showing a physical distance. */
export function DistanceMarker({ from, to, label, color = COLOR.faint, offset = [0, 0.3, 0] }) {
  const a = v3(from), b = v3(to);
  const mid = a.clone().add(b).multiplyScalar(0.5).add(v3(offset));
  return (
    <group>
      <Line points={[a.toArray(), b.clone().add(v3(offset)).toArray()].length === 2 ? [a.toArray(), a.clone().add(v3(offset)).toArray()] : []} color={color} />
      <Line points={[a.clone().add(v3(offset)).toArray(), b.clone().add(v3(offset)).toArray()]} color={color} dashed dashSize={0.06} gapSize={0.05} lineWidth={1} />
      <Line points={[b.toArray(), b.clone().add(v3(offset)).toArray()]} color={color} />
      {label && (
        <Text position={mid.toArray()} fontSize={0.14} color={COLOR.ink} anchorX="center" anchorY="bottom">
          {label}
        </Text>
      )}
    </group>
  );
}

/** A 1D lattice of particles for the longitudinal-wave scene. `displacements` is
 *  an array of scalar offsets ALONG the propagation axis, one per particle. */
export function ParticleGrid({ count = 60, spacing = 0.12, axis = 'x', displacements, color = COLOR.computed, radius = 0.045 }) {
  const positions = useMemo(() => {
    const dirVec = axis === 'x' ? [1, 0, 0] : axis === 'y' ? [0, 1, 0] : [0, 0, 1];
    const out = [];
    const start = -((count - 1) * spacing) / 2;
    for (let i = 0; i < count; i++) {
      const base = start + i * spacing;
      const d = (displacements && displacements[i]) || 0;
      const total = base + d;
      out.push([dirVec[0] * total, dirVec[1] * total, dirVec[2] * total]);
    }
    return out;
  }, [count, spacing, axis, displacements]);
  return (
    <group>
      {positions.map((p, i) => (
        <mesh key={i} position={p}>
          <sphereGeometry args={[radius, 10, 8]} />
          <meshStandardMaterial color={color} />
        </mesh>
      ))}
    </group>
  );
}

/** A small arc between two directions, with an optional degree label — used to
 *  call out the angle between two vectors (e.g. field vs. axis). */
export function Angle({ center = [0, 0, 0], from = [1, 0, 0], to = [0, 1, 0], radius = 0.4, color = COLOR.faint, label }) {
  const c = v3(center);
  const a = v3(from).normalize();
  const b = v3(to).normalize();
  const points = useMemo(() => {
    const quatTotal = new THREE.Quaternion().setFromUnitVectors(a, b);
    const angle = 2 * Math.acos(Math.min(1, Math.max(-1, quatTotal.w)));
    const axis = new THREE.Vector3(quatTotal.x, quatTotal.y, quatTotal.z).normalize();
    const steps = 20;
    const pts = [];
    for (let i = 0; i <= steps; i++) {
      const t = (i / steps) * angle;
      const q = new THREE.Quaternion().setFromAxisAngle(axis.lengthSq() ? axis : new THREE.Vector3(0, 0, 1), t);
      const p = a.clone().applyQuaternion(q).multiplyScalar(radius).add(c);
      pts.push(p.toArray());
    }
    return pts;
    // eslint-disable-next-line react-hooks/exhaustive-deps -- deps are a/b/c's scalar components, see Vector above
  }, [c.x, c.y, c.z, a.x, a.y, a.z, b.x, b.y, b.z, radius]);
  return (
    <group>
      <Line points={points} color={color} lineWidth={1} />
      {label && (
        <Text position={points[Math.floor(points.length / 2)]} fontSize={0.13} color={color} anchorX="center" anchorY="middle">
          {label}
        </Text>
      )}
    </group>
  );
}

// ----------------------------------------------------------------------- UI --

export function Label({ position, text, color = COLOR.ink, fontSize = 0.16, anchorX = 'center', anchorY = 'middle' }) {
  return (
    <Text position={position} fontSize={fontSize} color={color} anchorX={anchorX} anchorY={anchorY}>
      {text}
    </Text>
  );
}

export function Equation({ position, text, color = COLOR.computed, fontSize = 0.15 }) {
  return (
    <Text position={position} fontSize={fontSize} color={color} anchorX="center" anchorY="middle" font={undefined}>
      {text}
    </Text>
  );
}

/** DOM-based tooltip anchored to a 3D point — only mount `Html` lazily (caller's
 *  responsibility, this file has no drei/Html import cost beyond what's already
 *  pulled in by Line/Text). Kept minimal: a labelled pill. */
export function Tooltip({ position, text }) {
  return (
    <Text position={position} fontSize={0.12} color="#ffffff" outlineWidth={0.01} outlineColor={COLOR.ink} anchorX="center" anchorY="bottom">
      {text}
    </Text>
  );
}

/** A soft pulsing ring/halo around a point — used to draw the eye to "the
 *  computed element" (e.g. the third Fleming axis) without extra chrome. */
export function Highlight({ position = [0, 0, 0], radius = 0.3, color = COLOR.computed }) {
  return (
    <mesh position={position} rotation={[-Math.PI / 2, 0, 0]}>
      <ringGeometry args={[radius * 0.82, radius, 32]} />
      <meshBasicMaterial color={color} transparent opacity={0.5} side={THREE.DoubleSide} />
    </mesh>
  );
}

/** A short leader line from an anchor point to a label offset — for callouts
 *  that shouldn't sit directly on top of geometry. */
export function Annotation({ anchor, offset = [0, 0.4, 0], text, color = COLOR.ink }) {
  const a = v3(anchor);
  const labelPos = a.clone().add(v3(offset));
  return (
    <group>
      <Line points={[a.toArray(), labelPos.toArray()]} color={color} lineWidth={1} dashed dashSize={0.04} gapSize={0.04} />
      <Text position={labelPos.toArray()} fontSize={0.13} color={color} anchorX="center" anchorY="bottom">
        {text}
      </Text>
    </group>
  );
}
