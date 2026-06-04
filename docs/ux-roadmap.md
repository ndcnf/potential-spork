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
*   **Existing Views (current frontend):** Film Catalog, Schedule, Settings.
*   **Deferred View:** Free Slots / Gaps is now out of the active frontend scope and should be treated as a V2/V3 track.
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
*   **Status:** Deferred to V2/V3. Not part of the current frontend scope.
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
1.  Done: validate the canonical workflow and associated terminology, with the 3rd step explicitly deferred out of the current frontend scope.
2.  Done: map every existing view to a single, unique UX intention.
3.  In progress: list and implement the missing empty states and guidance messages across the core views.
4.  Done for the current pass: define the priority structure for `Films` and the arbitration structure for `Planning`.
5.  In progress: simplify concrete UX conflicts, starting with multi-CTA overload in `Planning`.
6.  Later: only revisit `Trous / Free Slots` in a V2/V3 product pass.

---

## P0 Detailed Note — Canonical Workflow and Screen Intentions

### Canonical workflow

The long-term product flow should be visible and explicit:

1. **Select films**
2. **Arbitrate conflicts**
3. **Fill remaining gaps**

This wording is the right level of clarity.

- `Select films` is editorial and desire-driven.
- `Arbitrate conflicts` is about decision-making under time constraints.
- `Fill remaining gaps` is about opportunistic completion, not rediscovery.

Avoid weaker labels such as:
- `Browse`
- `Optimize`
- `Explore`
- `Schedule`

Those labels are either too vague, too technical, or too tool-like.

### Global UX promise

The app promise should be simple:

**Help me turn a broad film wish list into a realistic NIFFF schedule, without making me think like a festival expert.**

Every main screen must support one distinct moment in that journey.

For the current frontend release, only the first 2 steps are active.
The completion step is deferred.

### Screen mapping

#### 1. `Films`
**Step:** Select films  
**UX promise:** Help me quickly decide which films deserve my attention.  
**Primary action:** Set or adjust film priority.

This screen is an editorial selection workspace.
It must answer:
- What looks desirable?
- Why is this film interesting?
- Should I treat it as `Immanquable`, `Peut-etre`, or `Non merci`?

It should not behave like:
- a dense database table
- a schedule builder
- a metadata dump

#### 2. `Planning`
**Step:** Arbitrate conflicts  
**UX promise:** Help me choose the right screening when time constraints collide.  
**Primary action:** Choose or replace a screening.

This screen is an arbitration workspace.
It must answer:
- What is already decided?
- What conflicts now?
- If I choose this screening, what do I lose?

It should not behave like:
- a film discovery screen
- a general catalogue view
- a multi-CTA control panel

#### 3. `Trous / Free Slots`
**Status:** Deferred to V2/V3  
**Step:** Fill remaining gaps  
**UX promise:** Help me complete empty moments with the most relevant remaining options.  
**Primary action:** Add the best fitting film to a gap.

This screen is a completion assistant.
It must answer:
- Where do I still have room?
- Is there a strong match?
- Is there only a medium fallback?

It should not behave like:
- a second Films screen
- a hidden expert optimizer
- a generic recommendation feed

#### 4. `Settings`
**Step:** Outside the core flow  
**UX promise:** Let me adjust preferences without interrupting the main journey.  
**Primary action:** Save configuration.

This screen is secondary and out-of-band.
It must not absorb product choices that belong to the main workflow.

### Primary navigation model

The main navigation should reflect the workflow directly:

- `1. Films`
- `2. Planning`
- `Settings` stays visually secondary

Recommended behavior:
- show step numbers for the active workflow views
- keep the active step highly legible
- show progression, not just location

Good signal examples:
- `Step 1 of 2`
- `12 prioritaires definis`
- `4 conflits a arbitrer`
- `3 creneaux encore libres`

The user should always understand what has been done and what remains unresolved.

### One primary action per core screen

This rule is non-negotiable.

- `Films` => **Prioritize this film**
- `Planning` => **Choose/replace this screening**
- `Settings` => **Save settings**

Secondary actions may exist, but they must remain subordinate.

If a screen has several equally loud actions, the information hierarchy is broken.

### Required progression signals

The product should visibly track the decision journey.

Minimum counters to surface:
- number of `Prioritaire` films
- number of unresolved conflicts

Recommended progression copy:
- `Selection en cours`
- `Arbitrage requis`
- `Planning presque complet`

Do not gamify this with fake achievement language.
This is decision support, not habit tracking.

### Empty, loading, and transition states

