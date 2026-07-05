export function permutationsEvents(nums = [1, 2, 3]) {
  const events = [];
  const nodes = [];
  let stepId = 1;
  let nodeIdCounter = 1;
  const N = nums.length;
  
  // Build a full N-ary tree up to depth N
  function buildTree(depth, id) {
    const node = { id, children: [] };
    nodes.push(node);
    if (depth < N) {
      for (let i = 0; i < N; i++) {
        const childId = ++nodeIdCounter;
        node.children.push(childId);
        buildTree(depth + 1, childId);
      }
    }
    return node;
  }
  
  const rootNode = buildTree(0, 1);
  const rootId = rootNode.id;
  
  events.push({
    step_id: stepId++,
    op: 'TREE_INIT',
    args: { nodes, root: rootId },
    note: `Initialize decision tree for permutations of [${nums.join(', ')}]`,
  });
  
  const used = Array(N).fill(false);
  
  function solve(depth, currentPerm, id) {
    const node = nodes.find(n => n.id === id);
    
    events.push({
      step_id: stepId++,
      op: 'CALL',
      args: { id, depth, currentPerm: [...currentPerm], used: [...used] },
      note: `Explore depth ${depth} with perm [${currentPerm.join(', ')}]`,
    });
    
    if (depth === N) {
      events.push({
        step_id: stepId++,
        op: 'RECORD',
        args: { id, perm: [...currentPerm] },
        note: `Recorded permutation: [${currentPerm.join(', ')}]`,
      });
      events.push({
        step_id: stepId++,
        op: 'RETURN',
        args: { id },
        note: `Return to backtrack`,
      });
      return;
    }
    
    for (let i = 0; i < N; i++) {
      const childId = node.children[i];
      
      events.push({
        step_id: stepId++,
        op: 'CHOOSE',
        args: { id: childId, choice: nums[i] },
        note: `Try choosing ${nums[i]}`,
      });
      
      events.push({
        step_id: stepId++,
        op: 'CHECK_USED', // For prediction anchors
        args: { value: nums[i], isUsed: used[i] },
        note: `Check if ${nums[i]} is already used`,
      });
      
      if (used[i]) {
        events.push({
          step_id: stepId++,
          op: 'PRUNE',
          args: { id: childId },
          note: `${nums[i]} is already used, prune this branch`,
        });
        events.push({
          step_id: stepId++,
          op: 'UNCHOOSE', // We still unchoose to back out visually
          args: { id: childId },
          note: `Backtrack from pruned branch`,
        });
        continue;
      }
      
      used[i] = true;
      currentPerm.push(nums[i]);
      
      solve(depth + 1, currentPerm, childId);
      
      used[i] = false;
      currentPerm.pop();
      
      events.push({
        step_id: stepId++,
        op: 'UNCHOOSE',
        args: { id: childId },
        note: `Undo choice of ${nums[i]} and backtrack`,
      });
    }
    
    events.push({
      step_id: stepId++,
      op: 'RETURN',
      args: { id },
      note: `Return from depth ${depth}`,
    });
  }
  
  solve(0, [], rootId);
  
  return events;
}
