import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from './supabase';
import AuthModal from '../AuthModal';
import { identifyUser, resetAnalytics, track, trackOnce, EVENTS } from './analytics';
import { setErrorUser, clearErrorUser } from './errors';

// A sign-in is a brand-new signup when the account was created essentially now
// (Supabase stamps created_at at first OAuth). Returning logins have an older
// created_at. 2-min window absorbs redirect/clock skew without catching day-2 logins.
function isFirstSignup(user) {
  if (!user?.created_at) return false;
  return Date.now() - new Date(user.created_at).getTime() < 2 * 60 * 1000;
}

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
const DEV_SESSION = { access_token: 'dev-bypass', user: { id: 'dev', email: 'aloksingh98541@gmail.com' } };

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
      if (_event === 'SIGNED_IN') {
        track(EVENTS.SIGNED_IN);
        // Fire signed_up once per new account (SIGNED_IN also fires on tab focus /
        // token refresh, so dedupe on the user id to avoid re-counting).
        if (isFirstSignup(session?.user)) {
          trackOnce(`signed_up:${session.user.id}`, EVENTS.SIGNED_UP);
        }
      }
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

  // A 401 mid-session means the JWT expired or was revoked — sign out so the
  // stale session doesn't keep silently failing every request behind it.
  useEffect(() => {
    if (DEV_AUTH_BYPASS) return;
    const onUnauthorized = () => supabase.auth.signOut();
    window.addEventListener('retainhq:unauthorized', onUnauthorized);
    return () => window.removeEventListener('retainhq:unauthorized', onUnauthorized);
  }, []);

  // Tie the PostHog person + Sentry user to the (pseudonymous) user id; reset on sign-out.
  useEffect(() => {
    if (session?.user?.id) {
      identifyUser(session.user.id);
      setErrorUser(session.user.id);
    } else {
      resetAnalytics();
      clearErrorUser();
    }
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
