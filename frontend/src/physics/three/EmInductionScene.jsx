import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { Cylinder, Label, COLOR } from './primitives.jsx';

/**
 * `em-induction` — magnet moving through a coil; induced current obeys Lenz's law.
 * Params: { motion: "insert" | "withdraw", magnet_pole: "N" | "S" }
 *
 * Physics (pure): the approaching pole sets the sign of the flux the magnet
 * contributes through the coil (`poleFieldSign`, N -> +y i.e. field points away
 * from N through the coil). Lenz's law: induced current opposes the CHANGE in
 * flux, so on insertion (flux magnitude increasing) the induced coil field is
 * the OPPOSITE sign; on withdrawal (flux decreasing) the induced field
 * reinforces (same sign), trying to maintain it. `coilCurrentTangent(phi)` then
 * converts the required coil field sign into a physical current direction using
 * the standard solenoid right-hand rule: current going counter-clockwise viewed
 * from +y produces B along +y at the coil's centre.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function computePhysics(params) {
  const motion = params?.motion === 'withdraw' ? 'withdraw' : 'insert';
  const pole = params?.magnet_pole === 'S' ? 'S' : 'N';
  const poleFieldSign = pole === 'N' ? 1 : -1;
  const inducedFieldSign = motion === 'insert' ? -poleFieldSign : poleFieldSign;
  // tangent(phi) for CCW-viewed-from+y (B -> +y): (-sin, 0, cos); flip for -y.
  const coilCurrentTangent = (phi) => {
    const ccw = [-Math.sin(phi), 0, Math.cos(phi)];
    return inducedFieldSign >= 0 ? ccw : ccw.map((c) => -c);
  };
  return { motion, pole, poleFieldSign, inducedFieldSign, coilCurrentTangent };
}

const COIL_Y = 0;
const COIL_R = 0.55;
const TRAVEL = 1.9; // magnet travels from |TRAVEL| to 0 (insert) or reverse (withdraw)

export default function EmInductionScene({ params, animate }) {
  const d = useMemo(() => computePhysics(params), [params]);
  const magnetRef = useRef();
  const tRef = useRef(0);

  const arrowMarkers = useMemo(() => {
    const n = 6;
    return Array.from({ length: n }, (_, i) => {
      const phi = (i / n) * Math.PI * 2;
      const pos = [Math.cos(phi) * COIL_R, COIL_Y, Math.sin(phi) * COIL_R];
      const tangent = d.coilCurrentTangent(phi);
      return { pos, tangent };
    });
  }, [d]);

  const arrowHelpers = useMemo(
    () => arrowMarkers.map((m) => new THREE.ArrowHelper(new THREE.Vector3(...m.tangent), new THREE.Vector3(...m.pos), 0.28, COLOR.computed, 0.09, 0.06)),
    [arrowMarkers]
  );

  useFrame((_, dt) => {
    if (animate) tRef.current = (tRef.current + dt * 0.35) % 1; // one pass ~2.8s
    // insert: from -TRAVEL (outside, below) to 0 (centre). withdraw: reverse.
    const from = d.motion === 'insert' ? -TRAVEL : 0;
    const to = d.motion === 'insert' ? 0 : -TRAVEL;
    const y = from + (to - from) * tRef.current;
    if (magnetRef.current) magnetRef.current.position.y = y;
  });

  return (
    <group>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[COIL_R, 0.05, 12, 48]} />
        <meshStandardMaterial color={COLOR.structure} />
      </mesh>
      {arrowHelpers.map((h, i) => (
        <primitive key={i} object={h} />
      ))}
      {/* `magnet_pole` is the LEADING pole — the one facing the coil as the magnet
          travels upward through it — so it sits at the bottom of the bar. */}
      <group ref={magnetRef} position={[0, d.motion === 'insert' ? -TRAVEL : 0, 0]}>
        <Cylinder position={[0, -0.35, 0]} radius={0.22} height={0.7} color={d.pole === 'N' ? COLOR.reaction : COLOR.structure} />
        <Cylinder position={[0, 0.35, 0]} radius={0.22} height={0.7} color={d.pole === 'N' ? COLOR.structure : COLOR.reaction} />
        <Label position={[0.35, -0.35, 0]} text={d.pole} fontSize={0.16} color={d.pole === 'N' ? COLOR.reaction : COLOR.structure} />
        <Label position={[0.35, 0.35, 0]} text={d.pole === 'N' ? 'S' : 'N'} fontSize={0.16} color={d.pole === 'N' ? COLOR.structure : COLOR.reaction} />
      </group>
    </group>
  );
}
