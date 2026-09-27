import QuestionContext from './QuestionContext';

// TEMPORARY dev harness (docs/IMPLEMENTATION-quiz-capture-v2.md Step 4) — one real example
// per context type, pulled from actual v2 pilot content so this doubles as a sanity check
// on real data, not synthetic fixtures. Reachable at /context-dev. Remove once wired into
// the Quiz v2 review card (Step 5).
const EXAMPLES = [
  {
    label: 'array — content/roadmaps/dsa/quicksort-and-partition.json',
    context: { type: 'array', values: [8, 3, 5, 1, 9, 2], highlight: [5], labels: { 5: 'pivot (2)' } },
  },
  {
    label: 'tree — content/roadmaps/dsa (mcq gold example)',
    context: { type: 'tree', level_order: [5, 3, 8, 1, 4, null, 9] },
  },
  {
    label: 'graph — content/evals/datasets/mcq_items.jsonl mcq009',
    context: {
      type: 'graph',
      nodes: ['A', 'B', 'C', 'D'],
      edges: [['A', 'B'], ['A', 'C'], ['B', 'D']],
      directed: false,
    },
  },
  {
    label: 'table — content/roadmaps/sql/inner-join.json',
    context: {
      type: 'table',
      tables: [
        { name: 'students', columns: ['id', 'name'], rows: [[1, 'Ann'], [2, 'Ben'], [3, 'Cid']] },
        { name: 'enrollments', columns: ['student_id', 'course'], rows: [[1, 'Math'], [1, 'Physics'], [2, 'Math']] },
      ],
    },
  },
  {
    label: 'code — content/roadmaps/python-swe/closures.json',
    context: {
      type: 'code',
      lang: 'python',
      source: 'def make_multiplier(n):\n    def multiplier(x):\n        return x * n\n    return multiplier\n\ntimes3 = make_multiplier(3)\nprint(times3(10))',
    },
  },
  { label: 'unknown type — must render nothing, never crash', context: { type: 'diagram3d', foo: 'bar' } },
  {
    label: 'malformed known type (row is a string, not an array) — error boundary must catch this, never crash',
    context: { type: 'table', columns: ['a', 'b'], rows: ['not-a-row'] },
  },
];

export default function QuestionContextDev() {
  return (
    <div className="max-w-2xl mx-auto w-full px-4 md:px-8 py-6">
      <h1 className="font-sans text-xl font-bold text-[#0F172A] mb-1">QuestionContext preview</h1>
      <p className="font-sans text-sm text-[#64748B] mb-6">
        Dev harness for the recall_questions v2 context renderer — one example per type.
      </p>
      <div className="flex flex-col gap-8">
        {EXAMPLES.map(({ label, context }) => (
          <div key={label}>
            <div className="font-mono text-[11px] text-[#94a3b8] mb-2">{label}</div>
            <QuestionContext context={context} />
          </div>
        ))}
      </div>
    </div>
  );
}
