-- Schema for Roadmaps Tracker

CREATE TABLE IF NOT EXISTS roadmaps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roadmap_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  roadmap_id UUID REFERENCES roadmaps(id) ON DELETE CASCADE,
  phase TEXT NOT NULL,
  section TEXT NOT NULL,
  title TEXT NOT NULL,
  tier TEXT CHECK (tier IN ('t1', 't2', 't3', 'dsa')),
  order_index INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  node_id UUID REFERENCES roadmap_nodes(id) ON DELETE CASCADE,
  status TEXT CHECK (status IN ('not_started', 'in_progress', 'done')) DEFAULT 'not_started',
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(user_id, node_id)
);

-- Row Level Security (RLS)
ALTER TABLE roadmaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE roadmap_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Public read for roadmaps" ON roadmaps FOR SELECT USING (true);
CREATE POLICY "Public read for roadmap_nodes" ON roadmap_nodes FOR SELECT USING (true);

CREATE POLICY "Users can manage their own progress" ON user_progress
  FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Seed Data: "Python for SWE"
INSERT INTO roadmaps (id, title, description)
VALUES ('11111111-1111-1111-1111-111111111111', 'Python for SWE', 'Comprehensive Python roadmap covering internals and production systems.')
ON CONFLICT (id) DO NOTHING;

-- Seed Nodes for Month 1 -> Python Concepts
INSERT INTO roadmap_nodes (roadmap_id, phase, section, title, tier, order_index) VALUES
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'Python Concepts', 'OOP basics', 't1', 1),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'Python Concepts', 'Dunders & operator overloading', 't2', 2),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'Python Concepts', 'First-class functions & closures', 't2', 3),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'Python Concepts', 'Decorators', 't3', 4),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'Python Concepts', '*args & **kwargs', 't1', 5),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'Python Concepts', 'Generators & iterators', 't3', 6),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'Python Concepts', 'Context managers', 't2', 7),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'Python Concepts', 'Type hints & Pydantic', 't2', 8);

-- Seed Nodes for Month 1 -> DSA
INSERT INTO roadmap_nodes (roadmap_id, phase, section, title, tier, order_index) VALUES
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'DSA', 'Arrays & two pointers', 'dsa', 1),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'DSA', 'Hashmaps & sets', 'dsa', 2),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'DSA', 'Stacks & queues', 'dsa', 3),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'DSA', 'Sliding window', 'dsa', 4),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'DSA', 'Binary search', 'dsa', 5),
('11111111-1111-1111-1111-111111111111', 'Month 1 — Python Internals', 'DSA', 'Recursion basics', 'dsa', 6);

-- Seed Nodes for Month 2 -> Python Production
INSERT INTO roadmap_nodes (roadmap_id, phase, section, title, tier, order_index) VALUES
('11111111-1111-1111-1111-111111111111', 'Month 2 — Production Python', 'Python Production', 'Error handling', 't2', 1),
('11111111-1111-1111-1111-111111111111', 'Month 2 — Production Python', 'Python Production', 'Env management', 't2', 2),
('11111111-1111-1111-1111-111111111111', 'Month 2 — Production Python', 'Python Production', 'Project structure', 't2', 3),
('11111111-1111-1111-1111-111111111111', 'Month 2 — Production Python', 'Python Production', 'FastAPI — routes & Pydantic', 't3', 4),
('11111111-1111-1111-1111-111111111111', 'Month 2 — Production Python', 'Python Production', 'Dependency injection', 't3', 5),
('11111111-1111-1111-1111-111111111111', 'Month 2 — Production Python', 'Python Production', 'Async / await', 't3', 6);

-- Seed Nodes for Month 2 -> DSA
INSERT INTO roadmap_nodes (roadmap_id, phase, section, title, tier, order_index) VALUES
('11111111-1111-1111-1111-111111111111', 'Month 2 — Production Python', 'DSA', 'Linked lists', 'dsa', 1),
('11111111-1111-1111-1111-111111111111', 'Month 2 — Production Python', 'DSA', 'Trees — BFS & DFS', 'dsa', 2),
('11111111-1111-1111-1111-111111111111', 'Month 2 — Production Python', 'DSA', 'Dynamic programming', 'dsa', 3),
('11111111-1111-1111-1111-111111111111', 'Month 2 — Production Python', 'DSA', 'Heaps & priority queues', 'dsa', 4),
('11111111-1111-1111-1111-111111111111', 'Month 2 — Production Python', 'DSA', 'Graphs basics', 'dsa', 5);
