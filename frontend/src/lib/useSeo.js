import { useEffect } from 'react';

/**
 * Per-route SEO metadata for the SPA.
 *
 * Rendering <title>/<meta> via React 19's native hoisting leaves the static
 * index.html tags in place too — producing duplicate <title>/<meta name=
 * "description"> where the generic one often wins. So instead we mutate the
 * single existing tags imperatively and restore the defaults on unmount, so the
 * landing page (static index.html) keeps its tags and every route shows exactly
 * one correct title + description. Googlebot renders JS, so it reads these.
 *
 * Pass null/undefined while data is still loading — the defaults stay untouched.
 */
export function useSeo(title, description) {
  useEffect(() => {
    if (!title && !description) return;

    const prevTitle = document.title;
    const metaEl = document.querySelector('head meta[name="description"]');
    const prevDesc = metaEl ? metaEl.getAttribute('content') : null;

    if (title) document.title = title;
    if (metaEl && description) metaEl.setAttribute('content', description);

    return () => {
      document.title = prevTitle;
      if (metaEl && prevDesc != null) metaEl.setAttribute('content', prevDesc);
    };
  }, [title, description]);
}
