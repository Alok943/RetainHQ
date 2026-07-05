import { useEffect } from 'react';

const SITE = 'https://retainhq.app';

/**
 * Per-route SEO metadata for the SPA.
 *
 * Rendering <title>/<meta> via React 19's native hoisting leaves the static
 * index.html tags in place too — producing duplicates where the generic one
 * often wins. So we mutate the single existing tags imperatively and restore the
 * defaults on unmount: the landing page (static index.html) keeps its tags, and
 * every route shows exactly one correct title/description/canonical. Googlebot
 * renders JS, so it reads these.
 *
 * Also sets a **self-referencing canonical** per route. Without this every SPA
 * page inherits index.html's homepage canonical, which tells Google the page is
 * a duplicate of the homepage and can keep it out of the index entirely.
 *
 * Optional `jsonLd` (object or array) is injected as a route-scoped
 * <script type="application/ld+json"> and removed on unmount.
 *
 * Pass null/undefined while data is still loading — the defaults stay untouched.
 */
export function useSeo(title, description, jsonLd) {
  const ldKey = jsonLd ? JSON.stringify(jsonLd) : null;

  useEffect(() => {
    if (!title && !description && !ldKey) return;

    const head = document.head;
    const prevTitle = document.title;
    const metaEl = head.querySelector('meta[name="description"]');
    const prevDesc = metaEl ? metaEl.getAttribute('content') : null;
    const canonicalEl = head.querySelector('link[rel="canonical"]');
    const prevCanonical = canonicalEl ? canonicalEl.getAttribute('href') : null;
    const selfUrl = SITE + window.location.pathname;

    if (title) document.title = title;
    if (metaEl && description) metaEl.setAttribute('content', description);
    if (canonicalEl) canonicalEl.setAttribute('href', selfUrl);

    let ldEl = null;
    if (ldKey) {
      ldEl = document.createElement('script');
      ldEl.type = 'application/ld+json';
      ldEl.textContent = ldKey;
      head.appendChild(ldEl);
    }

    return () => {
      document.title = prevTitle;
      if (metaEl && prevDesc != null) metaEl.setAttribute('content', prevDesc);
      if (canonicalEl && prevCanonical != null) canonicalEl.setAttribute('href', prevCanonical);
      if (ldEl) ldEl.remove();
    };
  }, [title, description, ldKey]);
}
