"""
Seed script: Linux & Shell roadmap for RetainHQ.
Idempotent — deletes and recreates the roadmap each run.
Run: ./.venv/Scripts/python.exe seed_linux_shell.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("50505050-5050-5050-5050-505050505050")
TITLE = "Linux & Shell"
DESCRIPTION = "Commands, scripting, permissions, processes, and networking — everything a developer needs to be productive on any Linux/Unix system or cloud server."

NODES = [
    # ---------------- Step 1: Getting Around ----------------
    ("Step 1: Getting Around", "Navigation", "File system hierarchy — /, /home, /etc, /var, /proc", "easy"),
    ("Step 1: Getting Around", "Navigation", "ls, cd, pwd, tree & hidden files", "easy"),
    ("Step 1: Getting Around", "Navigation", "Absolute vs relative paths", "easy"),
    ("Step 1: Getting Around", "Navigation", "man pages & --help — finding anything", "easy"),
    ("Step 1: Getting Around", "Navigation", "Tab completion & history (Ctrl+R)", "easy"),

    # ---------------- Step 2: Files & Text ----------------
    ("Step 2: Files & Text", "File Operations", "cp, mv, rm, mkdir & touch", "easy"),
    ("Step 2: Files & Text", "File Operations", "find — search by name, type, size & mtime", "medium"),
    ("Step 2: Files & Text", "File Operations", "ln — hard links vs symbolic links", "medium"),
    ("Step 2: Files & Text", "Viewing & Editing", "cat, less, head, tail & tail -f", "easy"),
    ("Step 2: Files & Text", "Viewing & Editing", "vim essentials — open, edit, save & quit", "easy"),
    ("Step 2: Files & Text", "Viewing & Editing", "nano for quick edits", "easy"),
    ("Step 2: Files & Text", "Text Processing", "grep — patterns, -r, -i, -v & -n", "easy"),
    ("Step 2: Files & Text", "Text Processing", "sed — in-place substitution & line deletion", "medium"),
    ("Step 2: Files & Text", "Text Processing", "awk — field splitting & one-liners", "medium"),
    ("Step 2: Files & Text", "Text Processing", "sort, uniq, wc & cut", "easy"),
    ("Step 2: Files & Text", "Text Processing", "Pipes & redirection — |, >, >>, 2>&1", "easy"),
    ("Step 2: Files & Text", "Text Processing", "xargs — build commands from stdin", "medium"),

    # ---------------- Step 3: Permissions & Users ----------------
    ("Step 3: Permissions & Users", "Permissions", "rwx bits — read, write, execute for user/group/other", "easy"),
    ("Step 3: Permissions & Users", "Permissions", "chmod — symbolic & octal notation", "easy"),
    ("Step 3: Permissions & Users", "Permissions", "chown & chgrp", "easy"),
    ("Step 3: Permissions & Users", "Permissions", "setuid, setgid & sticky bit", "hard"),
    ("Step 3: Permissions & Users", "Users", "sudo & /etc/sudoers", "medium"),
    ("Step 3: Permissions & Users", "Users", "useradd, usermod, passwd & groups", "medium"),
    ("Step 3: Permissions & Users", "Users", "su vs sudo — when to use each", "easy"),

    # ---------------- Step 4: Processes ----------------
    ("Step 4: Processes", "Viewing", "ps, top & htop — what's running", "easy"),
    ("Step 4: Processes", "Viewing", "pgrep, pidof & lsof", "medium"),
    ("Step 4: Processes", "Control", "kill, killall & signals (SIGTERM, SIGKILL, SIGHUP)", "medium"),
    ("Step 4: Processes", "Control", "fg, bg, jobs & nohup", "medium"),
    ("Step 4: Processes", "Control", "nice & renice — process priority", "medium"),
    ("Step 4: Processes", "System", "systemd — start, stop, enable & status", "medium"),
    ("Step 4: Processes", "System", "journalctl — reading system logs", "medium"),
    ("Step 4: Processes", "System", "/proc filesystem — runtime process info", "hard"),

    # ---------------- Step 5: Shell Scripting ----------------
    ("Step 5: Shell Scripting", "Basics", "Shebang, variables & quoting rules", "easy"),
    ("Step 5: Shell Scripting", "Basics", "if/elif/else & test expressions [ ]", "easy"),
    ("Step 5: Shell Scripting", "Basics", "for, while & until loops", "easy"),
    ("Step 5: Shell Scripting", "Basics", "Functions — define, call & return values", "medium"),
    ("Step 5: Shell Scripting", "Basics", "Script arguments — $1, $@, $# & getopts", "medium"),
    ("Step 5: Shell Scripting", "Intermediate", "Arrays & associative arrays (bash 4+)", "medium"),
    ("Step 5: Shell Scripting", "Intermediate", "Command substitution $() & arithmetic $(())", "medium"),
    ("Step 5: Shell Scripting", "Intermediate", "Exit codes, set -e & error handling", "medium"),
    ("Step 5: Shell Scripting", "Intermediate", "Heredoc & here-string", "easy"),
    ("Step 5: Shell Scripting", "Practical", "Cron jobs — crontab syntax & scheduling", "medium"),
    ("Step 5: Shell Scripting", "Practical", "Log rotation & cleanup scripts", "medium"),
    ("Step 5: Shell Scripting", "Practical", "Write a deploy/backup script from scratch", "hard"),

    # ---------------- Step 6: Networking & Security ----------------
    ("Step 6: Networking & Security", "Inspection", "ip, ifconfig, netstat & ss", "medium"),
    ("Step 6: Networking & Security", "Inspection", "curl & wget — HTTP from terminal", "easy"),
    ("Step 6: Networking & Security", "Inspection", "ping, traceroute & nslookup/dig", "easy"),
    ("Step 6: Networking & Security", "Inspection", "tcpdump & Wireshark basics", "hard"),
    ("Step 6: Networking & Security", "SSH", "SSH key generation & ssh-copy-id", "easy"),
    ("Step 6: Networking & Security", "SSH", "SSH config file — aliases & ProxyJump", "medium"),
    ("Step 6: Networking & Security", "SSH", "scp & rsync — file transfer", "easy"),
    ("Step 6: Networking & Security", "Firewall", "ufw & iptables — allow/block ports", "medium"),
    ("Step 6: Networking & Security", "Firewall", "fail2ban — brute-force protection", "medium"),

    # ---------------- Step 7: Performance & Disk ----------------
    ("Step 7: Performance & Disk", "Disk", "df, du & ncdu — disk usage", "easy"),
    ("Step 7: Performance & Disk", "Disk", "mount, umount & /etc/fstab", "medium"),
    ("Step 7: Performance & Disk", "Disk", "fdisk, lsblk & partition management", "hard"),
    ("Step 7: Performance & Disk", "Performance", "vmstat, iostat & sar", "hard"),
    ("Step 7: Performance & Disk", "Performance", "strace & ltrace — system call tracing", "hard"),
    ("Step 7: Performance & Disk", "Performance", "Tuning — swappiness, ulimit & file descriptors", "hard"),
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
            text("INSERT INTO roadmaps (id, title, description, created_at) VALUES (:id, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "title": TITLE, "desc": DESCRIPTION},
        )
        for i, (phase, section, title, tier) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes (id, roadmap_id, phase, section, title, tier, order_index) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx)"),
                {"id": str(uuid.uuid4()), "rid": str(ROADMAP_ID), "phase": phase,
                 "section": section, "title": title, "tier": tier, "idx": i},
            )
    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
