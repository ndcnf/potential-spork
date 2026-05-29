# Product Roadmap: NIFFF Planner V2

## 🎯 Vision
To create a personal, film-centric planning tool that guides users from broad exploration to a clear, committed schedule, eliminating the need for users to think like festival experts.

## ✨ Core Design Principles
*   **Film-First:** The film details, along with the viewing intention, must always take precedence over the current scheduling session view.
*   **Editorial Selection Matters:** Tagline, director, cast, country, duration, and year are not secondary metadata. They are primary selection criteria and must stay visible enough to support desire-based choice.
*   **Guided Workflow:** Every screen must guide the user toward the single, most useful next action.
*   **Visible Simplicity:** Limit states, colors, and complex mental branches in the UI.
*   **Consistency over Richness:** Maintain unified signals, priorities, and interactions across all modules.
*   **Comparison Lite:** Enable comparison for decision-making, not for exhaustive planning.
*   **Explicit Progression:** The app must clearly show what has been decided, what is blocked, and what the next decisive step is.

## 📊 Current State Assessment
*   **Existing Views:** Film Catalog, Schedule, Free Slots, Settings.
*   **Visual Foundation:** A refined visual theme utilizing a consistent dark mode; a simplified design system based on `background / foreground / accent` states managed via opacity.
*   **Product Focus:** The core logic is confirmed to be `film-first`.
*   **Prioritization:** Simplified UI priority model: **Priority**, **Medium**, **Ignore**.
*   **Key Pain Point:** The product currently feels like an aggregation of expert tools rather than a decision-making guide and planning journey.

## 🛣️ Roadmap Milestones
### **P0: Clarify Central Workflow (Focus: Decision Flow)**
*   **Objective:** Establish a simple, canonical user journey: **Select Films ➡️ Arbitrate Choices ➡️ Fill Schedule.**
*   **Tasks:**
    *   Define the 3 visible canon steps.
    *   Reposition existing views to fit the new flow.
    *   Write a specific UX promise for each core view.
    *   Identify one primary, unique action per screen.
    *   Formalize empty states and transition messages.
*   **Out of Scope:** Full screen redesign, new data models, fine visual optimizations.
*   **Success Criteria:** Workflow explainable in under one minute; every view has a clear role; empty states are helpful.

### **P1: Elevate Films View (Focus: Qualification)**
*   **Objective:** Make the Film Catalog the primary gateway for initial qualification and decision-making.
*   **Tasks:**
    *   Emphasize the 3 priority levels.
    *   Streamline film cards/list items without flattening editorial value.
    *   Preserve the core film-selection cues: title, year, tagline, director, cast, country, duration.
    *   Treat tagline as a primary selling element, not decorative copy.
    *   Introduce action-oriented grouping/filtering mechanisms.
    *   Add visible progression indicators.
    *   Transition to a simple, secondary scheduling function.
*   **Out of Scope:** Complex multi-action scheduling, advanced scoring, deep filter personalization.
*   **Success Criteria:** Quick triage of a large selection; priority of films visible at a glance; Film Catalog feels like a decision stage.

#### P1 clarification

The `Films` view is not just a utility list. It is an editorial selection workspace.

For this product, the following elements are part of the core decision payload:
- title
- year
- tagline
- director
- cast
- country
- duration

Priority does not replace these signals.

Priority answers: **how much do I want to see it?**  
Film metadata answers: **why do I want to see it?**

Both are required.

### **P2: Structure Planning (Focus: Guided Arbitrage)**
*   **Objective:** Transform the Schedule view from a mere result table into an actionable space for choice.
*   **Tasks:**
    *   Highlight conflicts visibly and make them solvable.
    *   Introduce clear, structured sections.
    *   Provide simple recommendations or comparison frameworks.
    *   Limit Calls-to-Action (CTAs) per schedule slot.
    *   Show the impact/consequence of a decision.
*   **Out of Scope:** Black-box schedulers, expert settings in the main flow, complex drag-and-drop.
*   **Success Criteria:** Conflicts are visible and resolvable first; consequences of decisions are clear; reduced hesitation without a framework.

### **P3: Free Slots/Gaps (Focus: Completion Engine)**
*   **Objective:** Convert "Free Slots" view into an opportunistic, intelligent scheduling assistant.
*   **Tasks:**
    *   Center the view on actionable gaps.
    *   Suggest a short list of highly relevant films.
    *   Differentiate suggestions: **High Priority Match** / *Medium Option* / No Match.
    *   Avoid requiring a temporary switch back to the Film Catalog.
    *   Provide clear guidance when no viable actions exist.
*   **Out of Scope:** Full catalogue exploration, visible fine-tuning of matching logic, peripheral actions outside of filling slots.
*   **Success Criteria:** Actionable gaps understood immediately; completion flow avoids permanent reversion to source views; suggestions are genuinely useful.

## 🛠️ Core Constraints & Guiding Rules
*   **The Problem:** The main fix is structural: evolving expert tools into a guided workflow.
*   **Theme:** Maintain the coherent dark mode.
*   **Color Scheme:** Minimalist assumptions: `background`, `foreground`, `accent` with opacity variations for states.
*   **Priority:** Film selection is always paramount, overriding immediate scheduling needs.
*   **UX Guardrail:** Prevent CTA overload, especially in comparison or scheduling screens.
*   **Scope:** All new features must justify their place within the core journey: **Select ➡️ Arbitrate ➡️ Complete.**
*   **Settings:** Must remain a secondary, out-of-band configuration area.

