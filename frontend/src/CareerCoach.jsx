import React, { useEffect, useState, useCallback } from 'react';
import { apiFetch } from './lib/api';
import { useSeo } from './lib/useSeo';
import CareerOnboarding from './CareerOnboarding';
import CareerTree from './CareerTree';

// Entry point for Career Coach Phase 2 (SPEC-career-coach-phase2.md §8).
// Router, not a page: shows the onboarding wizard until a goal has a
// committed tree (goal.roadmap_id set), then the tree view.
function CareerCoach() {
  useSeo(
    'Career Coach — build your job-ready tree | RetainHQ',
    'Pick a role, take a 5-minute diagnostic, and get a tree of exactly what to study next — tracked with the same evidence engine as everything else in RetainHQ.'
  );

  const [loading, setLoading] = useState(true);
  const [goal, setGoal] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    apiFetch('/api/career/goals/active')
      .then(setGoal)
      .catch((err) => {
        if (err.status === 404) setGoal(null);
        else throw err;
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto w-full p-4 md:p-8 flex flex-col gap-4">
        <div className="skeleton h-6 w-48" />
        <div className="skeleton h-3 w-72" />
        <div className="skeleton h-32 w-full rounded-3xl mt-2" />
      </div>
    );
  }

  if (goal && goal.roadmap_id) {
    return <CareerTree goal={goal} onGoalChanged={load} />;
  }

  return <CareerOnboarding existingGoal={goal} onCommitted={load} />;
}

export default CareerCoach;
