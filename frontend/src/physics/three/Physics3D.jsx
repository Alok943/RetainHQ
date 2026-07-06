import { useState, useRef, useEffect, useMemo, Component } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Eye } from 'lucide-react';
import RayDiagram from '../RayDiagram.jsx';
import GraphDiagram from '../GraphDiagram.jsx';
import SchematicDiagram from '../SchematicDiagram.jsx';
import { lessonImageUrl } from '../../lib/assets';

import OrbitScene from './OrbitScene.jsx';
import MagneticFieldScene from './MagneticFieldScene.jsx';
import FlemingRuleScene from './FlemingRuleScene.jsx';
import EmInductionScene from './EmInductionScene.jsx';
import PrismScene from './PrismScene.jsx';
import LongitudinalWaveScene from './LongitudinalWaveScene.jsx';

/**
 * Physics3D — the ONE entry point for `diagram3d`. This module is always
 * `React.lazy`-imported by callers (LessonView.jsx / PhysicsNumericals.jsx) so
 * Three.js never touches a lesson that doesn't have a diagram3d block.
 *
 * Responsibilities (see content/PROMPT-physics-3d.md, guardrails section):
 *  - dispatch to a scene-kind component from the fixed 6-kind catalog
 *  - degrade to the `poster` 2D fallback (or caption text) when WebGL is
 *    unavailable, the device looks too weak, or the scene throws
 *  - drive the Predict -> (Manipulate) -> Observe -> Reflect interaction spine,
 *    reusing the app's reveal-button visual language
 *  - respect prefers-reduced-motion and pause when scrolled offscreen
 *  - dispose the GL context on unmount
 */

const SCENES = {
  orbit: OrbitScene,
  'magnetic-field': MagneticFieldScene,
  'fleming-rule': FlemingRuleScene,
  'em-induction': EmInductionScene,
  'dispersion-prism': PrismScene,
  'longitudinal-wave': LongitudinalWaveScene,
};

function useWebglSupported() {
  return useMemo(() => {
    try {
      const c = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl')));
    } catch {
      return false;
    }
  }, []);
}

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(
    () => typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  );
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handler = (e) => setReduced(e.matches);
    mq.addEventListener?.('change', handler);
    return () => mq.removeEventListener?.('change', handler);
  }, []);
  return reduced;
}

function useLowEndDevice() {
  return useMemo(() => {
    if (typeof navigator === 'undefined') return false;
    const coarse = !!window.matchMedia?.('(pointer: coarse)').matches;
    const lowCores = (navigator.hardwareConcurrency || 8) <= 4;
    return coarse && lowCores;
  }, []);
}

function useOffscreen(ref) {
  const [offscreen, setOffscreen] = useState(false);
  useEffect(() => {
    if (!ref.current || typeof IntersectionObserver === 'undefined') return;
    const obs = new IntersectionObserver(([entry]) => setOffscreen(!entry.isIntersecting), { threshold: 0.1 });
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, [ref]);
  return offscreen;
}

class Physics3DErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error) {
    console.error('[Physics3D] scene crashed, falling back to poster:', error);
    this.props.onError?.();
  }
  render() {
    return this.state.hasError ? this.props.fallback : this.props.children;
  }
}

/** `poster` is an existing 2D diagram object (ray/graph/schematic/image) or, if
 *  absent, the caption text in a bordered card — never a blank space. */
function PosterFallback({ diagram3d }) {
  const poster = diagram3d?.poster;
  if (poster && typeof poster === 'object') {
    if (poster.type === 'ray') return <RayDiagram diagram={poster} />;
    if (poster.type === 'graph') return <GraphDiagram diagram={poster} />;
    if (poster.type === 'schematic') return <SchematicDiagram diagram={poster} />;
    if (poster.type === 'image') {
      const url = lessonImageUrl(poster.asset);
      if (url) {
        return <img src={url} alt={poster.alt || ''} className="w-full rounded-lg border border-[rgba(15,23,42,0.1)] bg-white" />;
      }
    }
  }
  return (
    <div className="rounded-lg border border-[rgba(15,23,42,0.12)] bg-[#f9f9f6] p-4">
      <span className="font-sans text-[12.5px] text-[#0F172A] leading-snug">
        {diagram3d?.caption || 'This concept has an interactive 3D view — unavailable on this device.'}
      </span>
    </div>
  );
}

