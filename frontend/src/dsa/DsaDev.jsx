import { Suspense, lazy } from 'react';

// TEMPORARY dev harness for the DSA pilot — renders the Player standalone before the lesson
// kind + content-pipeline integration lands. Reachable at /dsa-dev. Remove once wired into LessonView.
const Player = lazy(() => import('./Player.jsx'));

const INVARIANTS = {
  'inv-subarray': 'We only ever touch indices within the current [lo..hi] range.',
  'inv-divide': 'Each split breaks the range into two halves to sort independently.',
  'inv-merge': 'Before each write, pick the smaller current front of the two sorted halves.',
  'inv-sorted': 'After this completes, the range [lo..hi] is fully sorted.',
};

export default function DsaDev() {
  return (
    <div className="max-w-3xl mx-auto w-full px-4 md:px-8 py-6">
      <h1 className="font-sans text-xl font-bold text-[#0F172A] mb-1">DSA pilot — Merge Sort</h1>
      <p className="font-sans text-sm text-[#64748B] mb-5">Dev harness for the execution-trace Player (ArrayViz + StateMachine + tweakable input).</p>
      <Suspense fallback={<div className="text-sm text-[#64748B]">Loading visualizer…</div>}>
        <Player generatorKey="merge-sort" defaultInput={[5, 2, 8, 1, 9, 3]} invariants={INVARIANTS} />
      </Suspense>
    </div>
  );
}
