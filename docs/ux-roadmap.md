# Product Roadmap: NIFFF Planner V2

## 🎯 Vision
To create a personal, film-centric planning tool that guides users from broad exploration to a clear, committed schedule, eliminating the need for users to think like festival experts.

## ✨ Core Design Principles
*   **Film-First:** The film details, along with the viewing intention, must always take precedence over the current scheduling session view.
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
    *   Streamline film cards/list items.
    *   Introduce action-oriented grouping/filtering mechanisms.
    *   Add visible progression indicators.
    *   Transition to a simple, secondary scheduling function.
*   **Out of Scope:** Complex multi-action scheduling, advanced scoring, deep filter personalization.
*   **Success Criteria:** Quick triage of a large selection; priority of films visible at a glance; Film Catalog feels like a decision stage.

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