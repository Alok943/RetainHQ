import { Component } from 'react';
import { MAIN_RENDERERS } from './dsa/renderers';

// Complete-binary-tree array indexing (index i -> children at 2i+1/2i+2, null = absent
// node) — the same convention already used when authoring v2 recall_questions content
// (see content/PROMPT-recall-v2.md). x is assigned by in-order rank so siblings never
// overlap; TreeViz has no auto-layout fallback of its own (unlike GraphViz), so this is
// required, not optional.
const TREE_X_SPACING = 56;
const TREE_Y_SPACING = 64;

function buildArrayFrame(context) {
  // ArrayViz's `regions`/`pointers` carry algorithm-specific meaning (a "left"/"right"
  // partition half, a named two-pointer). A generic highlighted index doesn't mean any
  // of those, so it's rendered via `sorted` — the one single-color highlight ArrayViz
  // offers that doesn't imply a specific algorithmic role. Custom label text (if any)
  // is rendered as a caption below the bars instead of fighting the renderer's fixed
  // pointer-name labels (i/j/lo/hi/...).
  return {
    array: context.values,
    sorted: Array.isArray(context.highlight) ? context.highlight : [],
  };
}

function buildTreeFrame(context) {
  const levelOrder = context.level_order;
  const nodes = {};
  let xCounter = 0;

  function build(i, depth) {
    if (i >= levelOrder.length || levelOrder[i] == null) return null;
    const leftId = build(2 * i + 1, depth + 1); // in-order: left first, so x grows left-to-right
    const id = String(i);
    const node = { id, value: levelOrder[i], x: xCounter * TREE_X_SPACING, y: depth * TREE_Y_SPACING };
    xCounter += 1;
    if (leftId) node.left = leftId;
    const rightId = build(2 * i + 2, depth + 1);
    if (rightId) node.right = rightId;
    nodes[id] = node;
    return id;
  }
  build(0, 0);
  return { tree: { nodes } };
}

function buildGraphFrame(context) {
  const nodes = (context.nodes || []).map((n) =>
    n && typeof n === 'object' ? n : { id: n, value: n }
  );
  const edges = (context.edges || []).map((e) =>
    Array.isArray(e)
      ? { u: e[0], v: e[1], directed: !!context.directed }
      : { ...e, directed: e.directed ?? !!context.directed }
  );
  return { graph: { nodes }, edges };
}

