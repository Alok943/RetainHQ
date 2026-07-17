import React, { useState, useEffect } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

function cls(...classes) {
  return classes.filter(Boolean).join(' ');
}

function TeX({ expr }) {
  const html = katex.renderToString(expr, { throwOnError: false });
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

export default function DerivationPlayer({ block }) {
  const { goal, steps, rules } = block;
  const [revealedIdx, setRevealedIdx] = useState(0); 
  const [predictionMade, setPredictionMade] = useState(false);
  
  const currentStep = steps[revealedIdx];
  const hasPredict = currentStep && currentStep.predict && !predictionMade;
  
  const [selectedOption, setSelectedOption] = useState(null);
  const [showingWrongPath, setShowingWrongPath] = useState(false);
  const [wrongPathIdx, setWrongPathIdx] = useState(0);
  
  const handleNext = () => {
    if (revealedIdx < steps.length - 1) {
      setRevealedIdx(revealedIdx + 1);
      setPredictionMade(false);
      setSelectedOption(null);
      setShowingWrongPath(false);
      setWrongPathIdx(0);
    }
  };

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Enter' && !hasPredict && !showingWrongPath && revealedIdx < steps.length - 1) {
        handleNext();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [revealedIdx, hasPredict, showingWrongPath, steps.length]);

  return (
    <div className="my-6">
      <div className="bg-[#0F172A] text-white px-5 py-4 rounded-t-lg font-sans font-medium">
        Goal: {goal}
      </div>
      <div className="border border-t-0 border-[rgba(15,23,42,0.08)] rounded-b-lg p-5 overflow-hidden">
        
        {/* Revealed Steps */}
        <div className="flex flex-col gap-6">
          {steps.slice(0, revealedIdx + (hasPredict ? 0 : 1)).map((step, i) => {
            const isCurrent = i === revealedIdx;
            return (
              <div key={i} className={cls("flex flex-col transition-opacity", isCurrent && !hasPredict ? "opacity-100" : "opacity-60")}>
                <div className="overflow-x-auto pb-1 text-lg whitespace-nowrap">
                  <TeX expr={step.expr} />
                </div>
                <div className="text-sm text-[#64748B] mt-1 italic border-l-2 border-[#CBD5E1] pl-3">
                  {step.why}
                </div>
              </div>
            );
          })}
        </div>

        {/* Prediction Gate */}
        {hasPredict && !showingWrongPath && (
          <div className="bg-[#f8fafc] border border-[rgba(15,23,42,0.08)] rounded-lg p-5 mt-6">
            <h4 className="font-sans font-semibold text-[#0F172A] mb-3">Next Move</h4>
            <p className="font-sans text-sm text-[#334155] mb-4">{currentStep.predict.question}</p>
            <div className="flex flex-col gap-2">
              {currentStep.predict.options.map((opt, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setSelectedOption(i);
                    if (opt.correct) {
                      setPredictionMade(true);
                    } else {
                      setShowingWrongPath(true);
                      setWrongPathIdx(0);
                    }
                  }}
                  className="text-left px-4 py-3 rounded border bg-white border-[rgba(15,23,42,0.08)] text-[#334155] hover:border-[#0891B2] transition-colors overflow-x-auto"
                >
                  <TeX expr={opt.expr} />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Wrong Path Playback */}
        {showingWrongPath && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-5 mt-6">
            <h4 className="font-sans font-semibold text-red-900 mb-3">That leads to an error</h4>
            <div className="flex flex-col gap-4">
              {currentStep.predict.options[selectedOption].wrong_path?.slice(0, wrongPathIdx + 1).map((wexpr, i) => (
                <div key={i} className="overflow-x-auto text-lg text-red-950 whitespace-nowrap pb-1">
                  <TeX expr={wexpr} />
                </div>
              ))}
            </div>
            
            <div className="mt-4 flex items-center justify-between">
              {wrongPathIdx < (currentStep.predict.options[selectedOption].wrong_path?.length || 0) - 1 ? (
                <button
                  onClick={() => setWrongPathIdx(wrongPathIdx + 1)}
                  className="px-4 py-2 bg-red-100 text-red-900 rounded text-sm font-medium hover:bg-red-200"
                >
                  See what happens next
                </button>
              ) : (
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-800 mb-4 bg-red-100 p-3 rounded">
                    {currentStep.predict.options[selectedOption].feedback}
                  </p>
                  <button
                    onClick={() => {
                      setShowingWrongPath(false);
                      setSelectedOption(null);
                    }}
                    className="px-4 py-2 bg-red-900 text-white rounded text-sm font-medium hover:bg-red-950"
                  >
                    Rewind and try again
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Next Button */}
        {!hasPredict && !showingWrongPath && revealedIdx < steps.length - 1 && (
          <div className="mt-8 flex justify-end">
            <button
              onClick={handleNext}
              className="px-6 py-2 bg-[#0F172A] text-white rounded text-sm font-medium hover:bg-[#1E293B] shadow-sm flex items-center gap-2"
            >
              Next Step 
              <span className="text-xs opacity-50 font-normal border border-white/20 rounded px-1.5 py-0.5">Enter</span>
            </button>
          </div>
        )}

        {/* Completion Rules Recap */}
        {revealedIdx === steps.length - 1 && !hasPredict && (
          <div className="mt-8 pt-6 border-t border-[rgba(15,23,42,0.08)]">
            <h4 className="font-sans font-semibold text-[#0F172A] mb-4">Rules used in this derivation</h4>
            <ul className="space-y-3">
              {rules.map((rule, i) => (
                <li key={i} className="text-sm text-[#334155] flex items-start gap-3 bg-slate-50 p-3 rounded border border-slate-100">
                  <span className="font-mono text-xs font-semibold text-slate-400 mt-0.5">#{rule.id}</span>
                  <span>{rule.statement}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

      </div>
    </div>
  );
}
