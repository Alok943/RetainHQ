import React from 'react';
import GlossaryTerm from '../GlossaryTerm';

/**
 * Core term matcher: plain prose in, array of strings and <GlossaryTerm> nodes
 * out. Matches each term at most once per lesson (tracked via the `used` Set).
 * Longest terms are matched first.
 */
function linkifyTerms(text, terms, used) {
  if (!text || !terms || terms.length === 0) return [text];

  // Sort terms longest-first to match multi-word terms before single words
  const sortedTerms = [...terms].sort((a, b) => b.term.length - a.term.length);

  for (const entry of sortedTerms) {
    const termLower = entry.term.toLowerCase();
    if (used.has(termLower)) continue;

    // Use word boundaries. Case insensitive.
    const escapedTerm = entry.term.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
    const regex = new RegExp(`\\b(${escapedTerm})\\b`, 'i');

    const match = text.match(regex);
    if (match) {
      used.add(termLower);
      const before = text.substring(0, match.index);
      const matchedText = match[1]; // preserve original case
      const after = text.substring(match.index + matchedText.length);

      const beforeNodes = linkifyTerms(before, terms, used);
      const afterNodes = linkifyTerms(after, terms, used);

      return [
        ...beforeNodes,
        <GlossaryTerm key={termLower} term={entry.term} definition={entry.definition} example={entry.example}>
          {matchedText}
        </GlossaryTerm>,
        ...afterNodes
      ];
    }
  }

  // No match found
  return [text];
}

/**
 * Inline renderer for lesson prose: `backtick spans` become styled <code>
 * chips, and everything else goes through the glossary term matcher. Glossary
 * matching is intentionally disabled inside code spans — `append()` should be
 * a code chip, not a tooltip link.
 */
export function linkifyGlossary(text, terms = [], used = new Set()) {
  if (!text) return [text];
  if (typeof text !== 'string') return [text];

  const parts = text.split(/(`[^`\n]+`)/g);
  if (parts.length === 1) return linkifyTerms(text, terms, used);

  return parts.flatMap((part, i) => {
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return [
        <code key={`c${i}`} className="font-mono text-[0.9em] text-[#0F172A] bg-[#0F172A]/[0.06] border border-[#0F172A]/[0.08] rounded px-1 py-px whitespace-nowrap">
          {part.slice(1, -1)}
        </code>
      ];
    }
    return linkifyTerms(part, terms, used);
  });
}

/**
 * @deprecated Do NOT use as a JSX component — React StrictMode double-invokes
 * each component independently, causing the shared `used` Set to be mutated in
 * the discarded first render so the second (kept) render sees terms as already
 * consumed and falls back to shorter/wrong matches.
 *
 * Call `linkifyGlossary(text, terms, used)` directly as a plain function instead.
 */
export function GlossaryText({ children, terms, used }) {
  if (typeof children !== 'string') return children;
  if (!terms || terms.length === 0) return children;
  return <>{linkifyGlossary(children, terms, used)}</>;
}
