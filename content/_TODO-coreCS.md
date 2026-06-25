# Curation queue — Core CS: OS / DBMS / Networks (`core-cs`, `kind: "theory"`)

> **For Antigravity.** Generate **one JSON per node** using **`PROMPT-coreCS.md`** (`kind:"theory"` —
> analogy + explanation + recall; **no runtime, no formula, no method**). Files go in
> `content/roadmaps/core-cs/<slug>.json` (filename = slug). Reference exemplar:
> `content/roadmaps/core-cs/deadlock-conditions.json` (validated). Validate with
> `python content/validate.py`; tick a box once saved **and** green.

Source of truth: `backend/seed_core_cs.py`. **`company` tags = honest categories, never fabricated.**

## Evidence (why Core CS)
Round-1 ELIMINATOR for SDE + Backend (OA MCQ screens: S&P Global, Increff OS/DBMS/Networks 50-MCQ)
and a shared module feeding ~6 tracks. See `docs/jd-research-run1.md`.

## ⚠️ DBMS — SKIP the SQL-overlap nodes
The crossed-out DBMS nodes below are taught WITH a real runtime in the `sql` roadmap. Do NOT make
inferior no-runtime copies — skip them (link to the sql lesson instead). Build only genuine theory.


## Operating Systems
### Fundamentals
- [ ] What an OS is & its functions  →  `what-an-os-is-and-its-functions`
- [ ] Kernel, shell & system calls  →  `kernel-shell-and-system-calls`
- [ ] User mode vs kernel mode  →  `user-mode-vs-kernel-mode`
### Processes & Threads
- [ ] Process vs program & the PCB  →  `process-vs-program-and-the-pcb`
- [ ] Process states & transitions  →  `process-states-and-transitions`
- [ ] Context switching  →  `context-switching`
- [ ] Thread vs process & benefits  →  `thread-vs-process-and-benefits`
- [ ] Multithreading models  →  `multithreading-models`
### CPU Scheduling
- [ ] Scheduling criteria  →  `scheduling-criteria`
- [ ] FCFS & the convoy effect  →  `fcfs-and-the-convoy-effect`
- [ ] SJF & SRTF  →  `sjf-and-srtf`
- [ ] Round Robin & time quantum  →  `round-robin-and-time-quantum`
- [ ] Priority scheduling & starvation  →  `priority-scheduling-and-starvation`
### Synchronisation
- [ ] Race condition & critical section  →  `race-condition-and-critical-section`
- [ ] Peterson's solution  →  `peterson-s-solution`
- [ ] Mutex vs semaphore  →  `mutex-vs-semaphore`
- [ ] Producerâ€“consumer problem  →  `producer-consumer-problem`
- [ ] Readerâ€“writer & dining philosophers  →  `reader-writer-and-dining-philosophers`
### Deadlock
- [ ] Deadlock & 4 necessary conditions  →  `deadlock-and-4-necessary-conditions`
- [ ] Prevention vs avoidance  →  `prevention-vs-avoidance`
- [ ] Banker's algorithm  →  `banker-s-algorithm`
- [ ] Detection & recovery  →  `detection-and-recovery`
### Memory Management
- [ ] Contiguous allocation & fragmentation  →  `contiguous-allocation-and-fragmentation`
- [ ] Paging & page tables  →  `paging-and-page-tables`
- [ ] TLB & effective access time  →  `tlb-and-effective-access-time`
- [ ] Segmentation  →  `segmentation`
### Virtual Memory
- [ ] Demand paging & page faults  →  `demand-paging-and-page-faults`
- [ ] Page replacement: FIFO / LRU / Optimal  →  `page-replacement-fifo-lru-optimal`
- [ ] Thrashing & working set  →  `thrashing-and-working-set`
### Disk & Files
- [ ] Disk scheduling algorithms  →  `disk-scheduling-algorithms`
- [ ] File allocation methods  →  `file-allocation-methods`

