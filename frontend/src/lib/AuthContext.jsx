import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from './supabase';
import AuthModal from '../AuthModal';
import { identifyUser, resetAnalytics, track, EVENTS } from './analytics';

const AuthContext = createContext({
  session: null,
  loading: true,
  requireAuth: () => false,
  showAuthModal: () => {},
});

export const useAuth = () => useContext(AuthContext);

// DEV ONLY: pretend we're signed in locally so the authenticated app renders
// without Google OAuth. `import.meta.env.DEV` is false in production builds, so
// this is dead-code-eliminated from any deployed bundle — it cannot ship.
const DEV_AUTH_BYPASS =
  import.meta.env.DEV && import.meta.env.VITE_DEV_AUTH_BYPASS === 'true';
const DEV_SESSION = { access_token: 'dev-bypass', user: { id: 'dev', email: 'dev@localhost' } };

export function AuthProvider({ children }) {
  const [session, setSession] = useState(DEV_AUTH_BYPASS ? DEV_SESSION : null);
  const [loading, setLoading] = useState(!DEV_AUTH_BYPASS);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);

  useEffect(() => {
    // Dev bypass: skip all Supabase auth wiring.
    if (DEV_AUTH_BYPASS) return;

    // Initial fetch
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    // Listen for changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setLoading(false);
      if (_event === 'SIGNED_IN') track(EVENTS.SIGNED_IN);
      if (session && isModalOpen) {
        setIsModalOpen(false);
        if (pendingAction) {
          pendingAction();
          setPendingAction(null);
        }
      }
    });

    return () => subscription.unsubscribe();
  }, [isModalOpen, pendingAction]);

  // Tie the PostHog person to the (pseudonymous) user id; reset on sign-out.
  useEffect(() => {
    if (session?.user?.id) identifyUser(session.user.id);
    else resetAnalytics();
  }, [session?.user?.id]);

  const requireAuth = (callback) => {
    if (session) {
      if (callback) callback();
      return true;
    } else {
      track(EVENTS.AUTH_WALL_HIT); // guest hit a write that needs an account
      setPendingAction(() => callback);
      setIsModalOpen(true);
      return false;
    }
  };

  const showAuthModal = () => setIsModalOpen(true);

  return (
    <AuthContext.Provider value={{ session, loading, requireAuth, showAuthModal }}>
      {children}
      {isModalOpen && (
        <AuthModal onClose={() => {
          setIsModalOpen(false);
          setPendingAction(null);
        }} />
      )}
    </AuthContext.Provider>
  );
}