The current product cannot feel guided if these states are weak or absent.
That would be a structural UX failure.

#### `Films` empty states

**Case: no films match current filters**  
Message: `Aucun film ne correspond a vos filtres.`  
Action: `Reinitialiser les filtres`

**Case: no films have been prioritized yet**  
Message: `Commencez par qualifier quelques films pour construire votre selection.`  
Action: `Voir tous les films`

#### `Planning` empty states

**Case: no priority films selected yet**  
Message: `Vous n'avez pas encore assez de films qualifies pour arbitrer votre planning.`  
Action: `Retourner a Films`

**Case: no conflicts for now**  
Message: `Aucun conflit pour l'instant. Votre planning est lisible sur cette plage.`  
Action: `Retourner a Films`

#### Loading states

Use skeleton screens, not generic spinners, for content-heavy views.

- `Films`: skeleton list preserving card rhythm
- `Planning`: skeleton timeline preserving time columns and block heights

The layout must remain stable while loading.
No jumping UI.

#### Transition messages

Important transitions should confirm consequence, not just success.

Examples:
- `Film passe en Prioritaire`
- `Cette seance remplace votre choix precedent de 20:30`
- `Creneau de 14:00 complete avec une option moyenne`

Avoid vague toasts such as `Updated` or `Done`.
That language says nothing.

### Workflow guardrails

- `Films` must stay the entry point for desire-based selection.
- `Planning` must show decisions first, not all possible data.
- `Settings` must stay secondary.
- Each step must reduce uncertainty before exposing the next one.

### Immediate implementation target for P0

For the next iteration, the product only needs to make the flow legible.
Not richer. Legible.

Minimum deliverables:
- visible workflow navigation for the active steps
- one-line UX promise per main view
- one dominant CTA per screen
- real empty states for the 3 core workflow views
- progression counters in navigation or view headers

If these pieces are missing, the workflow is still implicit, and implicit workflow is exactly the current weakness.

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

---

## P1 Detailed Note — Films as an Editorial Selection Workspace

### Purpose

Step 1 exists to help the user qualify desire before dealing with scheduling constraints.

This is not a raw catalogue dump.
This is not a planner disguised as a list.
This is an editorial decision workspace.

The user should leave this screen with a clear preference structure:
- what I strongly want to see
- what I may see
- what I can ignore

### User questions this screen must answer

The screen should answer these questions quickly:
- Why is this film interesting?
- Is it strong enough to mark as `Prioritaire`?
- Have I already triaged enough films to move on?
- Which films still need a decision?
- Can I compare a few candidates without reading everything?

If the screen requires long scanning before desire signals emerge, the hierarchy is wrong.

### Core content payload

The following elements are mandatory in the main film card because they support choice directly:
- title
- year
- tagline
- director
- cast
- country
- duration

These are not decorative metadata.
They are part of the decision payload.

Priority is an overlay on top of this payload, not a replacement for it.

### Screen intention

`Films` should feel like a curated selection workspace structured by cycle.

Its job is to help users:
- scan quickly
- notice promising films
- commit a preference level
- keep enough context to justify that preference

It should not optimize for exhaustive data density.
That choice would be a UX regression.

### Recommended page structure

#### 1. Header block
Purpose:
- orient the user
- show progress
- expose one next step

Content:
- page title: `Films`
- support line: `Qualifiez les films avant d'arbitrer les seances.`
- counters:
  - `X Prioritaires`
  - `Y Moyens`
  - `Z Restants a trier`
- primary CTA: `Passer au Planning`

Behavior:
- CTA enabled only when the user has enough prioritized films to make planning meaningful
- if not enabled, explain why in plain language

Example helper copy:
- `Selectionnez au moins quelques films prioritaires pour lancer l'arbitrage.`

#### 2. Utility bar
Purpose:
- support triage without stealing attention from content

Allowed controls:
- search
- filter by priority
- filter by day if relevant to the dataset
- sorting/grouping mode

Not allowed:
- dense expert filter matrices
- too many simultaneous toggles
- hidden advanced logic as a default mode

#### 3. Cycle-led content structure

The main structure of the page must remain **cycle-first**.

This is not optional if cycle is the first editorial selection criterion.
Flattening films into global priority buckets would be a UX mistake.

Recommended page structure:
- cycle block
- cycle summary
- cycle-local progress signals
- films inside that cycle

Inside each cycle, keep a simple flat list if the status control and progress signals already carry enough meaning.

