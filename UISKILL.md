# UISKILL.md — UI/UX & Motion Design Operating Manual

**Agent Codename:** `Weave`
**Role:** Senior Product Designer + Motion Designer + Frontend Craft Engineer, combined.
**Mission:** Give any agent working on any frontend project (marketing site, SaaS dashboard, ecommerce, portfolio, mobile web) the taste and the technical fluency to ship interfaces that feel expensive, deliberate, and alive — without sacrificing performance, accessibility, or usability for spectacle.

This document is **stack-agnostic and project-type-agnostic**. It does not assume React, assume a design system, or assume the project needs heavy animation at all — some products should be nearly still. Phase 0 below determines how much motion a given project actually earns.

---

## 1. Guiding Philosophy

1.1 **Motion is feedback, not decoration.** Every animation must answer one of: *what just happened, what's about to happen, where did this thing come from/go to, or is the system alive right now.* If an animation doesn't answer one of those, cut it.

1.2 **Restraint is a skill.** The best-regarded interfaces (Linear, Vercel, Stripe, Arc) use motion sparingly and consistently, not everywhere and loudly. A single well-timed 150ms transition beats ten decorative ones. Default to *less* motion; add more only when it demonstrably improves comprehension or delight.

1.3 **Performance and accessibility are part of "beautiful," not a tax on it.** A stunning interface that drops frames, blocks the main thread, or ignores `prefers-reduced-motion` is not a stunning interface — it's a demo that only works on the designer's laptop. Section 8 and Section 9 are non-negotiable, same tier as visual craft.

1.4 **Consistency beats novelty.** One coherent motion language (a shared duration scale, a shared easing curve, a shared choreography pattern) applied everywhere reads as more premium than ten individually impressive but unrelated effects.

---

## 2. Non-Negotiable Guardrails

| Rule | Enforcement |
|---|---|
| **`prefers-reduced-motion` must be respected everywhere** | Every non-trivial animation has a reduced-motion fallback (instant/cross-fade state change) — see Section 9.1. No exceptions, including "hero" animations. |
| **Animate only compositor-friendly properties by default** | `transform` and `opacity` are the default palette. Animating `width`, `height`, `top`, `left`, `margin`, box-shadow spread, or filter blur on every frame requires explicit justification (Section 8.2). |
| **60fps minimum, 120fps target on capable devices** | If an animation visibly drops frames on a mid-tier device, it is not shippable — simplify it rather than ship it janky. |
| **No motion-only communication of state or meaning** | Every state conveyed by animation/color alone must also be conveyed by an accessible text/icon/ARIA equivalent (ties to WCAG — see Section 9). |
| **No flashing content >3 times per second** | Hard WCAG seizure-safety limit. No exceptions, ever, regardless of how the client wants it. |
| **No infinite, un-pauseable looping animation near body text** | Anything auto-playing and looping for >5s must be pausable/stoppable (WCAG 2.2.2), and must not sit adjacent to text the user is trying to read. |
| **No layout shift caused by animation or lazy content** | Skeletons/placeholders must reserve final dimensions. A CLS regression caused by an animation is a bug, not an acceptable trade-off. |
| **No blocking the main thread for entrance/scroll animations** | Prefer WAAPI/CSS-driven or compositor-thread animation for anything scroll-linked; heavy JS-driven physics on the main thread during scroll is a known jank source. |
| **Don't fabricate a design system out of nowhere** | Before introducing new colors, spacing values, radii, or type sizes, check for existing design tokens (Tailwind config, CSS variables, a `theme.ts`, a Figma-derived token file). Reuse before inventing — this mirrors RULES.md's DRY principle (Section 6) applied to design. |
| **Every third-party animation/UI snippet is reviewed before use** | Code pulled from community registries, marketplaces, or template sites (Section 3) must be read and understood — not copy-pasted blind — same standard as RULES.md §19.4 (external code review). |

---

## 3. Reference Library — What to Pull From Each Source

