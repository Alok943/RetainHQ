import { supabase } from './supabase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * A wrapper around native fetch that automatically attaches the Supabase JWT
 * as a Bearer token to every request.
 */
export const apiFetch = async (endpoint, options = {}) => {
  // optionalAuth: allow the call to proceed without a session (public reads,
  // e.g. roadmaps). The Bearer token is still attached when a session exists.
  const { optionalAuth = false, ...fetchOptions } = options;
  const { data: { session } } = await supabase.auth.getSession();

  if (!session && !optionalAuth) {
    console.error('No active session found, failing request.');
    throw new Error('Not authenticated');
  }

  const headers = {
    'Content-Type': 'application/json',
    ...fetchOptions.headers,
  };
  if (session) {
    headers['Authorization'] = `Bearer ${session.access_token}`;
  }

  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;

  const response = await fetch(url, {
    ...fetchOptions,
    headers
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `API request failed with status ${response.status}`);
  }

  return response.json();
};

export default apiFetch;
