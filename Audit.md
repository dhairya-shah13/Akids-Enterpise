# Universal Deep-Scan Repository Audit Prompt

**How to use this:** Paste this whole document into your AI coding agent (Cursor, Claude Code, Windsurf, Copilot Chat, etc.) with the repository open as the working directory. No edits needed — Phase 0 auto-detects the stack and domain, so the same prompt works on any codebase, in any language, every time you want a re-audit. Re-run it after any major release to get an automatic regression trend against the last run.

**Multi-repo systems (e.g. separate frontend/backend repos):** If your agent can only open one working directory at a time, run this prompt once per repo, then merge the resulting reports under a single Executive Scorecard before final delivery. Note in Phase 0 which repo is authoritative for business logic, if the split is asymmetric (e.g. a backend-authoritative / frontend-presentation-only architecture) — this changes how you weight Phase 4 findings (see Phase 4 note).

---

## ROLE

You are a senior multi-disciplinary audit team functioning as one reviewer, with the combined judgment of: Principal Software Architect, Application Security Engineer, Staff Backend Engineer, Staff Frontend Engineer, Database Architect, Site Reliability Engineer, DevOps/Cloud Security Engineer, Financial Systems Auditor, Multi-Tenant SaaS Auditor, and QA Lead.

## MISSION

Perform the deepest possible audit of the repository in the current working directory. Optimize for finding hidden, production-grade issues a normal code review would miss — not for speed. Evaluate as if this system will eventually serve 100,000+ users, millions of records, multiple tenants, and enterprise customers — but size each finding's *severity* to what the code actually does today, not to an assumed future scale. Flag scale landmines as such, separately from current exploitability.

Before diving into generic phases, spend one sentence in Phase 0 naming this system's **core trust promise** — the one guarantee that, if broken, would be the worst possible outcome for its users (e.g. "a customer can never see another customer's invoices," "a student can never see another student's grades," "a trade can never execute twice"). Read every subsequent phase through that lens first, generic security/quality concerns second.

## OPERATING RULES (non-negotiable)

1. **Evidence only.** Every finding cites a real file you opened, with an exact excerpt. No finding may rest on inference about code you haven't opened. Where automated tooling exists in the environment (dependency/CVE scanners, secret scanners such as gitleaks/trufflehog, SAST tools such as semgrep), the agent must run it and treat its output as additional evidence, not a substitute for manual review.
2. **No early stopping.** Continue until every file in the Critical-Path List (built in Phase 0) has been opened at least once, and every phase below has a recorded pass / fail / N/A note.
3. **Honest coverage.** Coverage % = (files actually opened ÷ total relevant files) × 100 — calculated, not asserted. If the repo is too large to fully read in one pass, say so explicitly and report the real number, not 100%.
4. **Confidence gate.** Score every finding's confidence 1–10. Only findings ≥9 go into the main Findings section. Findings at 6–8 are *not* discarded — they go into "Areas Requiring Manual Review" in the Final Assessment. Below 6, drop it.
5. **Root cause over symptom.** If a finding is a symptom of a deeper architectural pattern, name the architectural pattern, not just the five files it shows up in.
6. **One finding, one entry.** The same root cause appearing in five files is one finding with five locations, not five findings.
7. **Regression-aware.** If prior audit history exists (`.audit/history/*.json` and/or a "Known Prior Fixes" list from a previous run), explicitly re-verify each previously-fixed issue still holds. A re-introduced regression is automatically bumped one severity tier above what it would otherwise score, regardless of how minor the triggering diff looks.

## SEVERITY DEFINITIONS

- **Critical** — exploitable today for cross-tenant/cross-user data exposure, full auth bypass, financial loss, RCE, or a regression of a previously-fixed issue, with no compensating control.
- **High** — exploitable given specific preconditions (insider access, chained steps, a race window), or causes major data/financial inconsistency without a direct exploit.
- **Medium** — a real weakness with limited blast radius, partial existing mitigation, or requiring elevated trust to abuse.
- **Low** — a defense-in-depth or best-practice gap; low likelihood and/or low impact.

---

## PHASE 0 — Stack & Scope Detection (always run first)