## DBMS
### Foundations
- [ ] DBMS vs file system  →  `dbms-vs-file-system`
- [ ] 3-schema architecture & data independence  →  `3-schema-architecture-and-data-independence`
### Data Models
- [ ] ER model: entities, attributes, relationships  →  `er-model-entities-attributes-relationships`
- [ ] ER â†’ relational mapping  →  `er-relational-mapping`
- ~~Keys: super / candidate / primary / foreign  →  `keys-super-candidate-primary-foreign`~~  *(SKIP — covered by the `sql` roadmap)*
- [ ] Relational algebra  →  `relational-algebra`
### SQL
- ~~DDL, DML, DCL, TCL  →  `ddl-dml-dcl-tcl`~~  *(SKIP — covered by the `sql` roadmap)*
- ~~Joins  →  `joins`~~  *(SKIP — covered by the `sql` roadmap)*
- ~~Aggregates, GROUP BY & HAVING  →  `aggregates-group-by-and-having`~~  *(SKIP — covered by the `sql` roadmap)*
- ~~Subqueries & views  →  `subqueries-and-views`~~  *(SKIP — covered by the `sql` roadmap)*
### Normalisation
- [ ] Functional dependencies & anomalies  →  `functional-dependencies-and-anomalies`
- ~~1NF, 2NF, 3NF  →  `1nf-2nf-3nf`~~  *(SKIP — covered by the `sql` roadmap)*
- ~~BCNF & lossless decomposition  →  `bcnf-and-lossless-decomposition`~~  *(SKIP — covered by the `sql` roadmap)*
### Transactions
- [ ] ACID properties  →  `acid-properties`
- [ ] Schedules & serializability  →  `schedules-and-serializability`
- [ ] Concurrency control: 2PL  →  `concurrency-control-2pl`
- [ ] Recovery & logging  →  `recovery-and-logging`
### Indexing
- [ ] B-tree & B+ tree  →  `b-tree-and-b-tree`
- ~~Clustered vs non-clustered index  →  `clustered-vs-non-clustered-index`~~  *(SKIP — covered by the `sql` roadmap)*

## Computer Networks
### Models
- [ ] OSI 7 layers  →  `osi-7-layers`
- [ ] TCP/IP model & layer functions  →  `tcp-ip-model-and-layer-functions`
### Data Link
- [ ] Framing & error detection  →  `framing-and-error-detection`
- [ ] MAC, Ethernet & CSMA/CD  →  `mac-ethernet-and-csma-cd`
- [ ] ARP  →  `arp`
### Network Layer
- [ ] IP addressing & classes  →  `ip-addressing-and-classes`
- [ ] Subnetting & CIDR  →  `subnetting-and-cidr`
- [ ] IPv4 vs IPv6  →  `ipv4-vs-ipv6`
- [ ] Routing: distance vector vs link state  →  `routing-distance-vector-vs-link-state`
- [ ] NAT & ICMP  →  `nat-and-icmp`
### Transport Layer
- [ ] TCP vs UDP  →  `tcp-vs-udp`
- [ ] TCP 3-way handshake  →  `tcp-3-way-handshake`
- [ ] Flow control & sliding window  →  `flow-control-and-sliding-window`
- [ ] Congestion control  →  `congestion-control`
### Application Layer
- [ ] HTTP / HTTPS & methods  →  `http-https-and-methods`
- [ ] DNS  →  `dns`
- [ ] DHCP  →  `dhcp`
### Security
- [ ] Symmetric vs asymmetric encryption  →  `symmetric-vs-asymmetric-encryption`
- [ ] SSL/TLS & firewalls  →  `ssl-tls-and-firewalls`

---

**Build 61 theory nodes; skip 8 SQL-overlap DBMS nodes.**
Suggested order: OS (highest analogy payoff) → Networks → DBMS-theory. `deadlock-conditions` is done — skip it.
Prereqs are mostly light; set `prerequisites` only where one concept truly needs another.

## Wiring (Claude-side, not Antigravity)
Renderer: the `kind:"theory"` `LessonView` path (done). Roadmap slug `core-cs` = content folder key,
so URLs resolve directly. `sync-content.mjs` copies the dir; live on next push.