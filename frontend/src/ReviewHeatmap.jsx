import React, { useState, useEffect, useMemo } from 'react';
import { Flame, CalendarDays } from 'lucide-react';
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

function ReviewHeatmap() {
  const { session } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  // Build the grid data from the fetched days array
  const grid = useMemo(() => {
    if (!data) return null;

    // Build a lookup map from ISO date string → {count, recalled}
    const dayMap = new Map();
    for (const d of data.days) {
      dayMap.set(d.date, { count: d.count, recalled: d.recalled });
    }

    // End = today; start = the Sunday of the week 52 full weeks ago
    const today = new Date();
    const todayStr = toLocalDateStr(today);
    const todayDow = today.getDay(); // 0=Sun

    // The grid ends at the last day of the current week (Saturday)
    const endOfGrid = addDays(today, 6 - todayDow);
    // Start = 52 weeks before the first day of the current week
    const startOfCurrentWeek = addDays(today, -todayDow);
    const startOfGrid = addDays(startOfCurrentWeek, -52 * 7); // 53 weeks total

    // Build columns: each column = one week (7 days Sun..Sat)
    const weeks = [];
    let cursor = new Date(startOfGrid);

    while (cursor <= endOfGrid) {
      const week = [];
      for (let dow = 0; dow < 7; dow++) {
        const dateStr = toLocalDateStr(cursor);
        const entry = dayMap.get(dateStr) ?? null;
        week.push({
          dateStr,
          count: entry?.count ?? 0,
          recalled: entry?.recalled ?? 0,
          isFuture: cursor > today,
        });
        cursor = addDays(cursor, 1);
      }
      weeks.push(week);
    }

    // Month labels: figure out which week column each month starts at
    const monthLabels = [];
    for (let wi = 0; wi < weeks.length; wi++) {
      const firstDay = weeks[wi][0]; // Sunday of that week
      const d = new Date(firstDay.dateStr + 'T00:00:00'); // parse as local
      if (wi === 0 || d.getDate() <= 7) {
        // Show the month label if this is the first week where that month appears
        const prevWeekFirst = wi > 0 ? new Date(weeks[wi - 1][0].dateStr + 'T00:00:00') : null;
        if (!prevWeekFirst || prevWeekFirst.getMonth() !== d.getMonth()) {
          monthLabels.push({ wi, label: MONTH_NAMES[d.getMonth()] });
        }
      }
    }

    return { weeks, monthLabels, todayStr };
  }, [data]);

  if (loading) {
    return (
      <div className="kinetic-card bg-white p-5">
        <div className="h-4 w-32 bg-[rgba(15,23,42,0.07)] rounded animate-pulse mb-4" />
        <div className="h-24 bg-[rgba(15,23,42,0.04)] rounded animate-pulse" />
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
    <div className="kinetic-card bg-white p-5 flex flex-col gap-4">
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

      {isEmpty ? (
        <p className="font-sans text-sm text-[#64748B] py-4 text-center">
          Complete reviews to start building your streak.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <div className="inline-block min-w-max">
            {/* Month labels row */}
            <div className="flex mb-1 ml-7">
              {grid.weeks.map((_, wi) => {
                const label = grid.monthLabels.find((m) => m.wi === wi);
                return (
                  <div key={wi} className="w-[13px] mr-[2px] shrink-0">
                    {label ? (
                      <span className="font-sans text-[9px] text-[#94a3b8] whitespace-nowrap">
                        {label.label}
                      </span>
                    ) : null}
                  </div>
                );
              })}
            </div>

            {/* Grid: 7 rows (day of week) × N cols (weeks) */}
            <div className="flex gap-[2px]">
              {/* Day-of-week labels */}
              <div className="flex flex-col gap-[2px] mr-1">
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

              {/* Week columns */}
              {grid.weeks.map((week, wi) => (
                <div key={wi} className="flex flex-col gap-[2px]">
                  {week.map((cell) => (
                    <div
                      key={cell.dateStr}
                      className={[
                        'w-[11px] h-[11px] rounded-[2px]',
                        cell.isFuture
                          ? 'bg-[rgba(15,23,42,0.03)]'
                          : cellClass(cell.count),
                      ].join(' ')}
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

            {/* Legend */}
            <div className="flex items-center gap-1 mt-2 ml-7">
              <span className="font-sans text-[9px] text-[#94a3b8]">Less</span>
              {[0, 1, 2, 4, 7].map((count) => (
                <div
                  key={count}
                  className={`w-[11px] h-[11px] rounded-[2px] ${cellClass(count)}`}
                />
              ))}
              <span className="font-sans text-[9px] text-[#94a3b8]">More</span>
            </div>
          </div>
        </div>
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