Determine, before anything else:
- **Language(s)/framework(s)** — via marker files (package.json, requirements.txt/pyproject.toml, go.mod, pom.xml/build.gradle, Gemfile, composer.json, Cargo.toml, *.csproj).
- **Architecture shape** — monolith vs. services, frontend/backend split, API style (REST/GraphQL/RPC), and whether one side is authoritative for business logic (check for an explicit architecture doc/README/context file stating this).
- **Database engine(s)** and ORM/migration tooling.
- **Deployment surface** — Dockerfile, k8s manifests, CI/CD configs, IaC.
- **This system's core trust promise** (one sentence — see MISSION).
- **Domain features that gate later phases:**
  - *Multi-tenant?* Look for tenant_id/org_id/account_id columns, tenant-scoped middleware, row-level security, schema-per-tenant patterns, **or an analogous per-user/per-cohort ownership-isolation model even without formal tenancy** (e.g. a single-org app where user A must never read user B's records). If a genuine isolation boundary of *either* kind exists → run Phase 8 under that model. If truly absent (e.g. a single-user local tool) → Phase 8 is **N/A**, not 0.
  - *Financial domain?* Look for ledger/journal/invoice/payment/payroll/tax/balance models, double-entry patterns, currency fields. If absent → Phase 7 is **N/A**, not 0.
- **Prior audit history:** Check for `.audit/history/*.json`, a CHANGELOG, or any "known fixes / security patch" notes in project docs (README, context files, CONTRIBUTING). If found, extract a short **Known Prior Fixes** list — specific, previously-fixed issues to explicitly re-verify (see Operating Rule 7). If nothing is found, state that explicitly and skip this list rather than inventing one.
- **Build the Critical-Path List**: entry points, auth/middleware, models/schema, controllers/routes, payment or tenant/ownership-scoping code, background jobs, file/data-import pipelines, infra/config files. Coverage % is measured against this list.

Output Phase 0 as a short architecture/dependency map — including the core trust promise and any Known Prior Fixes list — before continuing to Phase 1. If a project-level RULES.md (or equivalent agent-operating-rules file) is present in the repository, findings from this audit that are selected for remediation must be handed off as an Implementation Plan under that document's approval process — this document produces findings, it does not authorize fixes.

---

## PHASE 1 — Trust Boundaries & API Security

Enumerate every trust boundary (user→API, API→service, service→DB, tenant/user→shared resource, frontend→backend, worker→DB, upload→storage, third-party webhook→app). For each: trace the data flow, state the trust assumption, look for a path that breaks it. Additionally check rate limiting/throttling, CORS configuration, security headers (CSP, HSTS, X-Frame-Options), webhook signature verification, API versioning, and whether error responses leak stack traces or internals in non-dev environments.

## PHASE 2 — Authentication & Authorization
Session/token handling (cookies, JWT, API keys), token replay, refresh-token abuse, logout/session invalidation, privilege escalation, IDOR, object-ownership checks, tenant-isolation bypass, role escalation, admin-only route gating. Cross-reference every documented endpoint against its actual guard/middleware — flag any endpoint whose access control can't be located in code.

## PHASE 3 — Input Validation & Injection
Mass assignment, unsafe serializers/overposting, validation bypasses, SQL/NoSQL injection, command injection, path traversal, SSRF, XXE, file-upload abuse (type/size/content spoofing), formula/CSV injection in exports.

## PHASE 4 — Frontend Security
XSS, unsafe HTML rendering (`dangerouslySetInnerHTML` / `v-html` / `innerHTML`), DOM injection, and — this is the highest-value check when the architecture has a designated business-logic layer — **client-side-only permission/validation checks not re-enforced server-side**. For every disabled-button, route-guard, or hidden-field condition found client-side, confirm a matching server-side enforcement exists; an unmatched one is a finding regardless of how unreachable it looks from the current UI.

## PHASE 5 — Data Integrity
Models, constraints, migrations. Missing unique/foreign-key constraints, missing validation, orphaned records, cascade-delete gaps, duplicate-creation races, corruptible or inconsistent aggregate states.

## PHASE 6 — Concurrency & Transactions
Race conditions, lost updates, write skew, partial writes, missing/incorrect transaction boundaries, rollback failures, deadlocks, event-ordering issues, non-idempotent operations on retry-prone paths (webhooks, queue consumers, re-run imports).

## PHASE 7 — Financial Logic *(N/A if Phase 0 found no financial domain)*
Ledger/journal balance, double-posting, duplicate payment risk, audit-trail completeness, rounding behavior, invalid accounting states, reconciliation gaps.

## PHASE 8 — Tenant / Ownership Isolation *(N/A if Phase 0 found no isolation boundary)*
Cross-tenant or cross-user reads/writes, cache-key contamination, shared mutable state across requests (module-level/singleton state that should be request-scoped), background-worker context leaks, storage-path isolation, and — for probabilistic or fuzzy-matched ownership links (e.g. matching a login to a record by email/name rather than a strict foreign key) — adversarial testing of the matching logic itself, not just the downstream access check.

## PHASE 9 — Database & Performance
N+1 queries, missing indexes on filtered/joined columns, full table scans, oversized serializers/payloads, blocking calls on hot paths, inefficient loops, query-count explosions under load.

## PHASE 10 — Reliability
Missing retries/backoff, queue/event loss on failure, unhandled exceptions on critical paths, single points of failure, recovery/backfill gaps, graceful degradation on external-dependency failure (DB, third-party API).

## PHASE 11 — DevOps, Config & Compliance
Secrets in code/CI logs/`.env.example`, whether dev-only conveniences (verbose logging, permissive CORS, console-logged credentials/links) are actually gated by environment and can't leak to production, backup existence *and* restore-tested status (not just "a backup job exists"), rollback procedure, monitoring/alerting gaps, PII handling and retention, audit-log completeness for sensitive actions.

## PHASE 12 — Business Logic
Trace core workflows (state machines, approval chains, multi-step processes) for invalid state transitions, approval bypasses, duplicate execution of non-idempotent workflows, missing validation between steps, and forged-role/forged-state attempts against each transition endpoint (don't just assume a guard works — trace it).

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
| Tenant / Ownership Isolation | Phase 8 (N/A if not applicable) |
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

Before starting: check for `.audit/history/*.json`. If found, load the most recent file as the prior scorecard and extract the Known Prior Fixes list (Phase 0).

After finishing: write the new scorecard to `.audit/history/<date>.json` and overwrite `.audit/latest-report.md` with the full report. In addition, append a `### [Category: Audit] — {short summary}` subsection to the shared `Changelog.md` (see RULES.md §8.1) — under the current run's `## [YYYY-MM-DD HH:MM]` heading if one already exists for this session, or a new one if not — summarizing the audit's overall score, critical/high finding count, and a link/reference to `.audit/latest-report.md`. Update the `## Audit` subsection of the shared `Context.md` with the current scorecard and open findings count. Example record:

```json
{"date":"2026-08-05","commit":"<sha if available>","scores":{"Authentication & AuthZ":40,"Tenant / Ownership Isolation":30,"...":"..."},"overall":39}
```

Trend arrow per dimension: **↑** if score rose ≥3 pts since the prior file, **↓** if it fell ≥3 pts, **→** if within ±2 pts, **"Baseline"** if no prior file exists.

If the environment has no persistent file access between sessions, ask the user to paste the prior scorecard rather than skipping the column.

---

## REQUIRED OUTPUT FORMAT

### 1. Executive Scorecard (lead with this)

| Dimension | Score | Grade | Trend vs Prior Audit |
|---|---|---|---|
| Authentication & AuthZ | | | |
| Tenant / Ownership Isolation | | | |
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

### 3. Known Prior Fixes — Regression Check
*(Skip this section entirely if Phase 0 found no prior audit history/changelog to draw from — do not fabricate entries.)*
A short pass/fail table against each previously-fixed issue identified in Phase 0, with file/line evidence confirming it still holds (or a bumped-severity finding in Section 4 if it doesn't).

### 4. Findings (Critical → High → Medium, in that order)
For each finding: Title · Category · Dimension(s) affected · Severity · Confidence (≥9) · Location (file / class / function) · Evidence (real excerpt) · Root Cause · Reproduction Scenario · Business Impact (framed in terms of who is harmed and how, in plain language) · Recommended Fix.

### 5. Final Assessment
Critical / High / Medium / Low counts · Top 10 risks ranked · Production Readiness Score (= Overall from scorecard) · Most Dangerous Module · Most Fragile Module · Areas Requiring Manual Review (the confidence 6–8 items) · Suggested re-scan trigger (next major release, or N days out).

**Before delivering the report, run one final verification pass:** re-check that every Critical and High finding still reproduces from the cited evidence, and re-confirm every Known Prior Fix verdict against the actual code one more time.