// Matches SqlResult.jsx's (unexported) ResultTable styling exactly, so a static table here
// and a live query result elsewhere read as the same component to the eye. `rows` are
// positional arrays (matches the recall_questions v2 context contract), not column-keyed
// objects like SqlResult's live query rows.
function StaticTable({ name, columns, rows }) {
  return (
    <div className="overflow-x-auto rounded-md border border-[rgba(15,23,42,0.1)]">
      {name && (
        <div className="px-3 py-1 bg-[#f9f9f6] border-b border-[rgba(15,23,42,0.08)] font-sans text-[10px] font-semibold uppercase tracking-wide text-[#64748B]">
          {name}
        </div>
      )}
      <table className="w-full border-collapse font-mono text-[12px]">
        <thead>
          <tr className="bg-[#f1f5f9]">
            {columns.map((c, i) => (
              <th key={i} className="text-left font-semibold text-[#0F766E] px-3 py-1.5 border-b border-[rgba(15,23,42,0.1)] whitespace-nowrap">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 ? 'bg-[rgba(15,23,42,0.02)]' : ''}>
              {row.map((v, j) => (
                <td key={j} className="px-3 py-1.5 text-[#0F172A] border-b border-[rgba(15,23,42,0.05)] whitespace-nowrap">
                  {v === null || v === undefined ? <span className="text-[#cbd5e1] italic">NULL</span> : String(v)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Matches CodeTrace.jsx's static (non-active-line) pane styling — same "editor" panel
// look used everywhere else code appears in the app.
function CodeBlock({ lang, source }) {
  const lines = source.replace(/\n$/, '').split('\n');
  return (
    <div className="rounded-md overflow-hidden border border-[rgba(15,23,42,0.1)]">
      {lang && (
        <div className="px-3 py-1 bg-[#f9f9f6] border-b border-[rgba(15,23,42,0.08)] font-sans text-[10px] font-semibold uppercase tracking-wide text-[#64748B]">
          {lang}
        </div>
      )}
      <pre className="m-0 p-3 text-[12.5px] leading-relaxed font-mono overflow-x-auto bg-[#0b1220] text-[#e2e8f0]">
        {lines.map((ln, i) => (
          <div key={i}>
            <span className="inline-block w-6 text-right mr-3 text-[#475569] select-none">{i + 1}</span>
            {ln || ' '}
          </div>
        ))}
      </pre>
    </div>
  );
}

// React only defers work wrapped in an actual component's render to the tree an error
// boundary protects — a plain try/catch around JSX in QuestionContext's own function body
// would NOT catch a throw from ArrayViz/TreeViz/GraphViz, since JSX construction doesn't
// execute a component until React renders it (react-hooks/error-boundaries lint rule).
// This boundary is what actually makes "malformed context never crashes the review flow" true.
class ContextErrorBoundary extends Component {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error) {
    console.error('QuestionContext failed to render — showing nothing instead:', error);
  }
  componentDidUpdate(prevProps) {
    // Without this, a boundary that ever trips stays tripped: this component
    // instance persists across review cards, so one card's malformed context
    // would silently blank out context for every card served after it.
    if (this.state.hasError && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ hasError: false });
    }
  }
  render() {
    return this.state.hasError ? null : this.props.children;
  }
}

function ContextBody({ context }) {
  switch (context.type) {
    case 'array': {
      if (!Array.isArray(context.values) || context.values.length === 0) return null;
      const Renderer = MAIN_RENDERERS.array;
      const labelEntries = context.labels ? Object.entries(context.labels) : [];
      return (
        <div className="my-2">
          <Renderer frame={buildArrayFrame(context)} />
          {labelEntries.length > 0 && (
            <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-1.5">
              {labelEntries.map(([idx, text]) => (
                <span key={idx} className="font-sans text-[11px] text-[#64748B]">
                  <span className="font-mono text-[#0F766E]">[{idx}]</span> {text}
                </span>
              ))}
            </div>
          )}
        </div>
      );
    }

    case 'tree': {
      if (!Array.isArray(context.level_order) || context.level_order.length === 0) return null;
      const Renderer = MAIN_RENDERERS.tree;
      return (
        // No fixed height: TreeViz's <svg> has no `height` attribute of its own, only a
        // viewBox, so it scales to whatever height its own aspect ratio needs at this
        // width — a fixed pixel height here would either crop it or (as found in-browser)
        // let it overflow into the next block, since a block div's height doesn't clip
        // an overflowing child by default.
        <div className="my-2 flex justify-center">
          <div className="w-full max-w-xs">
            <Renderer frame={buildTreeFrame(context)} />
          </div>
        </div>
      );
    }

    case 'graph': {
      if (!Array.isArray(context.nodes) || context.nodes.length === 0) return null;
      const Renderer = MAIN_RENDERERS.graph;
      return (
        <div className="my-2 flex justify-center">
          <div className="w-full max-w-md">
            <Renderer frame={buildGraphFrame(context)} />
          </div>
        </div>
      );
    }

    case 'table': {
      const tables = Array.isArray(context.tables)
        ? context.tables
        : Array.isArray(context.columns) && Array.isArray(context.rows)
        ? [{ name: null, columns: context.columns, rows: context.rows }]
        : [];
      if (tables.length === 0) return null;
      return (
        <div className="my-2 flex flex-col gap-3">
          {tables.map((t, i) => (
            <StaticTable key={i} name={t.name} columns={t.columns} rows={t.rows} />
          ))}
        </div>
      );
    }

    case 'code': {
      if (!context.source) return null;
      return (
        <div className="my-2">
          <CodeBlock lang={context.lang} source={context.source} />
        </div>
      );
    }

    default:
      return null;
  }
}

/**
 * Renders a recall_questions v2 `context` block (docs/IMPLEMENTATION-quiz-capture-v2.md
 * Step 4) on a review card — one static frame, no player/step controls, reusing the
 * existing DSA renderers (array/tree/graph) and matching SqlResult's table + CodeTrace's
 * code styling exactly rather than inventing a new look. An unknown type, or malformed
 * data for a known type, renders nothing — a bad context block must never crash the
 * review flow or block a due card from being reviewed.
 */
export default function QuestionContext({ context }) {
  if (!context || typeof context !== 'object') return null;
  return (
    <ContextErrorBoundary resetKey={JSON.stringify(context)}>
      <ContextBody context={context} />
    </ContextErrorBoundary>
  );
}
