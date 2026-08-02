import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Flame, CalendarDays, ChevronDown, ChevronUp } from 'lucide-react';
import { apiFetch } from './lib/api';
import { useAuth } from './lib/AuthContext';

// Build an ISO "YYYY-MM-DD" string from a local Date object WITHOUT timezone conversion.
// We compare these strings against the naive-UTC dates returned by the API.
function toLocalDateStr(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// Advance a Date by N days (mutates and returns for chaining)
function addDays(d, n) {
  const copy = new Date(d);
  copy.setDate(copy.getDate() + n);
  return copy;
}

// Intensity bucket → Tailwind bg utility class (cyan #0891B2 scale)
// Bucket thresholds: 0 = empty, 1 = light, 2-3 = medium-light, 4-6 = medium-dark, 7+ = full
function cellClass(count) {
  if (count === 0) return 'bg-[rgba(15,23,42,0.05)]';
  if (count === 1) return 'bg-[#0891B2]/20';
  if (count <= 3) return 'bg-[#0891B2]/45';
  if (count <= 6) return 'bg-[#0891B2]/70';
  return 'bg-[#0891B2]';
}

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const TOTAL_WEEKS = 53;         // a full year of columns

// Month labels for a slice of weeks: label a column when its Sunday belongs to a
// different month than the previous column's Sunday.
function monthLabelsFor(weeks) {
  const labels = [];
  for (let wi = 0; wi < weeks.length; wi++) {
    const d = new Date(weeks[wi][0].dateStr + 'T00:00:00'); // parse as local
    const prev = wi > 0 ? new Date(weeks[wi - 1][0].dateStr + 'T00:00:00') : null;
    if (!prev || prev.getMonth() !== d.getMonth()) {
      // Skip the leading column if its month label would immediately repeat at
      // the next column (a stub week of 1-2 days reads as a mislabelled month).
      if (wi === 0 && weeks.length > 1) {
        const next = new Date(weeks[1][0].dateStr + 'T00:00:00');
        if (next.getMonth() !== d.getMonth()) continue;
      }
      labels.push({ wi, label: MONTH_NAMES[d.getMonth()] });
    }
  }
  return labels;
}

function ReviewHeatmap() {
  const { session } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (!session) {
      setLoading(false);
      return;
    }
    apiFetch('/api/dashboard/heatmap')
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // Build the grid data from the fetched days array — always the real full
  // year, never a synthetic shorter range. The card stays compact by
  // clamping the *visible* width and defaulting the scroll position to the
  // right edge (today), not by computing less data.
  const grid = useMemo(() => {
    if (!data) return null;

    // Build a lookup map from ISO date string → {count, recalled}
    const dayMap = new Map();
    for (const d of data.days) {
      dayMap.set(d.date, { count: d.count, recalled: d.recalled });
    }

    // The grid runs up to *today* and stops — no trailing strip of future
    // cells. The API only knows about completed reviews, so future days would
    // be permanently blank filler.
    const today = new Date();
    const todayStr = toLocalDateStr(today);
    const todayDow = today.getDay(); // 0=Sun

    // Start = 52 weeks before the Sunday of the current week (53 columns total)
    const startOfGrid = addDays(addDays(today, -todayDow), -(TOTAL_WEEKS - 1) * 7);

    // Build columns: each column = one week (7 days Sun..Sat). The last column
    // is a partial week, holding Sunday..today only.
    const weeks = [];
    let cursor = new Date(startOfGrid);

    while (cursor <= today) {
      const week = [];
      for (let dow = 0; dow < 7 && cursor <= today; dow++) {
        const dateStr = toLocalDateStr(cursor);
        const entry = dayMap.get(dateStr) ?? null;
        week.push({
          dateStr,
          count: entry?.count ?? 0,
          recalled: entry?.recalled ?? 0,
        });
        cursor = addDays(cursor, 1);
      }
      weeks.push(week);
    }

    return { weeks, todayStr };
  }, [data]);

  // Every column is always rendered. Collapsed, the track is right-aligned
  // inside an overflow-hidden box, so the browser itself shows exactly the
  // most recent weeks that fit and clips the rest off the left edge — no
  // measuring, and it re-fits on any container change for free.
  const view = useMemo(() => {
    if (!grid) return null;
    return { weeks: grid.weeks, monthLabels: monthLabelsFor(grid.weeks) };
  }, [grid]);

  // When expanded, the full year usually overflows — pin the scroll to the
  // right edge (today) so it opens on current progress, not the oldest weeks.
  useEffect(() => {
    if (expanded && scrollRef.current) {
      scrollRef.current.scrollLeft = scrollRef.current.scrollWidth;
    }
  }, [expanded, view]);

  if (loading) {
    return (
      <div className="kinetic-card bg-white p-5 flex flex-col gap-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="skeleton h-6 w-20" />
          <div className="w-px h-4 bg-[rgba(15,23,42,0.08)]" />
          <div className="skeleton h-6 w-24" />
          <div className="skeleton h-6 w-24" />
          <div className="skeleton h-6 w-20" />
        </div>
        <div className="skeleton h-24 w-full rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="kinetic-card bg-white p-5 text-sm text-[#ba1a1a]">
        Couldn't load review activity: {error}
      </div>
    );
  }

  if (!session) return null;

  const isEmpty = !data || data.total_reviews === 0;

  return (
    // min-w-0: the card is a grid item, whose automatic minimum size would
    // otherwise let the full-year track widen the card past its column.
    <div className="kinetic-card bg-white p-5 flex flex-col gap-4 min-w-0">
      {/* Stats row */}
      <div className="flex flex-wrap gap-4 items-center">
        <div className="flex items-center gap-1.5">
          <Flame size={16} className="text-[#0891B2]" />
          <span className="font-mono text-lg font-semibold text-[#0F172A]">
            {data?.current_streak ?? 0}
          </span>
          <span className="font-sans text-xs text-[#64748B]">day streak</span>
        </div>
        <div className="w-px h-4 bg-[rgba(15,23,42,0.08)]" />
        <StatPill label="Longest streak" value={`${data?.longest_streak ?? 0}d`} />
        <StatPill label="Total reviews" value={data?.total_reviews ?? 0} />
        <StatPill label="Active days" value={data?.active_days ?? 0} />
      </div>

      {view && (
      <div className="flex flex-col gap-1.5 min-w-0">
      {/* Day-of-week labels sit outside the clipped track so they are never the
          thing that gets cut off; the spacer aligns them under the month row. */}
      <div className="flex min-w-0">
        <div className="shrink-0 flex flex-col mr-1">
          <div className="h-[12px] mb-1" aria-hidden="true" />
          <div className="flex flex-col gap-[2px]">
            {DAY_LABELS.map((label, i) => (
              <div
                key={label}
                className="h-[11px] flex items-center"
                style={{ visibility: i % 2 === 1 ? 'visible' : 'hidden' }}
              >
                <span className="font-sans text-[8px] text-[#94a3b8] leading-none w-6 text-right pr-0.5">
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Collapsed: justify-end + overflow-hidden makes the browser show the
            most recent weeks that fit and clip the older ones off the left —
            the "fit to the card" sizing, done in CSS rather than measured.
            Expanded: a plain scroller, pinned to today on open. */}
        <div
          ref={scrollRef}
          id="review-heatmap-grid"
          className={
            expanded
              ? 'min-w-0 flex-1 overflow-x-auto'
              : 'min-w-0 flex-1 overflow-hidden flex justify-end cursor-pointer'
          }
          {...(expanded
            ? {}
            : {
                role: 'button',
                tabIndex: 0,
                'aria-expanded': false,
                'aria-label': 'Show the full year of review activity',
                onClick: () => setExpanded(true),
                onKeyDown: (e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setExpanded(true);
                  }
                },
              })}
        >
          <div className="shrink-0 min-w-max">
            {/* Month labels — same 11px + 2px stride as the grid below, so the
                two rows stay pixel-aligned at any clip point. */}
            <div className="flex gap-[2px] h-[12px] mb-1">
              {view.weeks.map((week, wi) => {
                const label = view.monthLabels.find((m) => m.wi === wi);
                return (
                  <div key={week[0].dateStr} className="w-[11px] shrink-0">
                    {label ? (
                      <span className="font-sans text-[9px] text-[#94a3b8] leading-none whitespace-nowrap">
                        {label.label}
                      </span>
                    ) : null}
                  </div>
                );
              })}
            </div>

            {/* Grid: 7 rows (day of week) × 53 cols (weeks) */}
            <div className="flex gap-[2px]">
              {view.weeks.map((week) => (
                <div key={week[0].dateStr} className="flex flex-col gap-[2px]">
                  {week.map((cell) => (
                    <div
                      key={cell.dateStr}
                      className={`w-[11px] h-[11px] rounded-[2px] ${cellClass(cell.count)}`}
                      title={
                        cell.count === 0
                          ? `No reviews on ${cell.dateStr}`
                          : `${cell.dateStr} — ${cell.count} review${cell.count !== 1 ? 's' : ''} (${cell.recalled} recalled)`
                      }
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer — outside the track so the legend and toggle stay put
          regardless of scroll position */}
      <div className="flex items-center justify-between gap-2 ml-7">
        <div className="flex items-center gap-1">
          <span className="font-sans text-[9px] text-[#94a3b8]">Less</span>
          {[0, 1, 2, 4, 7].map((count) => (
            <div
              key={count}
              className={`w-[11px] h-[11px] rounded-[2px] ${cellClass(count)}`}
            />
          ))}
          <span className="font-sans text-[9px] text-[#94a3b8]">More</span>
        </div>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          aria-controls="review-heatmap-grid"
          className="flex items-center gap-0.5 font-sans text-[10px] text-[#64748B] hover:text-[#0891B2] transition-colors"
        >
          {expanded ? 'Show less' : 'Full year'}
          {expanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
        </button>
      </div>
      </div>
      )}

      {isEmpty && (
        <p className="font-sans text-sm text-[#64748B] text-center">
          Complete reviews to start building your streak.
        </p>
      )}
    </div>
  );
}

function StatPill({ label, value }) {
  return (
    <div className="flex flex-col leading-tight">
      <span className="font-mono text-sm font-semibold text-[#0F172A]">{value}</span>
      <span className="font-sans text-[10px] text-[#64748B]">{label}</span>
    </div>
  );
}

export default ReviewHeatmap;
