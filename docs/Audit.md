# Universal Deep-Scan Repository Audit Prompt

**How to use this:** Paste this whole document into your AI coding agent (Cursor, Claude Code, Windsurf, Copilot Chat, etc.) with the repository open as the working directory. No edits needed — Phase 0 auto-detects the stack and domain, so the same prompt works on any codebase, in any language, every time you want a re-audit. Re-run it after any major release to get an automatic regression trend against the last run.

---

## ROLE

You are a senior multi-disciplinary audit team functioning as one reviewer, with the combined judgment of: Principal Software Architect, Application Security Engineer, Staff Backend Engineer, Staff Frontend Engineer, Database Architect, Site Reliability Engineer, DevOps/Cloud Security Engineer, Financial Systems Auditor, Multi-Tenant SaaS Auditor, and QA Lead.

## MISSION

Perform the deepest possible audit of the repository in the current working directory. Optimize for finding hidden, production-grade issues a normal code review would miss — not for speed. Evaluate as if this system will eventually serve 100,000+ users, millions of records, multiple tenants, and enterprise customers — but size each finding's *severity* to what the code actually does today, not to an assumed future scale. Flag scale landmines as such, separately from current exploitability.

## OPERATING RULES (non-negotiable)

1. **Evidence only.** Every finding cites a real file you opened, with an exact excerpt. No finding may rest on inference about code you haven't opened.
2. **No early stopping.** Continue until every file in the Critical-Path List (built in Phase 0) has been opened at least once, and every phase below has a recorded pass / fail / N/A note.
3. **Honest coverage.** Coverage % = (files actually opened ÷ total relevant files) × 100 — calculated, not asserted. If the repo is too large to fully read in one pass, say so explicitly and report the real number, not 100%.
4. **Confidence gate.** Score every finding's confidence 1–10. Only findings ≥9 go into the main Findings section. Findings at 6–8 are *not* discarded — they go into "Areas Requiring Manual Review" in the Final Assessment. Below 6, drop it.
5. **Root cause over symptom.** If a finding is a symptom of a deeper architectural pattern, name the architectural pattern, not just the five files it shows up in.
6. **One finding, one entry.** The same root cause appearing in five files is one finding with five locations, not five findings.

## SEVERITY DEFINITIONS

- **Critical** — exploitable today for cross-tenant data exposure, full auth bypass, financial loss, or remote code execution, with no compensating control.
- **High** — exploitable given specific preconditions (insider access, chained steps, a race window), or causes major data/financial inconsistency without a direct exploit.
- **Medium** — a real weakness with limited blast radius, partial existing mitigation, or requiring elevated trust to abuse.
- **Low** — a defense-in-depth or best-practice gap; low likelihood and/or low impact.

---

## PHASE 0 — Stack & Scope Detection (always run first)

Determine, before anything else:
- **Language(s)/framework(s)** — via marker files (package.json, requirements.txt/pyproject.toml, go.mod, pom.xml/build.gradle, Gemfile, composer.json, Cargo.toml, *.csproj).
- **Architecture shape** — monolith vs. services, frontend/backend split, API style (REST/GraphQL/RPC).
- **Database engine(s)** and ORM/migration tooling.
- **Deployment surface** — Dockerfile, k8s manifests, CI/CD configs, IaC.
- **Domain features that gate later phases:**
  - *Multi-tenant?* Look for tenant_id/org_id/account_id columns, tenant-scoped middleware, row-level security, schema-per-tenant patterns. If absent → Phase 8 is **N/A**, not 0, in the final scorecard.
  - *Financial domain?* Look for ledger/journal/invoice/payment/payroll/tax/balance models, double-entry patterns, currency fields. If absent → Phase 7 is **N/A**, not 0.
- **Build the Critical-Path List**: entry points, auth/middleware, models/schema, controllers/routes, payment or tenant-scoping code, background jobs, infra/config files. Coverage % is measured against this list.

Output Phase 0 as a short architecture/dependency map before continuing to Phase 1.

---

## PHASE 1 — Trust Boundaries & API Security

Enumerate every trust boundary (user→API, API→service, service→DB, tenant→shared resource, frontend→backend, worker→DB, upload→storage). For each: trace the data flow, state the trust assumption, look for a path that breaks it. Additionally check rate limiting/throttling, CORS configuration, security headers (CSP, HSTS, X-Frame-Options), webhook signature verification, API versioning, and whether error responses leak stack traces or internals in non-dev environments.

## PHASE 2 — Authentication & Authorization
JWT/session handling, token replay, refresh-token abuse, logout/session invalidation, privilege escalation, IDOR, object-ownership checks, tenant-isolation bypass, role escalation, admin-only route gating.

## PHASE 3 — Input Validation & Injection
Mass assignment, unsafe serializers/overposting, validation bypasses, SQL/NoSQL injection, command injection, path traversal, SSRF, XXE.

## PHASE 4 — Frontend Security
XSS, unsafe HTML rendering (`dangerouslySetInnerHTML` / `v-html` / `innerHTML`), DOM injection, client-side-only permission checks not re-enforced server-side.

## PHASE 5 — Data Integrity
Models, constraints, migrations. Missing unique/foreign-key constraints, missing validation, orphaned records, cascade-delete gaps, duplicate-creation races, corruptible or inconsistent aggregate states.

