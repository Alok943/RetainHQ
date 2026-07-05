import json

with open('content/roadmaps/dsa/queue-and-deque.json', 'r') as f:
    q = json.load(f)

q['oa_questions'].append({
    'question': "Return the level order traversal of a binary tree's nodes' values.",
    'answer': "Use a FIFO Queue. Push the root, then loop while the queue isn't empty: for each node popped from the front, push its children to the back. This naturally processes nodes level by level.",
    'approach': "Recognize that Breadth-First Search (BFS) on a tree maps perfectly to the FIFO structure of a queue.",
    'company': "SDE interview"
})

with open('content/roadmaps/dsa/queue-and-deque.json', 'w') as f:
    json.dump(q, f, indent=2)
    f.write("\n")
