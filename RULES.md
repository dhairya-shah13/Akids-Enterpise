# RULES.md — Agent Operating Rules

These rules govern how any AI coding agent must operate on this project. They are
non-negotiable unless explicitly overridden, in writing, by the project owner for a
specific task.

---

## 1. Clarification & Communication

1.1 If any instruction is ambiguous, incomplete, or open to more than one reasonable
interpretation, the agent **must stop and ask** for clarification before proceeding.
Guessing intent is not acceptable when the guess could lead to rework or risk.

1.2 If a prompt implies a decision with real trade-offs (architecture, library choice,
data model, security posture, cost), the agent must surface the options and ask,
rather than silently picking one.

1.3 The agent must clearly state any assumptions it is making, even for small
decisions it did proceed with unprompted.

---

## 2. Planning Before Execution

2.1 For **every** prompt that results in code being written, edited, or deleted, the
agent must first produce an **Implementation Plan** covering:
   - What will change (files, modules, components)
   - Why it's being changed (linked to the request)
   - Approach / design decisions and alternatives considered
   - Risks, edge cases, and security or performance implications
   - Any new dependencies being introduced and why

2.2 The agent must **not** write, edit, or delete any code until the Implementation
Plan has been explicitly approved by the project owner.

2.3 This applies every time — no skipping the plan step for "small" changes, quick
fixes, or repeated similar tasks. Each run gets its own plan and its own approval.

2.4 If, mid-implementation, the actual work starts to diverge meaningfully from the
approved plan, the agent must pause and get re-approval for the deviation.

---

## 3. Security

3.1 The agent must treat security as a first-class requirement, not an afterthought,
for every feature — not just "security features."

3.2 Minimum baseline the agent must actively defend against:
   - Injection attacks (SQL, NoSQL, command, XSS, template injection)
   - CSRF on all state-changing requests
   - Broken authentication/authorization (including insecure direct object references)
   - Insecure deserialization
   - Sensitive data exposure (secrets, PII, tokens in logs, source, or client bundles)
   - Insecure file uploads (type validation, size limits, storage location)
   - Missing rate limiting / brute-force protection on auth and public endpoints
   - Clickjacking, MIME sniffing, and other missing security headers (CSP, HSTS,
     X-Frame-Options, X-Content-Type-Options, Referrer-Policy)

3.3 All user input must be validated and sanitized server-side, regardless of any
client-side validation already in place.

3.4 Secrets, API keys, and credentials must never be hardcoded or committed. They
belong in environment variables or a secrets manager, and `.env`-style files must be
gitignored.

3.5 Dependencies must be kept free of known critical/high vulnerabilities; the agent
should flag outdated or vulnerable packages when it encounters them, even if unrelated
to the current task.

3.6 Authentication and authorization checks must be enforced on every relevant
endpoint/route — never assume a check upstream is sufficient.

3.7 If a request would require weakening a security control (e.g., disabling CSRF,
loosening CORS to `*`, exposing an admin route without auth), the agent must flag the
risk explicitly and get sign-off before doing it.

---

## 4. Responsiveness & UX

4.1 All UI must work correctly and look intentional across breakpoints — mobile,
tablet, and desktop — not just the viewport the agent happened to test in.

4.2 The agent must account for varying input methods (touch, mouse, keyboard) and
never rely on hover-only interactions for critical functionality.

4.3 Accessibility is part of "good UX for all users," not a separate concern:
   - Semantic HTML and proper ARIA where semantic HTML isn't enough
   - Sufficient color contrast
   - Full keyboard navigability
   - Meaningful alt text and labels
   - Respect for reduced-motion preferences where animation is used

4.4 Loading states, empty states, and error states must be designed, not left as
blank screens or raw error dumps.

4.5 The agent should sanity-check layouts at common breakpoints (e.g., ~375px,
~768px, ~1024px, ~1440px) before considering a UI task complete.

---

## 5. Code Quality

5.1 Code must be clean, readable, and consistently formatted according to the
project's existing style/linter config (or a sensible standard if none exists yet).

5.2 Comments must explain **why**, not just restate **what** the code does. Non-obvious
logic, workarounds, and business-rule-driven decisions must always be commented.

5.3 No dead code, no commented-out code left behind "just in case," and no
placeholder/TODO logic left silently in a completed deliverable — TODOs must be
called out explicitly to the project owner.

5.4 Naming (variables, functions, files, components) must be descriptive and
consistent with existing project conventions.

---

## 6. DRY — Don't Repeat Yourself

6.1 If a block of logic, UI component, or utility already exists that fulfills (or can
be generalized to fulfill) the current need, it must be reused — not re-implemented.

6.2 Before writing new logic, the agent must check whether equivalent logic already
exists elsewhere in the codebase.

6.3 If the agent notices during a task that similar logic is duplicated in multiple
places, it should flag this and propose a refactor (subject to the normal
plan-approval process — refactors are not exempt from Section 2).

6.4 No spaghetti code: control flow should be traceable, functions/components should
have a single clear responsibility, and deep nested conditionals should be refactored
into named, testable units where reasonable.

6.5 No pointless code: no unnecessary abstraction layers, no premature
generalization, no code added "in case it's needed later" without a stated reason.

---

## 7. Sub-Agent / Directory-Specific Rules

7.1 Any agent working within, or generating code that lives in, the `ponytail/`
directory must additionally follow all rules defined within that directory's own
rules file(s). Those rules supplement — and where more specific, take precedence
over — the general rules in this document for code scoped to that directory.

7.2 If rules in `ponytail/` conflict with this document in a way that can't be
reconciled, the agent must flag the conflict and ask rather than silently choosing
one set over the other.

---

## 8. Required Documentation

The agent must maintain the following three documents at the project root, and
**every task that changes the project must update the relevant doc(s) before the task
is considered complete.**

### 8.1 `Context.md`
A living, detailed reference of the project's current state, kept accurate at all
times. Must include, at minimum:
   - Current folder / file structure
   - Full feature list (implemented, in-progress, planned)
   - Architecture overview (stack, key libraries, data flow, external services)
   - Key conventions and patterns used in the codebase
   - Anything a new developer or a new agent would need to get oriented without
     asking questions

**Update rule:** `Context.md` must be updated after *every* change to the project,
without fail — structural changes, new features, removed features, and dependency
changes all count.

### 8.2 `Changelog.md`
A running log of every change made, in reverse-chronological order. Each entry must
follow this format:

```
## [Change Title] — DATE, TIME

### What changed
Detailed description of every change made in this run.

### Why
The reasoning/requirement behind the change.

### Bug fixed (if applicable)
What the bug was.

### Root cause (if applicable)
What actually caused the bug.
```

**Update rule:** A new entry must be added for every run/session in which the agent
makes changes — no batching multiple sessions into one vague entry.

### 8.3 `Readme.md`
The standard project README: what the project is, how to set it up, how to run it,
how to build/deploy it, and any other information a new contributor needs to get
started. Must be kept in sync with reality — no stale setup instructions.

---

## 9. Priority of Rules

If any instruction from the project owner directly conflicts with these rules, the
agent must point out the conflict and ask for explicit confirmation before proceeding
— it must not silently break a rule (especially Sections 2 and 3) just because it was
asked to move fast.