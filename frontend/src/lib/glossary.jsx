import React from 'react';
import GlossaryTerm from '../GlossaryTerm';

/**
 * Given a plain string and a list of glossary terms, returns an array of strings
 * and <GlossaryTerm> components. Matches each term at most once per lesson
 * (tracked via the `used` Set). Longest terms are matched first.
 */
export function linkifyGlossary(text, terms = [], used = new Set()) {
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
    if (entry.term === 'keyword-only' || entry.term === 'positional-only') {
      console.log('[gd]', JSON.stringify(text.slice(0, 40)), entry.term, 'used?', used.has(termLower), 'match?', !!match);
    }
    if (match) {
      used.add(termLower);
      const before = text.substring(0, match.index);
      const matchedText = match[1]; // preserve original case
      const after = text.substring(match.index + matchedText.length);
      
      const beforeNodes = linkifyGlossary(before, terms, used);
      const afterNodes = linkifyGlossary(after, terms, used);
      
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
