"""
Seed script: DevOps & Cloud roadmap for RetainHQ.
Idempotent — deletes and recreates the roadmap each run.
Run: ./.venv/Scripts/python.exe seed_devops_cloud.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("40404040-4040-4040-4040-404040404040")
TITLE = "DevOps & Cloud"
DESCRIPTION = "Docker → CI/CD → Kubernetes → AWS — the practical DevOps stack for backend engineers going into SWE or DevOps/SRE roles."

NODES = [
    # ---------------- Step 1: Linux & Networking Prereqs ----------------
    ("Step 1: Linux & Networking Prereqs", "Linux", "File system, permissions & common commands", "easy"),
    ("Step 1: Linux & Networking Prereqs", "Linux", "Processes — ps, kill, systemd & services", "easy"),
    ("Step 1: Linux & Networking Prereqs", "Linux", "Shell scripting basics for automation", "medium"),
    ("Step 1: Linux & Networking Prereqs", "Networking", "TCP/IP, DNS, HTTP/HTTPS & ports", "medium"),
    ("Step 1: Linux & Networking Prereqs", "Networking", "SSH — key auth, tunnels & port forwarding", "medium"),

    # ---------------- Step 2: Docker ----------------
    ("Step 2: Docker", "Basics", "Containers vs VMs — why Docker exists", "easy"),
    ("Step 2: Docker", "Basics", "Dockerfile — FROM, RUN, COPY, CMD & ENTRYPOINT", "easy"),
    ("Step 2: Docker", "Basics", "docker build, run, exec, logs & ps", "easy"),
    ("Step 2: Docker", "Basics", "Image layers & build cache — optimizing Dockerfiles", "medium"),
    ("Step 2: Docker", "Networking & Storage", "Docker networks — bridge, host & custom", "medium"),
    ("Step 2: Docker", "Networking & Storage", "Volumes & bind mounts — persistent data", "medium"),
    ("Step 2: Docker", "Compose", "docker-compose — multi-service local dev", "medium"),
    ("Step 2: Docker", "Compose", "Health checks, depends_on & environment files", "medium"),

    # ---------------- Step 3: CI/CD ----------------
    ("Step 3: CI/CD", "Concepts", "CI/CD pipeline stages — build, test, deploy", "easy"),
    ("Step 3: CI/CD", "GitHub Actions", "Workflow YAML — triggers, jobs & steps", "medium"),
    ("Step 3: CI/CD", "GitHub Actions", "Build & test on push — matrix strategy", "medium"),
    ("Step 3: CI/CD", "GitHub Actions", "Docker build & push to registry in Actions", "medium"),
    ("Step 3: CI/CD", "GitHub Actions", "Deploy to cloud on merge to main", "hard"),
    ("Step 3: CI/CD", "GitHub Actions", "Secrets, environments & approval gates", "medium"),
    ("Step 3: CI/CD", "Other Tools", "GitLab CI & Jenkins — concepts & comparison", "medium"),

    # ---------------- Step 4: Kubernetes ----------------
    ("Step 4: Kubernetes", "Core Concepts", "Why Kubernetes — orchestration problem", "easy"),
    ("Step 4: Kubernetes", "Core Concepts", "Pods, nodes & the control plane", "medium"),
    ("Step 4: Kubernetes", "Workloads", "Deployments — replicas, rolling updates & rollback", "medium"),
    ("Step 4: Kubernetes", "Workloads", "Services — ClusterIP, NodePort & LoadBalancer", "medium"),
    ("Step 4: Kubernetes", "Workloads", "ConfigMaps & Secrets", "easy"),
    ("Step 4: Kubernetes", "Workloads", "Persistent Volumes & PersistentVolumeClaims", "hard"),
    ("Step 4: Kubernetes", "Scaling", "HorizontalPodAutoscaler & resource requests/limits", "hard"),
    ("Step 4: Kubernetes", "Scaling", "Ingress — routing & TLS termination", "hard"),
    ("Step 4: Kubernetes", "Operations", "kubectl — get, describe, logs, exec & apply", "medium"),
    ("Step 4: Kubernetes", "Operations", "Helm — package manager for K8s", "hard"),

    # ---------------- Step 5: AWS Core Services ----------------
    ("Step 5: AWS Core Services", "Compute", "EC2 — instance types, AMIs & security groups", "medium"),
    ("Step 5: AWS Core Services", "Compute", "Lambda — serverless functions & triggers", "medium"),
    ("Step 5: AWS Core Services", "Compute", "ECS & EKS — managed containers on AWS", "hard"),
    ("Step 5: AWS Core Services", "Storage & DB", "S3 — buckets, policies & presigned URLs", "easy"),
    ("Step 5: AWS Core Services", "Storage & DB", "RDS — managed Postgres/MySQL & backups", "medium"),
    ("Step 5: AWS Core Services", "Storage & DB", "ElastiCache — Redis on AWS", "medium"),
    ("Step 5: AWS Core Services", "Networking", "VPC, subnets, IGW & NAT gateway", "hard"),
    ("Step 5: AWS Core Services", "Networking", "Route 53 — DNS & health checks", "medium"),
    ("Step 5: AWS Core Services", "Networking", "CloudFront — CDN & edge caching", "medium"),
    ("Step 5: AWS Core Services", "Security", "IAM — users, roles, policies & least privilege", "medium"),

    # ---------------- Step 6: Observability ----------------
    ("Step 6: Observability", "Pillars", "Logs, metrics & traces — the three pillars", "easy"),
    ("Step 6: Observability", "Tools", "Prometheus & Grafana — scrape, alert & dashboard", "medium"),
    ("Step 6: Observability", "Tools", "ELK / OpenSearch stack — centralized logs", "hard"),
    ("Step 6: Observability", "Tools", "Distributed tracing — OpenTelemetry & Jaeger", "hard"),
    ("Step 6: Observability", "SRE", "SLOs, SLAs & error budgets", "medium"),
    ("Step 6: Observability", "SRE", "On-call runbooks & incident response basics", "medium"),
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
