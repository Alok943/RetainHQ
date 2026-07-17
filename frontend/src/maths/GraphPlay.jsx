import React, { useState, useEffect } from 'react';
import { evaluate } from './evaluator';

function cls(...classes) {
  return classes.filter(Boolean).join(' ');
}

export default function GraphPlay({ block }) {
  const { mode, fn, a, predict } = block;
  const [predictionMade, setPredictionMade] = useState(false);
  const [selectedOption, setSelectedOption] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);
  
  if (predict && !predictionMade) {
    return (
      <div className="bg-[#f8fafc] border border-[rgba(15,23,42,0.08)] rounded-lg p-5 my-6">
        <h4 className="font-sans font-semibold text-[#0F172A] mb-3">Prediction</h4>
        <p className="font-sans text-sm text-[#334155] mb-4">{predict.question}</p>
        <div className="flex flex-col gap-2">
          {predict.options.map((opt, i) => (
            <button
              key={i}
              onClick={() => {
                setSelectedOption(i);
                setShowExplanation(true);
              }}
              className={cls(
                "text-left px-4 py-3 rounded border text-sm font-sans transition-colors",
                showExplanation 
                  ? (i === predict.answer 
                      ? "bg-green-50 border-green-200 text-green-900" 
                      : (i === selectedOption ? "bg-red-50 border-red-200 text-red-900" : "bg-white border-[rgba(15,23,42,0.08)] text-[#64748B] opacity-50"))
                  : "bg-white border-[rgba(15,23,42,0.08)] text-[#334155] hover:border-[#0891B2]"
              )}
              disabled={showExplanation}
            >
              {opt}
            </button>
          ))}
        </div>
        {showExplanation && (
          <div className="mt-4">
            <p className={cls("text-sm font-medium", selectedOption === predict.answer ? "text-green-700" : "text-red-700")}>
              {selectedOption === predict.answer ? "Correct!" : "Incorrect."}
            </p>
            <p className="text-sm text-[#475569] mt-1">{predict.why}</p>
            <button
              onClick={() => setPredictionMade(true)}
              className="mt-4 px-4 py-2 bg-[#0F172A] text-white rounded text-sm font-medium hover:bg-[#1E293B]"
            >
              Continue to Interactive Graph
            </button>
          </div>
        )}
      </div>
    );
  }

  return <GraphInteractive mode={mode} fn={fn} a={a} />;
}