## ✅ Next Iteration Checklist
1.  Validate the 3-step canonical workflow and associated terminology.
2.  Map every existing view to a single, unique UX intention.
3.  List all missing empty states and required guidance messages.
4.  Define the priority sections for both the Film Catalog and the Schedule view.
5.  Identify 3-5 concrete UX conflicts to simplify immediately.

---

## P2 Detailed Note — Planning as an Arbitration Workspace

### Purpose

Step 2 exists to turn a list of desired films into concrete scheduling decisions.

This is not a discovery screen. It is an arbitration workspace:
- compare conflicting screenings quickly
- decide what to keep, replace, or ignore
- build a realistic festival schedule without losing film context

The core job of this screen is to help the user decide, not to browse the full NIFFF catalogue.

### User Questions This Screen Must Answer

The user should be able to answer these questions very quickly:
- Which screenings are currently in conflict?
- Which films are actually important for me?
- If I choose this screening, what do I lose?
- What is the best remaining option for this film?
- Is this day still feasible and readable?
- What is already decided, and what still needs arbitration?

If the screen cannot answer these questions in a few seconds, it is too dense.

### What Must Be Visible in the Main View

The main planning view should only show what is needed for arbitration:
- clear time structure
- screenings positioned in time
- collisions and overlaps
- film priority: `Prioritaire`, `Moyen`, `Ignorer`
- decision state: selected, alternative, conflict, ignored
- minimum useful metadata per screening:
  - film title
  - time
  - venue if relevant for arbitration
  - one status signal

The main view should **not** show:
- long synopsis
- complete credits
- secondary cinephile metadata
- multiple competing tags, badges, and icons

### What Must Be Visible in the Detail Panel

The detail panel carries complexity. That is its role.

It should contain:
- full title
- full schedule information
- short summary only
- editable film priority
- alternative screenings of the same film
- direct conflicts with already selected screenings
- one main action depending on context:
  - `Choisir cette seance`
  - `Remplacer la seance actuelle`
  - `Ignorer`
- a clear explanation of the conflict in plain language

Optional only if useful:
- buffer time between screenings
- a simple recommendation if it is easy to justify

### Recommended Information Hierarchy

Visual order of importance:
1. Time
2. Current decision
3. Conflict level
4. Film priority
5. Secondary context

Concrete implications:
- timeline and collisions dominate visually
- film title remains the main text inside a screening item
- priority stays visible but sober
- secondary metadata recedes

In the dark theme:
- use contrast for structure
- reserve accent for strong intent and final choice
- use opacity for nuance, not more colors

### Recommended States and Actions

#### Minimum states
- `Non traite`
- `Selectionne`
- `En conflit`
- `Alternative disponible`
- `Ignore`

#### Primary actions
- choose a screening
- replace a selected screening with another
- change film priority
- ignore a film
- undo a recent decision

#### Secondary actions
- open detail
- reveal alternatives for the same film
- filter by day, priority, or conflicts only

Each screening item should expose only one primary action according to context:
- free => `Choisir`
- conflicting => `Remplacer`
- already retained => `Conserver`
- ignored => `Restaurer` if relevant

### Rules to Reduce Cognitive Load

- Show decisions to take first, not the whole catalogue.
- Use only the minimal visual language: background / foreground / accent.
- Keep `Prioritaire / Moyen / Ignorer` as the only preference model.
- Group conflicts visually instead of scattering them.
- Keep one detail level per zone:
  - main view = rapid arbitration
  - detail panel = context and consequences
- Reduce copy to the strict minimum.
- Avoid concurrent micro-signals: too many icons, outlines, tags, and hints.
- Reveal alternatives only when they are actually useful.
- Always show the consequence of an action: what gets replaced, what remains unresolved.

### Anti-Patterns to Avoid

- Turning Planning into a film detail page.
- Multiplying color semantics by genre, venue, status, and personal state.
- Giving the same visual weight to `Prioritaire` and `Moyen`.
- Hiding conflicts behind deep interactions.
- Asking the user to infer a conflict without showing what is lost.
- Using modals for every major arbitration.
- Adding opaque recommendation logic with no explanation.
- Reintroducing many CTAs per screening in comparison contexts.

### First Implementation Plan for P2 Only

#### V1 Scope
- one daily timeline view
- screenings cards positioned in time
- visible time conflicts
- editable film priority: `Prioritaire`, `Moyen`, `Ignorer`
- side detail panel
- actions: `Choisir`, `Remplacer`, `Ignorer`

#### Components to design or stabilize
- `PlanningScreen`
- `DayTimeline`
- `ScreeningCard`
- `ConflictGroup`
- `FilmDetailPanel`
- `PrioritySelector`

#### Product rules
- one selected screening blocks conflicting screenings
- ignored films leave the main planning flow by default
- priority drives visibility and arbitration order
- the detail panel must always show direct conflicts and same-film alternatives

#### Delivery sequence
1. Lock the dark timeline structure.
2. Keep screening cards minimal: title, time, priority, state.
3. Make conflict detection and display obvious.
4. Add the detail panel with clear decision actions.
5. Add priority changes from the same workflow.
6. Add only minimal filters: day, priority, conflicts.
7. Test on dense festival days before enriching anything.

#### Success criteria
- A user understands the day schedule at a glance.
- A user identifies conflicts in under 5 seconds.
- A user can arbitrate between two screenings in under 15 seconds.
- The product feels like schedule building, not database browsing.
