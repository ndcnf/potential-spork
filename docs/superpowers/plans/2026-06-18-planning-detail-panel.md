# Planning Detail Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the Planning detail panel readability by making the selected screening, alternatives, user decisions, and recommendations visually distinct.

**Architecture:** Keep the existing Vue view and planning composable. Make a scoped template/CSS refactor in `PlanningView.vue` and `planning.css`, with minimal helper additions only if needed.

**Tech Stack:** Vue 3 Composition API, Pinia store data, CSS custom properties, Vitest, Vite.

**Status:** Implementation and documentation are reflected in the current branch. Verification commands and visual QA remain explicit checklist items so they can be rerun and evidenced in a fresh session.

---

### Task 1: Detail Panel Structure

**Files:**

- Modify: `frontend/src/views/PlanningView.vue`
- Modify: `frontend/src/styles/planning.css`

- [x] Move the panel content into four readable sections: compact film header, active screening, comparison rows, external links.
- [x] Keep current actions and event handlers: `applyScreeningSelection`, `removeScreeningSelection`, `exportScreeningIcal`.
- [x] Do not change backend data or selection behavior.

### Task 2: Status And Recommendation Language

**Files:**

- Modify: `frontend/src/views/PlanningView.vue`
- Modify: `frontend/src/styles/planning.css`
- Modify if necessary: `frontend/src/styles/tokens.css`

- [x] Use distinct classes for user status markers and recommendation chips.
- [x] Make `confirmed` stronger than `tentative`.
- [x] Keep recommendation chips secondary and visually different from status pills.
- [x] Keep conflict readable through text and border, not color alone.

### Task 3: Documentation And Verification

**Files:**

- Modify: `docs/current-ui-state.md`
- Modify: `docs/source-of-truth.md`

- [x] Document that Planning separates user decision status from recommendation signals.
- [x] Document venues/lieux as a follow-up priority.
- [ ] Run `npm run test`.
- [ ] Run `npm run build`.
- [ ] Start the frontend locally and visually inspect Planning at desktop and mobile widths.
