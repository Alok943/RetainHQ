export function combinationSumEvents(input) {
  const candidates = input?.candidates || [2, 3, 6, 7];
  const target = input?.target || 7;
  const events = [];
  const nodes = [];
  let stepId = 1;
  let nodeIdCounter = 1;
  
  // Phase 1: Pre-build the exact tree structure to provide to TREE_INIT
  function preBuildTree(remaining, startIndex, id) {
    const node = { id, children: [] };
    nodes.push(node);
    
    if (remaining === 0) return node;
    
    for (let i = startIndex; i < candidates.length; i++) {
      const childId = ++nodeIdCounter;
      node.children.push(childId);
      // Even if candidate > remaining, we create the node so we can visually PRUNE it
      if (candidates[i] <= remaining) {
        preBuildTree(remaining - candidates[i], i, childId);
      } else {
        // Just create a leaf node for the prune
        nodes.push({ id: childId, children: [] });
      }
    }
    return node;
  }
  
  const rootNode = preBuildTree(target, 0, 1);
  const rootId = rootNode.id;
  
  events.push({
    step_id: stepId++,
    op: 'TREE_INIT',
    args: { nodes, root: rootId },
    note: `Initialize decision tree for combination sum (target ${target})`,
  });
  
  // Phase 2: Emit the events
  function solve(remaining, startIndex, currentCombo, id) {
    const node = nodes.find(n => n.id === id);
    
    events.push({
      step_id: stepId++,
      op: 'CALL',
      args: { id, remaining, startIndex, currentCombo: [...currentCombo] },
      note: `Explore with remaining=${remaining}, combo=[${currentCombo.join(', ')}]`,
    });
    
    if (remaining === 0) {
      events.push({
        step_id: stepId++,
        op: 'RECORD',
        args: { id, combo: [...currentCombo] },
        note: `Target reached! Record combination: [${currentCombo.join(', ')}]`,
      });
      events.push({
        step_id: stepId++,
        op: 'RETURN',
        args: { id },
        note: `Return to backtrack`,
      });
      return;
    }
    
    let childIdx = 0;
    for (let i = startIndex; i < candidates.length; i++) {
      const childId = node.children[childIdx++];
      const candidate = candidates[i];
      
      events.push({
        step_id: stepId++,
        op: 'CHOOSE',
        args: { id: childId, choice: candidate },
        note: `Try candidate ${candidate}`,
      });
      
      events.push({
        step_id: stepId++,
        op: 'CHECK_PRUNE', // Anchor for prediction
        args: { candidate, remaining },
        note: `Check if candidate ${candidate} > remaining ${remaining}`,
      });
      
      if (candidate > remaining) {
        events.push({
          step_id: stepId++,
          op: 'PRUNE',
          args: { id: childId },
          note: `Candidate ${candidate} > ${remaining}, prune branch`,
        });
        events.push({
          step_id: stepId++,
          op: 'UNCHOOSE',
          args: { id: childId },
          note: `Backtrack from pruned branch`,
        });
        // In some implementations we break because array is sorted, but let's just continue
        continue; 
      }
      
      currentCombo.push(candidate);
      solve(remaining - candidate, i, currentCombo, childId);
      currentCombo.pop();
      
      events.push({
        step_id: stepId++,
        op: 'UNCHOOSE',
        args: { id: childId },
        note: `Undo choice of ${candidate} and backtrack`,
      });
    }
    
    events.push({
      step_id: stepId++,
      op: 'RETURN',
      args: { id },
      note: `Return from node ${id}`,
    });
  }
  
  solve(target, 0, [], rootId);
  
  return events;
}
