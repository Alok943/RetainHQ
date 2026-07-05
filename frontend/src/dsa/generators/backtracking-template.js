export function backtrackingTemplateEvents(depth = 3) {
  const events = [];
  const nodes = [];
  let stepId = 1;
  let nodeIdCounter = 1;
  
  // We'll build a small generic tree: root has 2 children, they have 1 or 2 children, up to depth.
  // To keep it simple, let's just make a full binary tree of depth 2 (root + 2 levels)
  // which has 1 + 2 + 4 = 7 nodes.
  
  function buildTree(level, id) {
    const node = { id, children: [] };
    nodes.push(node);
    if (level < 2) {
      const leftId = ++nodeIdCounter;
      node.children.push(leftId);
      buildTree(level + 1, leftId);
      
      const rightId = ++nodeIdCounter;
      node.children.push(rightId);
      buildTree(level + 1, rightId);
    }
    return node;
  }
  
  const rootNode = buildTree(0, 1);
  const rootId = rootNode.id;
  
  events.push({
    step_id: stepId++,
    op: 'TREE_INIT',
    args: { nodes, root: rootId },
    note: 'Initialize the decision tree state space',
  });
  
  function solve(id, path, isLeft) {
    const node = nodes.find(n => n.id === id);
    
    events.push({
      step_id: stepId++,
      op: 'CALL',
      args: { id },
      note: `Explore node ${id}`,
    });
    
    // leaf node check
    if (!node.children || node.children.length === 0) {
      if (isLeft) { // Let's pretend left leaves are valid solutions, right are dead-ends
        events.push({
          step_id: stepId++,
          op: 'RECORD',
          args: { id },
          note: `Node ${id} is a valid solution, record it`,
        });
      } else {
        events.push({
          step_id: stepId++,
          op: 'PRUNE',
          args: { id },
          note: `Node ${id} is a dead-end, prune branch`,
        });
      }
      events.push({
        step_id: stepId++,
        op: 'RETURN',
        args: { id }, // point back to parent? or just ascend
        note: `Return from node ${id}`,
      });
      return;
    }
    
    for (let i = 0; i < node.children.length; i++) {
      const childId = node.children[i];
      const choiceName = i === 0 ? 'Choice A' : 'Choice B';
      
      events.push({
        step_id: stepId++,
        op: 'CHOOSE',
        args: { id: childId, choice: choiceName },
        note: `Make ${choiceName}`,
      });
      
      solve(childId, [...path, choiceName], i === 0);
      
      events.push({
        step_id: stepId++,
        op: 'UNCHOOSE',
        args: { id: childId, choice: choiceName },
        note: `Undo ${choiceName} and backtrack`,
      });
    }
    
    events.push({
      step_id: stepId++,
      op: 'RETURN',
      args: { id },
      note: `Return from node ${id}`,
    });
  }
  
  solve(rootId, [], true);
  
  return events;
}