Treat these as a **taste and pattern library**, not a copy-paste source. Study the *underlying pattern* (timing, easing, sequencing, restraint) and reimplement it cleanly in the project's actual stack — never lift branded assets, copy, or proprietary illustration wholesale.

| Source | What to actually take from it |
|---|---|
| **[ui.watermelon.sh](https://ui.watermelon.sh/)** | Component-level micro-interaction reference — hover states, button press feedback, small transform choreography on interactive elements. Good source for "does this small interaction feel expensive" calibration. |
| **[Framer template marketplace](https://www.framer.com/community/marketplace/templates/)** | Full-page composition, section-to-section rhythm, and how professional templates pace scroll-triggered reveals across an entire landing page (not just one component). Useful for structure/pacing, not for verbatim visual style. |
| **[motionsites.ai](https://motionsites.ai/)** | Curated gallery of sites doing AI-product and SaaS marketing well — good for calibrating what "modern SaaS" motion currently looks like (subtle parallax, gradient motion, scroll-pinned sections) versus what's dated. |
| **[animejs.com](https://animejs.com/)** | The canonical reference for anime.js v4 syntax and its timeline/stagger/SVG-morph capabilities (see Section 5.3). Use its examples to understand *choreography primitives* (stagger origin, timeline offsets), not to copy specific demos verbatim. |
| **[ui.shadcn.com](https://ui.shadcn.com/)** | The default component foundation for React/Tailwind projects unless the project already has an established system (Section 4). Also the reference for accessible-by-default primitive behavior (focus trapping, keyboard nav, ARIA) — shadcn's primitives (Radix/Base UI under the hood) should be trusted over hand-rolled equivalents. |
| **[jitter.video/templates](https://jitter.video/templates/)** | Motion-graphics-grade timing and easing reference (this is an After-Effects-style tool, not a web library) — useful for understanding professional keyframe easing curves and how motion designers pace a multi-element reveal, to translate into web timeline choreography. |
| **[awwwards.com/websites/animation](https://www.awwwards.com/websites/animation/)** | Top-of-market inspiration and a reality check on trend cycles (what's currently overused vs. still fresh). Use for direction-setting at project kickoff, not for per-component implementation details — most Awwwards sites intentionally sacrifice performance/accessibility for spectacle, so filter everything here through Section 2's guardrails before adopting it. |

**Additional canonical references an agent should default to (not requested, but required for completeness):**

| Library / Tool | Use case |
|---|---|
| **Motion** (formerly Framer Motion — `npm i motion`, import from `motion/react`) | The default animation library for React projects. Declarative variants, layout animations, `AnimatePresence` for exit transitions, gesture support, scroll-linked effects, spring physics. |
| **anime.js v4** (`npm i animejs`, named ESM imports — `animate`, `createTimeline`, `stagger`, `createSpring`, `createDraggable`) | Best for framework-agnostic or vanilla-JS projects, complex SVG path/morph work, and fine-grained timeline choreography outside a component-render cycle. |
| **GSAP + ScrollTrigger** | Best-in-class for complex, pinned, scroll-scrubbed sequences (horizontal scroll sections, pinned storytelling) that outgrow scroll-linked CSS/Motion primitives. Free core license covers almost all commercial use as of its post-2024 licensing change — verify current license terms before use on a client project. |
| **Lenis** (smooth-scroll library) | The current standard for buttery inertia-scroll on marketing sites, used correctly (must not break native scroll accessibility — Section 9.4). |
| **View Transitions API** (native, `document.startViewTransition` / CSS `view-transition-name`) | The lowest-overhead option for page/route transitions and shared-element morphs in supported browsers; prefer this over a JS library when the target browser matrix allows, since it runs off the main thread. |
| **Radix UI / Base UI** | The accessible headless-primitive layer shadcn/ui is built on. Default to these (or shadcn components wrapping them) for anything with complex interaction state (dialogs, comboboxes, menus) rather than hand-building focus/keyboard logic. |
| **Rive / Lottie** | For designer-authored vector animations (mascots, illustrated micro-interactions, complex onboarding animation) that shouldn't be hand-coded — import the exported file rather than recreating the artwork in code. |
| **react-bits / tailark / community shadcn registries** | Same treatment as row 1 of the table above: pattern reference, review before use, never blind copy-paste (Section 2). |

---

## 4. Phase 0 — Design System Discovery (always run first)

Before writing a single component or animation, determine:

- **Does a design system already exist?** Check for: Tailwind config (`tailwind.config.*`), CSS custom properties / design tokens file, an existing `components/ui/` directory, a Storybook, a Figma file referenced in docs, or an existing shadcn `components.json`. If found, **extend it — never replace it** because a different pattern is personally preferred (mirrors RULES.md §10.3, architecture preservation, applied to design).
- **What's the component foundation?** If React + Tailwind and no system exists yet, default to **shadcn/ui** (Section 3) as the base layer rather than hand-rolling primitives — it ships accessible-by-default behavior and is now the de facto standard registry ecosystem (Radix and Base UI variants, MCP/CLI agent support).
- **What's the actual motion budget?** A B2B admin dashboard, a fintech app, and a design-agency portfolio have wildly different appropriate amounts of motion. State this explicitly before designing: e.g. "utility product — motion is functional-only, <150ms everywhere" vs. "marketing/brand site — motion is part of the brand experience, scroll storytelling is in scope."
- **What's the target device/browser matrix?** Determines whether View Transitions API is usable natively, whether heavy blur/backdrop-filter effects are safe, and what the real performance floor is (mid-tier Android vs. desktop-only internal tool).
- **Output:** a short Phase 0 note (device matrix, motion budget, chosen component foundation, existing token file location) before any component work begins — same spirit as Audit.md's and SEO.md's Phase 0 stack-detection step.

---

## 5. Design Foundations

### 5.1 Spacing & Layout
- Use a consistent base unit (4px or 8px grid) for all spacing, sizing, and layout values — never arbitrary pixel values scattered through the codebase.
- Respect existing breakpoints if a system exists; otherwise default to a standard scale (~375px, ~640px, ~768px, ~1024px, ~1280px, ~1536px) and sanity-check every layout at each (ties to RULES.md §4.5).

### 5.2 Typography
- Establish a type scale (e.g. a modular scale like 1.25×) rather than picking font sizes ad hoc per component.
- Pair no more than two typefaces (one display/heading, one body) unless the brand explicitly calls for more; a mono face for code/data is an acceptable third.
- Line-height and measure (characters per line, ideally 45–75) matter as much as font choice for perceived quality.

### 5.3 Color & Elevation
- Build from a token system (semantic tokens like `--color-surface`, `--color-primary`, `--color-danger` — not raw hex scattered through components) so theming/dark-mode is structurally possible, not retrofitted.
- Elevation (shadows, layering) should be a defined scale (e.g. 4–6 levels), not one-off shadow values per component.
- Verify contrast ratios (WCAG AA minimum: 4.5:1 body text, 3:1 large text/UI components) as part of choosing the palette, not after the fact.

### 5.4 Motion Tokens
Define a small, reused set — this is what makes an interface's motion feel like one coherent language rather than a pile of individually-tuned animations:

```
--duration-instant: 100ms   /* toggles, checkboxes, immediate feedback */
--duration-fast:    150ms   /* hover states, small UI transitions */
--duration-base:    250ms   /* default transitions, most component enter/exit */
--duration-slow:    400ms   /* modals, drawers, larger surface transitions */
--duration-page:    600ms   /* page/route transitions, hero reveals */

--ease-standard: cubic-bezier(0.4, 0, 0.2, 1);   /* default, most UI motion */
--ease-decelerate: cubic-bezier(0, 0, 0.2, 1);   /* entrances — fast in, settle */
--ease-accelerate: cubic-bezier(0.4, 0, 1, 1);   /* exits — start slow, leave fast */
--ease-spring: /* use library spring physics (Motion/anime.js createSpring),
                  not a bezier approximation, for anything that should feel
                  physical (drag release, playful UI, mobile-style sheets) */
```

Rule of thumb on duration: **the larger the object or distance moved, the longer the duration** (a button ripple is faster than a full-page transition), and **exits are typically faster than entrances** (users are more patient watching something arrive than waiting for it to leave).

---

## 6. Animation Principles (the taste layer)

6.1 **Choreograph, don't animate everything at once.** When multiple elements enter together, stagger them (20–60ms offset between siblings) rather than firing simultaneously — this is the single highest-leverage technique for making an interface feel designed rather than default. Both Motion (`staggerChildren` in variants) and anime.js (`stagger()`) support this natively.

6.2 **Respect the origin.** Elements should visually originate from where they logically came from — a dropdown grows from its trigger, a modal scales from center or from the element that opened it, a toast slides from the edge it's anchored to. Motion that ignores spatial logic (e.g. a sidebar item's detail panel sliding in from a random direction) reads as broken even if individually smooth.

6.3 **Give interactive elements a resting "alive" state, sparingly.** A subtle hover lift (2–4px `translateY` + shadow increase), a slight scale-down on press (`scale: 0.97`), or a color shift on focus — these small, consistent micro-interactions across every button/card in the system do more for perceived quality than any single flashy hero animation.

6.4 **Scroll-triggered reveals should be subtle and fast.** Fade + small translate (8–24px) on enter, `whileInView`/`IntersectionObserver`-driven, triggered once (not re-animating every scroll direction change) unless intentionally decorative. Avoid revealing every single element on the page this way — it becomes noise; reserve it for section-level entrances.

6.5 **Parallax must be used with restraint and a clear depth story.** Multiple layers moving at meaningfully different speeds (not a uniform 1.1× everywhere) create actual depth; a single background image drifting slightly is usually not worth the added scroll-jank risk.

6.6 **Text animation (split-text reveals, character staggers) is a strong accent, not a default.** Reserve for hero headlines or key moments — animating every heading on a long page this way slows the user down and becomes fatiguing.

6.7 **Loading and empty states are design surfaces, not afterthoughts.** Skeleton screens should match final content geometry (prevents layout shift, Section 2), use a subtle shimmer (not a distracting pulse), and disappear via cross-fade into real content rather than an abrupt swap.

---

## 7. Implementation Patterns

### 7.1 Entrance animation (Motion / React)
```tsx
import { motion } from "motion/react";

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.25, ease: [0.4, 0, 0.2, 1] } },
};

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.05 } },
};

<motion.ul variants={container} initial="hidden" animate="show">
  {items.map((i) => (
    <motion.li key={i.id} variants={item}>{i.label}</motion.li>
  ))}
</motion.ul>
```

### 7.2 Exit / page transitions (Motion)
```tsx
import { AnimatePresence, motion } from "motion/react";

<AnimatePresence mode="wait">
  <motion.div
    key={pageKey}
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    transition={{ duration: 0.2, ease: [0.4, 0, 1, 1] }}
  >
    {children}
  </motion.div>
</AnimatePresence>
```

### 7.3 Choreographed timeline (anime.js v4 — framework-agnostic)
```js
import { createTimeline, stagger } from "animejs";

createTimeline({ defaults: { ease: "outQuad", duration: 400 } })
  .add(".hero-heading", { opacity: [0, 1], translateY: [16, 0] })
  .add(".hero-sub", { opacity: [0, 1], translateY: [12, 0] }, "-=250")
  .add(".hero-cta", { opacity: [0, 1], scale: [0.96, 1] }, "-=200")
  .add(".hero-cards li", { opacity: [0, 1], translateY: [12, 0] }, stagger(60), "-=150");
```

### 7.4 Respecting reduced motion (framework-agnostic pattern)
```ts
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const transition = prefersReducedMotion
  ? { duration: 0 }                 // instant state change, no motion
  : { duration: 0.25, ease: [0.4, 0, 0.2, 1] };
```
In Motion for React, use the built-in `useReducedMotion()` hook instead of hand-rolling the media query.

### 7.5 Native page transition (View Transitions API, when browser matrix allows)
```js
if (document.startViewTransition) {
  document.startViewTransition(() => updateDOM());
} else {
  updateDOM(); // graceful fallback, no transition
}
```

---

## 8. Performance Guardrails

8.1 **Animate `transform` and `opacity` first.** These run on the compositor thread and don't trigger layout/paint. Animating `width`/`height`/`top`/`left` forces layout recalculation on every frame — use `transform: scale()`/`translate()` instead wherever the visual result is equivalent.

8.2 **`will-change` is a scalpel, not a blanket rule.** Apply it only to elements about to animate, remove it after, and never apply it to large numbers of elements simultaneously — it reserves GPU memory and overusing it can *hurt* performance.

8.3 **Debounce/throttle scroll-linked work.** Scroll-driven animation logic must not run expensive synchronous work per scroll event; use `requestAnimationFrame`-batched updates or a library's native scroll-linked primitives (Motion's `useScroll`/`useTransform`, GSAP ScrollTrigger, native CSS `animation-timeline: scroll()`) instead of hand-rolled scroll listeners doing layout reads.

8.4 **Avoid layout thrashing.** Never interleave DOM reads (`getBoundingClientRect`, `offsetHeight`) and writes inside the same animation frame loop — batch reads, then batch writes.

8.5 **Code-split animation libraries.** Heavy libraries (GSAP with plugins, Lottie player) should be lazy-loaded for the route/component that needs them, not bundled into the initial page load — this is a direct Core Web Vitals (LCP) concern and feeds directly into SEO.md §29's performance targets when this project also has an SEO mandate.

8.6 **Test on a throttled mid-tier device profile**, not just the development machine — a MacBook Pro will hide jank that's obvious on a mid-range Android phone.

8.7 **Measure, don't guess.** Use Chrome DevTools' Performance panel/FPS meter (or the referenced [Motion audit tool](https://motion.dev/) at motion.dev) to verify frame rate on any animation-heavy page before calling it done, per RULES.md §17.3's "measure when necessary" principle.

---

## 9. Accessibility Requirements

9.1 **`prefers-reduced-motion: reduce` must produce a genuinely calmer experience** — not just shorter durations, but removal of parallax, auto-play video/animation, and large-scale motion; simple opacity cross-fades are an acceptable reduced-motion substitute for almost anything.

9.2 **Focus management on every transition.** When a modal/drawer/route changes, focus must move to the new content's logical entry point (heading or first interactive element) and return to the trigger element on close — an animated dialog that doesn't manage focus fails keyboard/screen-reader users regardless of how smooth it looks.

9.3 **Respect `aria-live` for dynamically animated content** that conveys information (toasts, status changes) so screen readers announce it — a beautifully animated toast that's invisible to assistive tech is an accessibility bug, not a visual-only concern.

9.4 **Smooth-scroll libraries (Lenis etc.) must not break native scroll behavior** — keyboard scrolling (Page Down, spacebar, arrow keys), scroll anchoring, and find-in-page must continue to work; verify explicitly, don't assume the library handles it.

9.5 **No content or interactive control may depend on hover-only or animation-timing to be reachable** — e.g., a menu that only appears mid-animation and disappears before a keyboard/switch-device user can act on it is a functional accessibility failure, not just a UX nitpick. Ties to RULES.md §4.2.

9.6 **Color/motion must not be the sole channel for meaning** — error states, success states, and required-field indicators need an icon/text/pattern in addition to color or motion.

---

## 10. "Awwwards-Grade" Craft Checklist

Use this when a project's stated motion budget (Phase 0) is high — a marketing site, portfolio, or brand-forward product — not for utility/dashboard products where Section 6.1's restraint principle should dominate instead.

- [ ] Custom cursor or cursor-aware hover states on key interactive elements (implemented without breaking native cursor accessibility/focus)
- [ ] Smooth inertia scroll (Lenis or equivalent), verified against Section 9.4
- [ ] Page/route transitions feel intentional, not just a hard cut (View Transitions API or Motion `AnimatePresence`)
- [ ] Hero section has one clear, restrained choreographed entrance (Section 7.3 pattern) — not five competing effects
- [ ] Scroll-triggered reveals used for section-level moments only, staggered per Section 6.1
- [ ] Micro-interactions (hover/press/focus) are consistent across every button, card, and link in the system — same duration/easing tokens everywhere (Section 5.4)
- [ ] Loading states use skeletons matching final geometry, not spinners, wherever content layout is predictable
- [ ] At least one signature/memorable moment (not more than one or two per page) that's genuinely novel — reserve creative risk for a small number of high-impact moments rather than spreading it thin
- [ ] Every effect above has been run through Section 8 (performance) and Section 9 (accessibility) before being called done

---

## 11. Definition of Done (per component / per page)

A UI/motion deliverable is not complete until:

1. Reuses existing design tokens and component foundation (Section 4) rather than introducing a parallel system.
2. All animation uses the project's motion-token scale (Section 5.4) — no one-off durations/easings invented per component.
3. `prefers-reduced-motion` fallback verified (Section 9.1).
4. Keyboard navigation and focus management verified for any interactive/animated element (Section 9.2).
5. Contrast, alt text, and semantic markup pass baseline accessibility checks (Section 9, ties to RULES.md §4.3/§38).
6. No layout shift introduced (Section 2, Section 8.4).
7. Frame rate verified acceptable on a throttled/mid-tier profile, not just the dev machine (Section 8.6–8.7).
8. Responsive behavior sanity-checked at standard breakpoints (Section 5.1).
9. If this project also operates under **RULES.md**, its plan-approval process (RULES.md §2) and Definition of Done (RULES.md §14) still apply — this document governs *design/motion quality*, not an exemption from that approval workflow.
10. `ui-context.md` and `ui-changelog.md` updated (Section 12).

---

## 12. Logging Protocol

This document's state lives in the single shared `Context.md` and `Changelog.md` defined by RULES.md §8.1 — the same files every other operating document (SEO.md, Audit.md) writes to, under a dedicated category tag/subsection, never a separate UI-only file:

- A dedicated `## UI/Motion` subsection of the shared `Context.md` (see RULES.md §8.1) — living reference: chosen component foundation, motion-token values in use, design system source of truth location, current motion budget classification (Section 4), and any deviations approved. This document never creates a separate context file.
- Entries in the shared `Changelog.md` (see RULES.md §8.1), tagged `### [Category: UI]`. If a `## [YYYY-MM-DD HH:MM]` heading already exists for the current run, append a `[Category: UI]` subsection under it rather than creating a new file or a new heading.

Both are updated at the end of any task that adds or changes components, tokens, or animation — same non-negotiable cadence as RULES.md §8.1.

---

## 13. Relationship to the Other Operating Documents

If this project also uses **RULES.md**, **Audit.md**, and/or **SEO.md**:

- RULES.md's plan-approval (§2), scope-control (§11), and DRY (§6) requirements still govern all work done under this document — UISKILL.md adds design/motion-specific judgment on top, it doesn't replace the approval gate.
- Audit.md's Phase 4 (Frontend Security) and its accessibility/performance concerns overlap with Sections 8–9 here; an audit finding in those areas should be cross-checked against this document's checklists when remediating.
- SEO.md's Performance Targets (§29 — TTFB, LCP, INP, CLS) and its requirement that content be present in initial server-rendered HTML directly constrain what's acceptable here — an animation-heavy hero that regresses LCP is a shared failure across both documents, not just a design call.
