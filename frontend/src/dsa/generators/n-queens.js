export function nQueensEvents(N = 4) {
  const events = [];
  const grid = Array.from({ length: N }, () => Array(N).fill(null));
  let step = 1;

  // Initialize the grid
  events.push({
    step_id: step++,
    op: 'GRID_INIT',
    args: { rows: N, cols: N, values: grid },
    note: `Initialize ${N}x${N} board`,
  });

  const queens = []; // {r, c}

  function isSafe(r, c) {
    for (const q of queens) {
      if (q.c === c || q.r - q.c === r - c || q.r + q.c === r + c) return false;
    }
    return true;
  }

  function getAttackedCells() {
    const attacked = [];
    for (let r = 0; r < N; r++) {
      for (let c = 0; c < N; c++) {
        if (!isSafe(r, c) && !queens.some(q => q.r === r && q.c === c)) {
          attacked.push({ r, c });
        }
      }
    }
    return attacked;
  }

  function solve(r) {
    events.push({
      step_id: step++,
      op: 'CALL',
      args: { row: r },
      note: `Exploring row ${r}`,
    });

    if (r === N) {
      events.push({
        step_id: step++,
        op: 'SOLUTION',
        args: { queens: [...queens] },
        note: `Found a valid placement for all ${N} queens!`,
      });
      events.push({
        step_id: step++,
        op: 'RETURN',
        note: `Backtrack to find other solutions`,
      });
      return;
    }

    for (let c = 0; c < N; c++) {
      const safe = isSafe(r, c);
      
      events.push({
        step_id: step++,
        op: 'TEST_CELL', // Just to anchor predictions before PLACE
        args: { r, c, isSafe: safe },
        note: `Check if (${r}, ${c}) is safe`,
      });

      if (safe) {
        queens.push({ r, c });
        events.push({
          step_id: step++,
          op: 'PLACE',
          args: { r, c },
          note: `Place queen at (${r}, ${c})`,
        });
        
        events.push({
          step_id: step++,
          op: 'ATTACK',
          args: { r, c, attacked: getAttackedCells() },
          note: `Queen at (${r}, ${c}) attacks its column and diagonals`,
        });

        solve(r + 1);

        queens.pop();
        events.push({
          step_id: step++,
          op: 'REMOVE',
          args: { r, c },
          note: `Remove queen from (${r}, ${c}) to backtrack`,
        });
        events.push({
          step_id: step++,
          op: 'UNATTACK',
          args: { r, c, attacked: getAttackedCells() },
          note: `Re-evaluate attacked cells after removal`,
        });
      }
    }

    events.push({
      step_id: step++,
      op: 'RETURN',
      note: `Finished exploring row ${r}`,
    });
  }

  solve(0);

  return events;
}