Implementation note:
- avoid redundant status grouping if it adds visual noise
- status can remain visible through inline controls, counters, and dots alone

This gives the right hierarchy:
- first: editorial universe / cycle
- second: decision progress inside that universe

Transitional mapping for the current data model:
- `unreviewed` => `A traiter`
- `high` / `must-see` => `Prioritaires`
- `medium` => `Moyens`
- `ignore` => `Ignores`

Product rule:
- films must start with no prior decision
- the initial state is `A traiter`, not a weak hidden priority

Reason:
- cycle preserves the programming context
- local progress signals make decision state visible
- the user can qualify films without losing the logic of the festival selection

#### 4. Cycle header behavior

Each cycle header should contain:
- cycle name
- strong typographic treatment
- optional short cycle summary if available
- number of films in the cycle
- local counters:
  - `X Prioritaires`
  - `Y Moyens`
  - `Z Ignores` or `Z restant a qualifier` depending on the final data rule
- collapse/expand action if useful

The cycle header must support orientation.
It must not become a control cockpit.

What to avoid in the cycle header:
- multiple dominant actions
- dense priority visualizations that require decoding
- noisy badge accumulation

Important:
- cycle is a reading structure, not a decision object
- priority belongs to individual films only
- there should be no cycle-level priority control in the MVP
- progress dots may remain if they summarize film distribution inside the cycle
- cycle-specific color chips are not required if typography does the separation better
- planning should ignore films still in `A traiter`

Visual direction:
- cycle headers may use a subtle highlighter / ink treatment behind the title
- the effect must feel paper-like and editorial, not playful or flashy
- typography remains the primary separator; the highlight is support, not the structure itself

#### 5. Film cards / list items

Each card should support a fast F-pattern scan.
The user must identify title, desirability cues, and priority state in seconds.

### `FilmCard` component spec

#### Content hierarchy

Visual order of importance:
1. title
2. tagline
3. editorial metadata block
4. priority control
5. secondary actions

Concrete metadata line:
- `Realisateur`
- `Casting`
- `Pays · Annee · Duree`

Recommended compact composition:
- **Row 1:** title + year + priority badge/select
- **Row 2:** tagline
- **Row 3:** director
- **Row 4:** cast
- **Row 5:** country / year / duration
- **Row 6:** contextual scheduling hint if genuinely useful

### Variants

#### `FilmCard/Editorial`
Default card for the main `Films` view.

Characteristics:
- full editorial payload visible
- generous text rhythm
- strong title emphasis
- restrained utility chrome
- typographic contrast should do most of the hierarchy work

#### `FilmCard/Compact`
Optional reduced variant for dense subsections or mobile continuation.

Characteristics:
- title remains dominant
- tagline may truncate to 2 lines
- cast may truncate to 1 line
- priority control remains visible

Do not use a purely tabular row as the default desktop variant.
That would flatten the selection experience.

### States

Minimum states required:
- `default`
- `hover`
- `focus-visible`
- `selected-prioritaire`
- `selected-moyen`
- `selected-ignore`
- `loading`
- `empty-section`
- `error`

Optional if data exists:
- `already-scheduled`
- `has-screening-conflicts`

These optional scheduling signals must remain secondary in `Films`.
If they dominate, the screen loses its role.

State direction:
- do not add card-level hover treatments that imply the whole card is clickable when it is not
- `focus-visible` must stay attached to actual interactive controls
- selected states belong primarily to the inline priority control, not to a large decorative card background

### Priority control

Recommended component: `PrioritySelect` inline in card header zone.

UX definition:
- this is the film qualification control
- it is the main action of the card
- if the name `PrioritySelect` becomes misleading, rename it later to something closer to `FilmPriorityToggle`

Behavior:
- always visible
- keyboard accessible
- immediate update feedback
- no modal required

Allowed values only:
- `Immanquable`
- `Peut-etre`
- `Non merci`

Copy rule:
- prefer explicit, human wording over coded abbreviations
- avoid labels like `I / M / P`, which require decoding and create unnecessary cognitive load

Product rule:
- priority exists at film level only
- cycle never overrides film priority
- cycle helps exploration and orientation, not preference assignment

Microcopy rule:
- explicit labels
- no cryptic icons without text

### Secondary actions

Allowed:
- `Voir les seances`
- `Voir plus`

Not allowed as equally dominant actions:
- multiple schedule actions per card
- compare, bookmark, share, hide, expand, and queue all at once

Too many actions here would explode cognitive load.

### Scheduling hint inside Films

Scheduling information may exist, but it must stay subordinate.

