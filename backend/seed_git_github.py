"""
Seed script: Git & GitHub roadmap for RetainHQ.
Idempotent — deletes and recreates the roadmap each run.
Run: ./.venv/Scripts/python.exe seed_git_github.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
TITLE = "Git & GitHub"
DESCRIPTION = "From zero to confident: version control, branching strategies, GitHub workflows, and advanced Git everyone uses but few understand."

# (phase, section, title, tier)
NODES = [
    # ---------------- Step 1: Core Concepts ----------------
    ("Step 1: Core Concepts", "Basics", "What is Git? VCS & why it matters", "easy"),
    ("Step 1: Core Concepts", "Basics", "git init, git clone & repo structure", "easy"),
    ("Step 1: Core Concepts", "Basics", "git status, git add & the staging area", "easy"),
    ("Step 1: Core Concepts", "Basics", "git commit — writing good messages", "easy"),
    ("Step 1: Core Concepts", "Basics", "git log, git diff & inspecting history", "easy"),
    ("Step 1: Core Concepts", "Basics", ".gitignore — patterns & global ignore", "easy"),

    # ---------------- Step 2: Branching & Merging ----------------
    ("Step 2: Branching & Merging", "Branches", "git branch, checkout & switch", "easy"),
    ("Step 2: Branching & Merging", "Branches", "git merge — fast-forward vs 3-way", "medium"),
    ("Step 2: Branching & Merging", "Branches", "Merge conflicts — resolve & continue", "medium"),
    ("Step 2: Branching & Merging", "Branches", "git rebase — linearise history", "medium"),
    ("Step 2: Branching & Merging", "Branches", "Rebase vs merge — when to use which", "medium"),
    ("Step 2: Branching & Merging", "Branches", "git stash — save & restore WIP", "easy"),

    # ---------------- Step 3: Remotes & Collaboration ----------------
    ("Step 3: Remotes & Collaboration", "Remotes", "git remote — add, view & manage", "easy"),
    ("Step 3: Remotes & Collaboration", "Remotes", "git fetch vs git pull", "medium"),
    ("Step 3: Remotes & Collaboration", "Remotes", "git push & tracking branches", "easy"),
    ("Step 3: Remotes & Collaboration", "Remotes", "Fork & upstream workflow (open source)", "medium"),
    ("Step 3: Remotes & Collaboration", "Remotes", "Resolving diverged branches after pull", "medium"),

    # ---------------- Step 4: GitHub Workflow ----------------
    ("Step 4: GitHub Workflow", "GitHub", "GitHub UI — repos, issues & projects", "easy"),
    ("Step 4: GitHub Workflow", "GitHub", "Pull Requests — open, review & merge", "easy"),
    ("Step 4: GitHub Workflow", "GitHub", "Code review — comments, suggest changes", "medium"),
    ("Step 4: GitHub Workflow", "GitHub", "Branch protection & required reviewers", "medium"),
    ("Step 4: GitHub Workflow", "GitHub", "GitHub Actions — basic CI on push", "medium"),
    ("Step 4: GitHub Workflow", "GitHub", "GitHub Actions — build, test & deploy pipeline", "hard"),
    ("Step 4: GitHub Workflow", "GitHub", "Secrets & environment variables in Actions", "medium"),

    # ---------------- Step 5: Advanced Git ----------------
    ("Step 5: Advanced Git", "Rewriting History", "git commit --amend & interactive rebase", "medium"),
    ("Step 5: Advanced Git", "Rewriting History", "git cherry-pick — port specific commits", "medium"),
    ("Step 5: Advanced Git", "Rewriting History", "git reset (soft / mixed / hard)", "hard"),
    ("Step 5: Advanced Git", "Rewriting History", "git revert — safe undo on shared branches", "medium"),
    ("Step 5: Advanced Git", "Rewriting History", "git reflog — recover lost commits", "hard"),
    ("Step 5: Advanced Git", "Internals", "Git objects — blob, tree, commit, tag", "hard"),
    ("Step 5: Advanced Git", "Internals", "HEAD, detached HEAD & refs", "medium"),
    ("Step 5: Advanced Git", "Internals", "git bisect — binary search for a bug", "hard"),

    # ---------------- Step 6: Workflows & Best Practices ----------------
    ("Step 6: Workflows & Best Practices", "Strategies", "Git Flow — feature/release/hotfix branches", "medium"),
    ("Step 6: Workflows & Best Practices", "Strategies", "Trunk-based development & feature flags", "medium"),
    ("Step 6: Workflows & Best Practices", "Strategies", "Semantic versioning & git tags", "easy"),
    ("Step 6: Workflows & Best Practices", "Strategies", "Conventional Commits & changelogs", "easy"),
    ("Step 6: Workflows & Best Practices", "Strategies", "Pre-commit hooks & lint-staged", "medium"),
    ("Step 6: Workflows & Best Practices", "Strategies", "Monorepo patterns with Git", "hard"),
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)}
        )
        await conn.execute(
            text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)}
        )

        await conn.execute(
            text("INSERT INTO roadmaps (id, title, description, created_at) "
                 "VALUES (:id, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "title": TITLE, "desc": DESCRIPTION},
        )

        for i, (phase, section, title, tier) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes "
                     "(id, roadmap_id, phase, section, title, tier, order_index) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx)"),
                {
                    "id": str(uuid.uuid4()),
                    "rid": str(ROADMAP_ID),
                    "phase": phase,
                    "section": section,
                    "title": title,
                    "tier": tier,
                    "idx": i,
                },
            )

    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