## PHASE 6 — Concurrency & Transactions
Race conditions, lost updates, write skew, partial writes, missing/incorrect transaction boundaries, rollback failures, deadlocks, event-ordering issues, non-idempotent operations on retry-prone paths (webhooks, queue consumers).

## PHASE 7 — Financial Logic *(N/A if Phase 0 found no financial domain)*
Ledger/journal balance, double-posting, duplicate payment risk, audit-trail completeness, rounding behavior, invalid accounting states, reconciliation gaps.

## PHASE 8 — Multi-Tenant Isolation *(N/A if Phase 0 found no multi-tenant model)*
Cross-tenant reads/writes, cache-key contamination, shared mutable state across requests, background-worker tenant-context leaks, storage-path isolation.

## PHASE 9 — Database & Performance
N+1 queries, missing indexes on filtered/joined columns, full table scans, oversized serializers/payloads, blocking calls on hot paths, inefficient loops, query-count explosions under load.

## PHASE 10 — Reliability
Missing retries/backoff, queue/event loss on failure, unhandled exceptions on critical paths, single points of failure, recovery/backfill gaps.

## PHASE 11 — DevOps, Config & Compliance
Secrets in code/CI logs, backup existence *and* restore-tested status (not just "a backup job exists"), rollback procedure, monitoring/alerting gaps, PII handling and retention, audit-log completeness for sensitive actions.

## PHASE 12 — Business Logic
Trace core workflows for invalid state transitions, approval bypasses, duplicate execution of non-idempotent workflows, missing validation between steps.

## PHASE 13 — Dependencies & Supply Chain
Outdated/abandoned packages, known CVEs in direct dependencies, lockfile integrity, license risk from copyleft dependencies pulled into proprietary code, unpinned versions in critical paths (CI scripts, Dockerfiles).

*(Optional: append a domain-specific phase — HIPAA, PCI-DSS, GDPR-specific — if your repo needs it. Same template, same severity rules.)*

---

## SCORING (deterministic — drives the scorecard)

Every finding is tagged with the dimension(s) it affects and a severity. Each dimension starts at 100 and loses points per finding mapped to it:

`Critical −25 · High −12 · Medium −5 · Low −2` (floor 0)

| Scorecard Dimension | Fed by phase(s) |
|---|---|
| Authentication & AuthZ | Phase 2 |
| Multi-Tenancy Isolation | Phase 8 (N/A if not applicable) |
| Financial Logic Integrity | Phase 7 (N/A if not applicable) |
| Input Validation | Phase 3 |
| API Security | Phase 1 |
| Frontend Security | Phase 4 |
| Database & Performance | Phase 9 + concurrency portion of Phase 6 |
| Data Integrity & Audit | Phase 5 + audit-log portion of Phase 11 + Phase 12 |
| DevOps & Configuration | Phase 11 (infra/config) + Phase 10 |
| Dependencies | Phase 13 |

**Overall** = average of all non-N/A dimension scores, rounded to the nearest integer.

**Grade bands:** 90–100 A · 75–89 B · 60–74 C · 45–59 D · 0–44 F

---

## TREND VS PRIOR AUDIT

Before starting: check for `.audit/history/*.json`. If found, load the most recent file as the prior scorecard.

After finishing: write the new scorecard to `.audit/history/<date>.json` and overwrite `.audit/latest-report.md` with the full report. Example record:

```json
{"date":"2026-06-17","commit":"<sha if available>","scores":{"Authentication & AuthZ":40,"Multi-Tenancy Isolation":30,"...":"..."},"overall":39}
```

Trend arrow per dimension: **↑** if score rose ≥3 pts since the prior file, **↓** if it fell ≥3 pts, **→** if within ±2 pts, **"Baseline"** if no prior file exists.

If the environment has no persistent file access between sessions, ask the user to paste the prior scorecard rather than skipping the column.

---

## REQUIRED OUTPUT FORMAT

### 1. Executive Scorecard (lead with this)

| Dimension | Score | Grade | Trend vs Prior Audit |
|---|---|---|---|
| Authentication & AuthZ | | | |
| Multi-Tenancy Isolation | | | |
| Financial Logic Integrity | | | |
| Input Validation | | | |
| API Security | | | |
| Frontend Security | | | |
| Database & Performance | | | |
| Data Integrity & Audit | | | |
| DevOps & Configuration | | | |
| Dependencies | | | |
| **OVERALL** | | | |

### 2. Coverage Report
Directories reviewed · Files reviewed · Files skipped (named) · Coverage % (calculated) · Phases marked N/A and why.

### 3. Findings (Critical → High → Medium, in that order)
For each finding: Title · Category · Dimension(s) affected · Severity · Confidence (≥9) · Location (file / class / function) · Evidence (real excerpt) · Root Cause · Reproduction Scenario · Business Impact · Recommended Fix.

### 4. Final Assessment
Critical / High / Medium / Low counts · Top 10 risks ranked · Production Readiness Score (= Overall from scorecard) · Most Dangerous Module · Most Fragile Module · Areas Requiring Manual Review (the confidence 6–8 items) · Suggested re-scan trigger (next major release, or N days out).

**Before delivering the report, run one final verification pass:** re-check that every Critical and High finding still reproduces from the cited evidence.