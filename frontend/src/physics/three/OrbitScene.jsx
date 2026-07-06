import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { Orbit, Sphere, Label, COLOR } from './primitives.jsx';
import { clamp } from './physicsUtils.js';

/**
 * `orbit` — universal gravitation / satellites / free-fall-vs-orbit.
 * Params: { central: {label, mass}, satellite: {label, mass}, radius_km, show_force_vector }
 *
 * Physics: bodies are sized by a LOG-scaled mass ratio (clamped so the satellite
 * never disappears against a much larger central body); the orbit radius on
 * screen is a fixed "hero" framing distance (radius_km only drives the caption/
 * label, not the world-unit scale, so wildly different real distances — Moon vs.
 * a geostationary satellite — don't blow up or collapse the canvas). Motion is
 * a constant angular rate (parametric, not simulated) with the force vector
 * re-pointing at the centre every frame.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function computePhysics(params) {
  const centralMass = Number(params?.central?.mass) || 1;
  const satMass = Number(params?.satellite?.mass) || 1;
  const ratio = clamp(satMass / centralMass, 1e-8, 1);
  // log-scaled: a much lighter satellite still renders at a visible minimum size.
  const satelliteRadius = clamp(0.14 + 0.12 * (1 + Math.log10(ratio) / 8), 0.14, 0.55);
  const centralRadius = 1.0;
  const orbitRadius = centralRadius + satelliteRadius + 1.8;
  const angularSpeed = (Math.PI * 2) / 8; // one revolution per ~8s — "slow orbit, not a blur"
  return { centralRadius, satelliteRadius, orbitRadius, angularSpeed };
}

export default function OrbitScene({ params, animate }) {
  const derived = useMemo(() => computePhysics(params), [params]);
  const { centralRadius, satelliteRadius, orbitRadius, angularSpeed } = derived;
  const angleRef = useRef(0);
  const satGroupRef = useRef();
  const showForce = params?.show_force_vector !== false;
  // Long enough to read clearly against the orbit radius, not just a nub past the satellite.
  const forceLength = orbitRadius * 0.55;
  const arrow = useMemo(
    () => (showForce ? new THREE.ArrowHelper(new THREE.Vector3(-1, 0, 0), new THREE.Vector3(orbitRadius, 0, 0), forceLength, COLOR.reaction, forceLength * 0.22, forceLength * 0.12) : null),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [showForce, forceLength]
  );

  useFrame((_, dt) => {
    if (animate) angleRef.current += dt * angularSpeed;
    const a = angleRef.current;
    const x = Math.cos(a) * orbitRadius;
    const z = Math.sin(a) * orbitRadius;
    if (satGroupRef.current) satGroupRef.current.position.set(x, 0, z);
    if (arrow) {
      arrow.position.set(x, 0, z);
      const dir = new THREE.Vector3(-x, 0, -z);
      if (dir.lengthSq() > 0) arrow.setDirection(dir.normalize());
    }
  });

  return (
    <group>
      <Orbit radius={orbitRadius} color={COLOR.faint} />
      <Sphere position={[0, 0, 0]} radius={centralRadius} color={COLOR.computed} />
      <Label position={[0, centralRadius + 0.3, 0]} text={params?.central?.label || 'Central body'} fontSize={0.18} />
      <group ref={satGroupRef} position={[orbitRadius, 0, 0]}>
        <Sphere position={[0, 0, 0]} radius={satelliteRadius} color={COLOR.structure} />
        <Label position={[0, satelliteRadius + 0.25, 0]} text={params?.satellite?.label || 'Satellite'} fontSize={0.15} />
      </group>
      {arrow && <primitive object={arrow} />}
    </group>
  );
}
