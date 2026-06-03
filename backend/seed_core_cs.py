"""
Seed script: Core CS as a RetainHQ roadmap (one roadmap, three sub-tracks).

Sub-tracks (rendered as the flowchart's step spine via `phase`):
  Operating Systems · DBMS · Computer Networks

These are prime spaced-repetition material — crisp factual recall (process
states, ACID, the TCP handshake). Each node carries a short recall hint in
`description` (shown in the node's notes popup).

Idempotent — deletes and recreates this roadmap each run.
Run: ./.venv/Scripts/python.exe seed_core_cs.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
TITLE = "Core CS — OS, DBMS & Networks"
DESCRIPTION = "The three core CS subjects that decide most placement & interview rounds. Built for active recall — short, factual, high-yield topics."

# (phase = sub-track, section, title, tier, recall hint)
NODES = [
    # ================= Operating Systems =================
    ("Operating Systems", "Fundamentals", "What an OS is & its functions", "easy", "Resource manager + abstraction: process, memory, file, I/O management."),
    ("Operating Systems", "Fundamentals", "Kernel, shell & system calls", "easy", "Kernel = core; system call = user→kernel gateway (fork, exec, wait, open)."),
    ("Operating Systems", "Fundamentals", "User mode vs kernel mode", "easy", "Dual mode + mode bit; privileged instructions only in kernel mode."),
    ("Operating Systems", "Processes & Threads", "Process vs program & the PCB", "easy", "Program = passive; process = active. PCB holds PID, state, registers, PC."),
    ("Operating Systems", "Processes & Threads", "Process states & transitions", "medium", "New → Ready → Running → Waiting → Terminated."),
    ("Operating Systems", "Processes & Threads", "Context switching", "medium", "Save/restore PCB; pure overhead, no useful work done."),
    ("Operating Systems", "Processes & Threads", "Thread vs process & benefits", "medium", "Threads share code/data/heap; cheaper context switch than processes."),
    ("Operating Systems", "Processes & Threads", "Multithreading models", "medium", "Many-to-one, one-to-one, many-to-many."),
    ("Operating Systems", "CPU Scheduling", "Scheduling criteria", "easy", "CPU utilisation, throughput, turnaround, waiting, response time."),
    ("Operating Systems", "CPU Scheduling", "FCFS & the convoy effect", "easy", "Non-preemptive; long job blocks short ones (convoy effect)."),
    ("Operating Systems", "CPU Scheduling", "SJF & SRTF", "medium", "Shortest job first; SRTF = preemptive SJF; optimal avg waiting time."),
    ("Operating Systems", "CPU Scheduling", "Round Robin & time quantum", "medium", "Preemptive; quantum too small = overhead, too large = FCFS."),
    ("Operating Systems", "CPU Scheduling", "Priority scheduling & starvation", "medium", "Starvation of low priority; fixed by aging."),
    ("Operating Systems", "Synchronisation", "Race condition & critical section", "medium", "CS needs mutual exclusion, progress, bounded waiting."),
    ("Operating Systems", "Synchronisation", "Peterson's solution", "hard", "Software mutual exclusion for 2 processes: flag[] + turn."),
    ("Operating Systems", "Synchronisation", "Mutex vs semaphore", "medium", "Mutex = lock (ownership); semaphore = counter (binary vs counting)."),
    ("Operating Systems", "Synchronisation", "Producer–consumer problem", "medium", "Bounded buffer with empty / full / mutex semaphores."),
    ("Operating Systems", "Synchronisation", "Reader–writer & dining philosophers", "hard", "Classic sync problems; avoid deadlock & starvation."),
    ("Operating Systems", "Deadlock", "Deadlock & 4 necessary conditions", "medium", "Mutual exclusion, hold & wait, no preemption, circular wait."),
    ("Operating Systems", "Deadlock", "Prevention vs avoidance", "medium", "Negate a condition vs stay in a safe state."),
    ("Operating Systems", "Deadlock", "Banker's algorithm", "hard", "Safe sequence from need / allocation / available matrices."),
    ("Operating Systems", "Deadlock", "Detection & recovery", "medium", "Wait-for graph; recover by kill or resource preemption."),
    ("Operating Systems", "Memory Management", "Contiguous allocation & fragmentation", "medium", "Internal vs external fragmentation; compaction."),
    ("Operating Systems", "Memory Management", "Paging & page tables", "medium", "Fixed frames; logical→physical; removes external fragmentation."),
    ("Operating Systems", "Memory Management", "TLB & effective access time", "medium", "Cache of page-table entries; EMAT from hit ratio."),
    ("Operating Systems", "Memory Management", "Segmentation", "medium", "Variable logical segments via a segment table."),
    ("Operating Systems", "Virtual Memory", "Demand paging & page faults", "medium", "Lazy load pages; fault → fetch from disk."),
    ("Operating Systems", "Virtual Memory", "Page replacement: FIFO / LRU / Optimal", "hard", "Belady's anomaly (FIFO); LRU approximates Optimal."),
    ("Operating Systems", "Virtual Memory", "Thrashing & working set", "hard", "High paging, low CPU util; working-set model."),
    ("Operating Systems", "Disk & Files", "Disk scheduling algorithms", "medium", "FCFS, SSTF, SCAN, C-SCAN, LOOK; minimise seek time."),
    ("Operating Systems", "Disk & Files", "File allocation methods", "easy", "Contiguous, linked, indexed."),

    # ================= DBMS =================
    ("DBMS", "Foundations", "DBMS vs file system", "easy", "Less redundancy; integrity, concurrency, security, recovery."),
    ("DBMS", "Foundations", "3-schema architecture & data independence", "medium", "External / conceptual / internal; logical vs physical independence."),
    ("DBMS", "Data Models", "ER model: entities, attributes, relationships", "easy", "Strong/weak entities; attribute types; cardinality."),
    ("DBMS", "Data Models", "ER → relational mapping", "medium", "Entities & relationships become tables; resolve M:N."),
    ("DBMS", "Data Models", "Keys: super / candidate / primary / foreign", "easy", "Uniqueness, minimality, referential integrity."),
    ("DBMS", "Data Models", "Relational algebra", "medium", "σ select, π project, ⋈ join, ∪, −."),
    ("DBMS", "SQL", "DDL, DML, DCL, TCL", "easy", "CREATE/ALTER; SELECT/INSERT; GRANT; COMMIT/ROLLBACK."),
    ("DBMS", "SQL", "Joins", "medium", "Inner, left, right, full, cross, self."),
    ("DBMS", "SQL", "Aggregates, GROUP BY & HAVING", "medium", "WHERE filters rows; HAVING filters groups."),
    ("DBMS", "SQL", "Subqueries & views", "medium", "Correlated subquery; view = virtual table."),
    ("DBMS", "Normalisation", "Functional dependencies & anomalies", "medium", "Insert/update/delete anomalies; Armstrong's axioms."),
    ("DBMS", "Normalisation", "1NF, 2NF, 3NF", "medium", "Atomic values; no partial dep; no transitive dep."),
    ("DBMS", "Normalisation", "BCNF & lossless decomposition", "hard", "Every determinant must be a candidate key."),
    ("DBMS", "Transactions", "ACID properties", "easy", "Atomicity, Consistency, Isolation, Durability."),
    ("DBMS", "Transactions", "Schedules & serializability", "hard", "Conflict vs view serializable; precedence graph."),
    ("DBMS", "Transactions", "Concurrency control: 2PL", "hard", "Growing & shrinking phases; strict 2PL avoids cascading aborts."),
    ("DBMS", "Transactions", "Recovery & logging", "medium", "Undo/redo logs, checkpoints, write-ahead logging."),
    ("DBMS", "Indexing", "B-tree & B+ tree", "hard", "B+ leaves are linked → efficient range queries."),
    ("DBMS", "Indexing", "Clustered vs non-clustered index", "medium", "Clustered orders the data; one per table."),

    # ================= Computer Networks =================
    ("Computer Networks", "Models", "OSI 7 layers", "easy", "Physical, Data Link, Network, Transport, Session, Presentation, Application."),
    ("Computer Networks", "Models", "TCP/IP model & layer functions", "easy", "Link, Internet, Transport, Application; maps onto OSI."),
    ("Computer Networks", "Data Link", "Framing & error detection", "medium", "Parity, checksum, CRC."),
    ("Computer Networks", "Data Link", "MAC, Ethernet & CSMA/CD", "medium", "Shared medium access; collision detection."),
    ("Computer Networks", "Data Link", "ARP", "medium", "Resolves IP → MAC address."),
    ("Computer Networks", "Network Layer", "IP addressing & classes", "easy", "IPv4 32-bit; classes A–E; public vs private."),
    ("Computer Networks", "Network Layer", "Subnetting & CIDR", "hard", "Subnet mask; VLSM; host vs network bits."),
    ("Computer Networks", "Network Layer", "IPv4 vs IPv6", "easy", "32-bit vs 128-bit; header differences."),
    ("Computer Networks", "Network Layer", "Routing: distance vector vs link state", "hard", "RIP (Bellman-Ford) vs OSPF (Dijkstra)."),
    ("Computer Networks", "Network Layer", "NAT & ICMP", "medium", "NAT maps private↔public; ping/traceroute use ICMP."),
    ("Computer Networks", "Transport Layer", "TCP vs UDP", "easy", "Reliable, ordered, connection-oriented vs fast, connectionless."),
    ("Computer Networks", "Transport Layer", "TCP 3-way handshake", "medium", "SYN → SYN-ACK → ACK; teardown via FIN."),
    ("Computer Networks", "Transport Layer", "Flow control & sliding window", "hard", "Receiver window; ARQ (stop-and-wait, Go-Back-N, SR)."),
    ("Computer Networks", "Transport Layer", "Congestion control", "hard", "Slow start, congestion avoidance, AIMD."),
    ("Computer Networks", "Application Layer", "HTTP / HTTPS & methods", "easy", "Stateless; GET/POST; status codes; HTTPS = HTTP over TLS."),
    ("Computer Networks", "Application Layer", "DNS", "medium", "Name → IP; recursive vs iterative; A/MX/CNAME records."),
    ("Computer Networks", "Application Layer", "DHCP", "easy", "DORA: Discover, Offer, Request, Ack."),
    ("Computer Networks", "Security", "Symmetric vs asymmetric encryption", "medium", "AES (shared key) vs RSA (public/private)."),
    ("Computer Networks", "Security", "SSL/TLS & firewalls", "medium", "Handshake + certificates; firewall filters traffic."),
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(
            text("INSERT INTO roadmaps (id, title, description, created_at) VALUES (:id, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "title": TITLE, "desc": DESCRIPTION},
        )
        for i, (phase, section, title, tier, desc) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes "
                     "(id, roadmap_id, phase, section, title, tier, order_index, description) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx, :desc)"),
                {"id": str(uuid.uuid4()), "rid": str(ROADMAP_ID), "phase": phase,
                 "section": section, "title": title, "tier": tier, "idx": i, "desc": desc},
            )
    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
