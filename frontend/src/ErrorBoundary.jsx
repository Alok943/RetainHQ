import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { captureError } from './lib/errors';

// Custom class component — NOT Sentry.ErrorBoundary — so the fallback renders
// even when Sentry is off (captureError itself no-ops without a DSN).
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    captureError(error, { componentStack: info?.componentStack });
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className="min-h-screen w-full flex items-center justify-center p-4 bg-[#f9f9f6]">
        <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-8 max-w-sm w-full flex flex-col items-center text-center gap-4">
          <div className="w-12 h-12 rounded-full bg-[#ba1a1a]/10 flex items-center justify-center">
            <AlertTriangle size={22} className="text-[#ba1a1a]" />
          </div>
          <div>
            <h2 className="font-sans text-lg font-semibold text-[#0F172A]">Something went wrong</h2>
            <p className="font-sans text-sm text-[#64748B] mt-1.5 leading-relaxed">
              This screen hit an unexpected error. Reloading usually fixes it — your progress
              is saved on the server, not lost.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 w-full mt-2">
            <button
              onClick={() => { window.location.href = '/dashboard'; }}
              className="kinetic-btn bg-white border border-[rgba(15,23,42,0.15)] text-[#0F172A] px-5 py-2.5 text-sm flex-1"
            >
              Back to dashboard
            </button>
            <button
              onClick={() => window.location.reload()}
              className="kinetic-btn kinetic-accent-gradient px-5 py-2.5 text-sm flex-1"
            >
              Reload
            </button>
          </div>
        </div>
      </div>
    );
  }
}