function PredictionPanel({ prediction, chosen, onChoose, onContinue }) {
  const committed = chosen !== null;
  const correct = committed && chosen === prediction.answer;
  return (
    <div className="px-3.5 py-3 border-b border-[rgba(15,23,42,0.08)] bg-[#0891B2]/[0.04]">
      <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#0891B2] mb-1.5">Predict first</div>
      <p className="font-sans text-sm font-medium text-[#0F172A] leading-relaxed mb-2.5">{prediction.question}</p>
      {!committed ? (
        <div className="flex flex-col gap-1.5">
          {prediction.choices.map((c, i) => (
            <button
              key={i}
              onClick={() => onChoose(i)}
              className="text-left text-[13px] font-medium text-[#0F172A] bg-white border border-[rgba(15,23,42,0.12)] rounded px-3 py-1.5 hover:border-[#0891B2] hover:bg-[#0891B2]/5 transition-colors"
            >
              {c}
            </button>
          ))}
        </div>
      ) : (
        <div className="animate-in fade-in duration-200">
          <div className={`rounded-lg border p-2.5 mb-2.5 ${correct ? 'border-[#0F766E]/25 bg-[#0F766E]/[0.06]' : 'border-[#B45309]/25 bg-[#B45309]/[0.06]'}`}>
            <p className="font-sans text-[12.5px] font-semibold mb-1" style={{ color: correct ? '#0F766E' : '#B45309' }}>
              {correct ? 'Correct.' : `Not quite — the answer is "${prediction.choices[prediction.answer]}".`}
            </p>
            {prediction.explains && <p className="font-sans text-[12.5px] text-[#0F172A] leading-relaxed">{prediction.explains}</p>}
          </div>
          <button onClick={onContinue} className="flex items-center gap-2 text-[13px] font-semibold text-white bg-[#0891B2] hover:bg-[#0e7490] rounded px-3 py-1.5 transition-colors">
            <Eye size={14} /> Watch it happen
          </button>
        </div>
      )}
    </div>
  );
}