function GraphInteractive({ mode, fn, a }) {
  const width = 360;
  const height = 240;
  const padding = 20;

  const xMin = a - 4;
  const xMax = a + 4;
  
  const points = [];
  const steps = 200;
  let yMin = Infinity;
  let yMax = -Infinity;

  for (let i = 0; i <= steps; i++) {
    const x = xMin + (i / steps) * (xMax - xMin);
    try {
      const y = evaluate(fn, x);
      if (Number.isFinite(y)) {
        points.push([x, y]);
        yMin = Math.min(yMin, y);
        yMax = Math.max(yMax, y);
      } else {
        points.push([x, null]);
      }
    } catch (e) {
      points.push([x, null]);
    }
  }

  if (yMin === Infinity) { yMin = -4; yMax = 4; }
  else if (yMax === yMin) { yMin -= 4; yMax += 4; }
  else {
    const p = (yMax - yMin) * 0.1;
    yMin -= p;
    yMax += p;
  }

  const mapX = (x) => padding + ((x - xMin) / (xMax - xMin)) * (width - 2 * padding);
  const mapY = (y) => height - padding - ((y - yMin) / (yMax - yMin)) * (height - 2 * padding);

  const segments = [];
  let currentSegment = [];
  for (const [x, y] of points) {
    if (y === null) {
      if (currentSegment.length > 0) {
        segments.push(currentSegment);
        currentSegment = [];
      }
    } else {
      currentSegment.push([mapX(x), mapY(y)]);
    }
  }
  if (currentSegment.length > 0) segments.push(currentSegment);

  const [animating, setAnimating] = useState(false);
  const [progress, setProgress] = useState(0); 
  const [h, setH] = useState(2); 

  useEffect(() => {
    let frame;
    if (animating && mode === 'limit') {
      let start = performance.now();
      const run = (now) => {
        let p = (now - start) / 3000;
        if (p > 1) p = 1;
        setProgress(p);
        if (p < 1) frame = requestAnimationFrame(run);
        else setAnimating(false);
      };
      frame = requestAnimationFrame(run);
    }
    return () => cancelAnimationFrame(frame);
  }, [animating, mode]);

  let overlay = null;
  let readout = null;

  if (mode === 'limit') {
    const xLeft = xMin + progress * (a - 0.01 - xMin);
    const xRight = xMax - progress * (xMax - a - 0.01);
    
    let yLeft = null, yRight = null;
    try { yLeft = evaluate(fn, xLeft); } catch(e){}
    try { yRight = evaluate(fn, xRight); } catch(e){}

    overlay = (
      <>
        {Number.isFinite(yLeft) && (
          <circle cx={mapX(xLeft)} cy={mapY(yLeft)} r={4} fill="#0891B2" />
        )}
        {Number.isFinite(yRight) && (
          <circle cx={mapX(xRight)} cy={mapY(yRight)} r={4} fill="#B45309" />
        )}
        {progress === 1 && (
          <circle cx={mapX(a)} cy={mapY(Number.isFinite(yLeft)?yLeft:0)} r={5} fill="none" stroke="#B91C1C" strokeWidth={2} />
        )}
      </>
    );

    readout = (
      <div className="mt-4 text-sm font-sans">
        <div className="flex justify-between items-center mb-2">
          <button 
            onClick={() => { setProgress(0); setAnimating(true); }}
            className="px-3 py-1.5 bg-[#0F172A] text-white rounded text-sm hover:bg-[#1E293B]"
          >
            Animate Limit
          </button>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-50 p-2 rounded border border-slate-200">
            <div className="text-xs text-slate-500 mb-1">Left Approach</div>
            <div>x: {xLeft.toFixed(3)}</div>
            <div>f(x): {Number.isFinite(yLeft) ? yLeft.toFixed(3) : 'undefined'}</div>
          </div>
          <div className="bg-slate-50 p-2 rounded border border-slate-200">
            <div className="text-xs text-slate-500 mb-1">Right Approach</div>
            <div>x: {xRight.toFixed(3)}</div>
            <div>f(x): {Number.isFinite(yRight) ? yRight.toFixed(3) : 'undefined'}</div>
          </div>
        </div>
      </div>
    );
  } else if (mode === 'secant-tangent') {
    let yA = null, yAH = null;
    try { yA = evaluate(fn, a); } catch(e){}
    try { yAH = evaluate(fn, a + h); } catch(e){}

    let slope = null;
    if (Number.isFinite(yA) && Number.isFinite(yAH)) {
      slope = (yAH - yA) / h;
    }

    if (Number.isFinite(yA) && Number.isFinite(yAH)) {
      const yL = slope * (xMin - a) + yA;
      const yR = slope * (xMax - a) + yA;
      
      overlay = (
        <>
          <line x1={mapX(xMin)} y1={mapY(yL)} x2={mapX(xMax)} y2={mapY(yR)} stroke="#0891B2" strokeWidth={2} strokeDasharray="4 4" />
          <circle cx={mapX(a)} cy={mapY(yA)} r={4} fill="#0F172A" />
          <circle cx={mapX(a + h)} cy={mapY(yAH)} r={4} fill="#B45309" />
        </>
      );
    }

    readout = (
      <div className="mt-4 text-sm font-sans flex flex-col gap-2">
        <label className="text-sm font-medium text-slate-700">
          h = {h.toFixed(3)}
        </label>
        <input 
          type="range" 
          min="0.01" 
          max="1.2599" 
          step="0.01" 
          value={Math.pow(h, 1/3)}
          onChange={(e) => setH(Math.pow(parseFloat(e.target.value), 3))}
          className="w-full"
        />
        <div className="bg-slate-50 p-2 rounded border border-slate-200 mt-2 font-mono text-xs">
          slope = (f(a+h) - f(a)) / h<br/>
          slope = {slope !== null ? slope.toFixed(4) : 'undefined'}
        </div>
      </div>
    );
  }

  return (
    <div className="my-6 border border-[rgba(15,23,42,0.08)] rounded-lg p-4 bg-white dark:bg-slate-900 shadow-sm">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto bg-slate-50 dark:bg-slate-800 rounded">
        <line x1={0} y1={mapY(0)} x2={width} y2={mapY(0)} stroke="#CBD5E1" strokeWidth={1} />
        <line x1={mapX(0)} y1={0} x2={mapX(0)} y2={height} stroke="#CBD5E1" strokeWidth={1} />
        
        {segments.map((seg, i) => {
          const d = seg.map((p, j) => (j === 0 ? `M ${p[0]} ${p[1]}` : `L ${p[0]} ${p[1]}`)).join(' ');
          return <path key={i} d={d} fill="none" stroke="#0F172A" strokeWidth={2} className="dark:stroke-slate-200" />;
        })}

        {overlay}
      </svg>
      {readout}
    </div>
  );
}
