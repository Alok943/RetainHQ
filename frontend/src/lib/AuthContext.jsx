import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from './supabase';
import AuthModal from '../AuthModal';

const AuthContext = createContext({
  session: null,
  loading: true,
  requireAuth: () => false,
  showAuthModal: () => {},
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);

  useEffect(() => {
    // Initial fetch
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    // Listen for changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setLoading(false);
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

  const requireAuth = (callback) => {
    if (session) {
      if (callback) callback();
      return true;
    } else {
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