function ManipulateControls({ manipulate, value, onChange }) {
  return (
    <div className="px-3 py-2.5 border-t border-[rgba(15,23,42,0.06)] bg-white flex flex-wrap items-center gap-2">
      {manipulate.prompt && <span className="font-sans text-[12px] text-[#475569] mr-1">{manipulate.prompt}</span>}
      {manipulate.options.map((opt) => (
        <button
          key={opt}
          onClick={() => onChange(opt)}
          className={`text-[12px] font-semibold rounded-full px-3 py-1 border transition-colors ${
            value === opt ? 'bg-[#0891B2] text-white border-[#0891B2]' : 'bg-white text-[#0891B2] border-[#0891B2]/40 hover:bg-[#0891B2]/5'
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

function ReflectionPanel({ reflection, revealed, onReveal }) {
  return (
    <div className="px-3.5 py-3 border-t border-[rgba(15,23,42,0.08)] bg-[#7C3AED]/[0.04]">
      <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#7C3AED] mb-1.5">Reflect</div>
      <p className="font-sans text-sm font-medium text-[#0F172A] leading-relaxed mb-2.5">{reflection.prompt}</p>
      {!revealed ? (
        <button onClick={onReveal} className="flex items-center gap-2 text-[13px] font-semibold text-white bg-[#7C3AED] hover:bg-[#6D28D9] rounded px-3 py-1.5 transition-colors">
          <Eye size={14} /> Reveal
        </button>
      ) : (
        <p className="font-sans text-[13px] text-[#0F172A] leading-relaxed animate-in fade-in duration-200">{reflection.answer}</p>
      )}
    </div>
  );
}

export default function Physics3D({ diagram3d }) {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
  const [crashed, setCrashed] = useState(false);

  const webglOk = useWebglSupported();
  const lowEnd = useLowEndDevice();
  const reducedMotion = usePrefersReducedMotion();
  const offscreen = useOffscreen(containerRef);

  const hasPrediction = !!diagram3d?.prediction;
  const hasManipulate = !!diagram3d?.manipulate;
  const hasReflection = !!diagram3d?.reflection;

  const [stage, setStage] = useState(hasPrediction ? 'predict' : 'observe');
  const [chosen, setChosen] = useState(null);
  const [manipulateValue, setManipulateValue] = useState(() =>
    hasManipulate ? diagram3d[diagram3d.manipulate.param] : undefined
  );
  const [reflectRevealed, setReflectRevealed] = useState(false);

  // Dispose the GL context + scene resources on unmount — a leaked WebGL
  // context per lesson visited is the classic mobile-crash failure mode.
  useEffect(() => {
    return () => {
      rendererRef.current?.forceContextLoss?.();
      rendererRef.current?.dispose?.();
      rendererRef.current = null;
    };
  }, []);

  const valid = !!diagram3d && typeof diagram3d === 'object' && !!diagram3d.scene;
  const SceneComponent = valid ? SCENES[diagram3d.scene] : null;
  const use3D = webglOk && !lowEnd && !crashed && !!SceneComponent;
  const animate = stage !== 'predict' && !reducedMotion && !offscreen;

  // Hooks must run unconditionally every render, so the "is this even a valid
  // diagram3d" bail-out happens AFTER every hook call, not before (an early
  // return before a hook here would violate the rules of hooks).
  const sceneParams = useMemo(() => {
    if (!valid) return null;
    if (!hasManipulate) return diagram3d;
    return { ...diagram3d, [diagram3d.manipulate.param]: manipulateValue };
  }, [valid, diagram3d, hasManipulate, manipulateValue]);

  if (!valid) return null;

  return (
    <div ref={containerRef} className="rounded-lg border border-[rgba(15,23,42,0.12)] bg-white overflow-hidden">
      {hasPrediction && stage === 'predict' && (
        <PredictionPanel
          prediction={diagram3d.prediction}
          chosen={chosen}
          onChoose={setChosen}
          onContinue={() => setStage('observe')}
        />
      )}

      <div style={{ height: 320 }} className="relative">
        {use3D ? (
          <Physics3DErrorBoundary fallback={<div className="p-3 h-full overflow-auto"><PosterFallback diagram3d={diagram3d} /></div>} onError={() => setCrashed(true)}>
            <Canvas
              dpr={[1, 2]}
              shadows={false}
              gl={{ antialias: true, powerPreference: 'low-power' }}
              camera={{ position: [2.6, 1.9, 3.2], fov: 42 }}
              frameloop={offscreen ? 'never' : 'always'}
              onCreated={({ gl }) => {
                rendererRef.current = gl;
              }}
            >
              <ambientLight intensity={0.65} />
              <directionalLight position={[3, 4, 2]} intensity={0.75} />
              <SceneComponent params={sceneParams} animate={animate} />
              <OrbitControls enableZoom={false} enableDamping dampingFactor={0.08} autoRotate={false} />
            </Canvas>
          </Physics3DErrorBoundary>
        ) : (
          <div className="p-3 h-full overflow-auto">
            <PosterFallback diagram3d={diagram3d} />
          </div>
        )}
      </div>

      {hasManipulate && stage !== 'predict' && (
        <ManipulateControls manipulate={diagram3d.manipulate} value={manipulateValue} onChange={setManipulateValue} />
      )}

      {diagram3d.caption && (
        <div className="px-3 py-2.5 border-t border-[rgba(15,23,42,0.06)] bg-[#f9f9f6]">
          <span className="font-sans text-[12.5px] text-[#0F172A] leading-snug">{diagram3d.caption}</span>
        </div>
      )}

      {hasReflection && stage !== 'predict' && (
        <ReflectionPanel reflection={diagram3d.reflection} revealed={reflectRevealed} onReveal={() => setReflectRevealed(true)} />
      )}
    </div>
  );
}
