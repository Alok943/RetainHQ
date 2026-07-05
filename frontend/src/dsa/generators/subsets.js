export function subsetsEvents(nums = [1, 2, 3]) {
  const events = [];
  const nodes = [];
  let stepId = 1;
  let nodeIdCounter = 1;
  
  function buildTree(index, id) {
    const node = { id, children: [] };
    nodes.push(node);
    if (index < nums.length) {
      // EXCLUDE branch
      const excludeId = ++nodeIdCounter;
      node.children.push(excludeId);
      buildTree(index + 1, excludeId);
      
      // INCLUDE branch
      const includeId = ++nodeIdCounter;
      node.children.push(includeId);
      buildTree(index + 1, includeId);
    }
    return node;
  }
  
  const rootNode = buildTree(0, 1);
  const rootId = rootNode.id;
  
  events.push({
    step_id: stepId++,
    op: 'TREE_INIT',
    args: { nodes, root: rootId },
    note: `Initialize decision tree for subsets of [${nums.join(', ')}]`,
  });
  
  function solve(index, currentSubset, id) {
    const node = nodes.find(n => n.id === id);
    
    events.push({
      step_id: stepId++,
      op: 'CALL',
      args: { id, index, currentSubset: [...currentSubset] },
      note: `Explore index ${index} with subset [${currentSubset.join(', ')}]`,
    });
    
    if (index === nums.length) {
      events.push({
        step_id: stepId++,
        op: 'RECORD',
        args: { id, subset: [...currentSubset] },
        note: `Recorded subset: [${currentSubset.join(', ')}]`,
      });
      events.push({
        step_id: stepId++,
        op: 'RETURN',
        args: { id },
        note: `Return to backtrack`,
      });
      return;
    }
    
    // EXCLUDE branch
    const excludeId = node.children[0];
    events.push({
      step_id: stepId++,
      op: 'CHOOSE',
      args: { id: excludeId, choice: 'Exclude' },
      note: `Choice: Exclude ${nums[index]}`,
    });
    solve(index + 1, currentSubset, excludeId);
    events.push({
      step_id: stepId++,
      op: 'UNCHOOSE',
      args: { id: excludeId },
      note: `Backtrack from Exclude branch`,
    });
    
    // INCLUDE branch
    const includeId = node.children[1];
    events.push({
      step_id: stepId++,
      op: 'CHOOSE',
      args: { id: includeId, choice: 'Include' },
      note: `Choice: Include ${nums[index]}`,
    });
    currentSubset.push(nums[index]);
    solve(index + 1, currentSubset, includeId);
    currentSubset.pop();
    events.push({
      step_id: stepId++,
      op: 'UNCHOOSE',
      args: { id: includeId },
      note: `Undo Include choice for ${nums[index]} and backtrack`,
    });
    
    events.push({
      step_id: stepId++,
      op: 'RETURN',
      args: { id },
      note: `Return from index ${index}`,
    });
  }
  
  solve(0, [], rootId);
  
  return events;
}
