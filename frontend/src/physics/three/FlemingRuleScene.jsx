import { useMemo } from 'react';
import { Vector, Highlight, Label, COLOR } from './primitives.jsx';
import { axisToVector, cross, normalize, vectorToAxisLabel } from './physicsUtils.js';

/**
 * `fleming-rule` — force on a conductor (left/motor) or induced current (right/dynamo).
 * Params: { rule: "left" | "right", field_direction, current_direction? , motion_direction? }
 *
 * Schema note (documented here because the PROMPT's single worked example only
 * covers the left-hand case): the two GIVEN axes differ by rule —
 *  - rule: "left"  (motor)  -> given `field_direction` (B) + `current_direction` (I),
 *                              computed = force_direction:  F-hat = I-hat x B-hat.
 *  - rule: "right" (dynamo) -> given `field_direction` (B) + `motion_direction` (v),
 *                              computed = current_direction: I-hat = v-hat x B-hat.
 * Both are the standard FBI / FBI-dynamo right-hand-rule cross products — see
 * three/__checks__.md for the canonical numeric examples this must match.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function computePhysics(params) {
  const rule = params?.rule === 'right' ? 'right' : 'left';
  const B = axisToVector(params?.field_direction);
  if (rule === 'left') {
    const I = axisToVector(params?.current_direction);
    const F = normalize(cross(I, B));
    return { rule, B, I, F, computedLabel: 'F', computedAxis: vectorToAxisLabel(F) };
  }
  const v = axisToVector(params?.motion_direction || params?.current_direction);
  const I = normalize(cross(v, B));
  return { rule, B, v, I, computedLabel: 'I', computedAxis: vectorToAxisLabel(I) };
}

export default function FlemingRuleScene({ params }) {
  const d = useMemo(() => computePhysics(params), [params]);
  const arrows = d.rule === 'left'
    ? [
        { dir: d.B, color: COLOR.structure, label: 'B', computed: false },
        { dir: d.I, color: COLOR.reaction, label: 'I', computed: false },
        { dir: d.F, color: COLOR.computed, label: d.computedLabel, computed: true },
      ]
    : [
        { dir: d.B, color: COLOR.structure, label: 'B', computed: false },
        { dir: d.v, color: COLOR.reaction, label: 'v', computed: false },
        { dir: d.I, color: COLOR.computed, label: d.computedLabel, computed: true },
      ];

  return (
    <group>
      {arrows.map((a, i) => (
        <group key={i}>
          <Vector origin={[0, 0, 0]} direction={a.dir} length={1.4} color={a.color} label={a.label} />
          {a.computed && <Highlight position={a.dir.map((x) => x * 1.55)} radius={0.22} color={COLOR.computed} />}
        </group>
      ))}
      <Label position={[0, -1.8, 0]} text={d.rule === 'left' ? "Left hand (motor): F = I x B" : 'Right hand (dynamo): I = v x B'} fontSize={0.14} color={COLOR.ink} />
    </group>
  );
}