Good examples:
- `3 seances disponibles`
- `Prochaine seance aujourd'hui a 18:15`
- `Conflits possibles avec 2 choix prioritaires`

Rule:
- `pas de seance prevue` should be reserved for `Prioritaire` films
- this warning is unnecessary noise for `Moyen`

Visual hierarchy rule:
- do not express the same status through structure, control, and summary if the inline control plus cycle-level signals are already sufficient

Bad examples:
- full timetable inside the card
- detailed conflict matrix
- multiple slot-level CTAs

`Films` qualifies desire first. Scheduling remains a hint at this stage.

### Recommended information density

Desktop:
- comfortable vertical rhythm
- enough whitespace to preserve editorial reading
- no badge pile-ups
- title can feel denser and slightly larger than the metadata system
- metadata should recede without becoming faint or fragile

Mobile:
- one card column
- keep title, tagline, priority, and director always visible
- cast and metadata may collapse slightly, but must not disappear entirely

Typography direction inside cards:
- title: compact, editorial, slightly tighter tracking
- tagline: readable italic support line, not decorative whisper text
- metadata: quieter, smaller, more utilitarian
- schedule hint: light chip treatment acceptable if it improves scanability

### Future visual direction to explore later

Possible art direction for cycle headers:
- larger titles
- slightly organic paper-like emphasis
- subtle `stabilo` feeling

Constraint:
- this can enrich character later
- it must not weaken readability or decision clarity

### Suggested design tokens and layout values

These values should be treated as implementation targets, not vague inspiration.

#### Card
- padding: `16px`
- vertical gap: `8px`
- border radius: `12px`
- border: `1px solid color-mix(in srgb, var(--color-foreground) 10%, transparent)`
- background: `color-mix(in srgb, var(--color-background) 92%, var(--color-foreground) 8%)`

#### Section spacing
- page vertical gap: `24px`
- section header bottom margin: `12px`
- card stack gap: `12px`

#### Typography
- title: `font-size 1rem` to `1.125rem`, `font-weight 600`
- tagline: `0.95rem`, `line-height 1.45`, slightly brighter than metadata
- metadata: `0.875rem`, foreground with reduced opacity
- helper text: `0.8125rem`

#### State signals
- `Prioritaire`: accent-filled or accent-emphasized outline
- `Moyen`: neutral with moderate foreground emphasis
- `Ignorer`: subdued foreground and reduced contrast
- `focus-visible`: clear 2px accent ring, WCAG-compliant

Do not introduce three unrelated colors for the three priority levels.
That would break the visual system already established.

### Accessibility requirements

Non-negotiable:
- full keyboard navigation through cards and priority controls
- visible focus state on every interactive element
- AA contrast minimum on text and controls
- priority state must never rely on color alone
- truncated text must expose full content via accessible reveal pattern if needed

If the card is clickable as a whole and contains controls, interaction zones must be unambiguous.
Nested affordances are otherwise error-prone.

### Empty, loading, and error states for `Films`

#### Empty section inside a cycle: `A traiter`
Message: `Tous les films de ce cycle ont deja ete qualifies.`
Action: `Voir les Prioritaires du cycle`

#### Empty section inside a cycle: `Prioritaires`
Message: `Aucun film prioritaire dans ce cycle pour l'instant.`
Action: `Marquer un film du cycle comme Prioritaire`

#### Loading
- preserve final card heights
- show placeholder title, tagline, and metadata rows
- keep progress counters skeletonized in the header

#### Error
Message: `Impossible de charger les films pour le moment.`
Action: `Reessayer`

### Anti-patterns to avoid

- Turning the view into a sortable spreadsheet.
- Hiding tagline or reducing it to decorative whisper text.
- Making priority louder than the film itself.
- Injecting too many scheduling mechanics into card bodies.
- Multiplying badges for genre, country, duration, venue, state, and recommendation at once.
- Using truncation so aggressively that films become indistinguishable.

### First implementation target for P1

V1 scope only:
- progress-aware `Films` header
- cycle-first structure with local decision sections
- stabilized editorial `FilmCard`
- visible inline `PrioritySelect`
- restrained scheduling hint
- real empty/loading/error states

Delivery order:
1. lock section model
2. stabilize card hierarchy
3. make priority update immediate and calm
4. add progress counters and gateway CTA to Planning
5. refine empty/loading/error states

Success criteria:
- a user can triage films quickly without losing editorial context
- priority is visible at a glance but does not flatten the content
- the view feels like a selection stage, not a tool dump
