import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiFetch } from './api';
import { useAuth } from './AuthContext';

// Shared cache for GET /api/classrooms/mine — the endpoint that decides the
// "Teach" nav entry and backs Teach / Profile / TeachClassroom. Each of those
// used to fetch it independently, and the nav re-fetched it on every route
// change, so a single page load hit the endpoint 2x and every navigation
// re-hit it (~1s each on Render's free tier). This fetches once per session and
// only refetches when a classroom is created or left (call refresh()).

const ClassroomsContext = createContext({
  classrooms: null,   // { teaching, enrolled } | null while loading / unauthed
  loading: true,
  error: null,
  refresh: () => {},
});

export const useClassrooms = () => useContext(ClassroomsContext);

export function ClassroomsProvider({ children }) {
  const { session } = useAuth();
  const [classrooms, setClassrooms] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(() => {
    if (!session) {
      setClassrooms(null);
      setError(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    return apiFetch('/api/classrooms/mine')
      .then((d) => { setClassrooms(d); setError(null); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [session]);

  // Fetch once when the session appears (and clear on sign-out). Route changes
  // deliberately do NOT retrigger this — classroom membership only changes via
  // create/leave, which call refresh() themselves.
  useEffect(() => { refresh(); }, [refresh]);

  return (
    <ClassroomsContext.Provider value={{ classrooms, loading, error, refresh }}>
      {children}
    </ClassroomsContext.Provider>
  );
}
