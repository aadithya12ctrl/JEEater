# 🌊 LearnFlow — App Flow
### *Every screen. Every decision. Every pink dot.*

---

## Flow Map Overview

```
LANDING
  └── Sign Up / Log In
        └── ONBOARDING (chapter select + profile bootstrap)
              └── SESSION HUB (home between sessions)
                    ├── NEW SESSION
                    │     └── CHAPTER BRIEF VIEW
                    │           └── SESSION SCREEN ←─────────────────┐
                    │                 ├── Socratic Flow               │
                    │                 ├── Concept Cinema Flow         │
                    │                 ├── Gap Explainer Flow          │
                    │                 ├── Closure Check Flow          │
                    │                 ├── Anti-Overing Flow           │
                    │                 └── DRIFT ALERT STATE ──────────┘
                    │                       └── Re-anchor → resume
                    │
                    ├── PROFILE VIEW
                    └── REVISION QUEUE
```

---

## Screen 1 — Landing

**Entry point for new and returning users.**

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   "The exam doesn't reward knowing.                 │
│    It rewards thinking."       [Agent Web SVG]      │
│                                                     │
│   8 AI agents. Zero answer-giving. All principle.   │
│                                                     │
│   [ Start for Free → ]    [ Log In ]                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Decisions here:**
- `Start for Free` → Screen 2a (Sign Up)
- `Log In` → Screen 2b (Log In) → Screen 4 (Session Hub)

---

## Screen 2a — Sign Up

**Fields:** Name · Email · Password · Exam target (JEE / NEET / Both)

**On submit → Screen 3 (Onboarding)**

---

## Screen 2b — Log In

**Fields:** Email · Password · Forgot password link

**On success:**
- Returning user with active session → Screen 5 (Session Screen, restored)
- Returning user, no active session → Screen 4 (Session Hub)

---

## Screen 3 — Onboarding

**Purpose:** Bootstrap the Adaptive Profile without asking the student their level. Everything inferred from choices, not self-report.

**Step 1 — Chapter Select**
```
┌────────────────────────────────────────────────────┐
│  ✦  What are you working on right now?             │
│                                                    │
│  [ Laws of Motion ]  [ Work & Energy ]             │
│  [ Rotational Dynamics ]  [ Electrostatics ]  ...  │
│                                                    │
│  Pink pill chips, multi-select allowed             │
└────────────────────────────────────────────────────┘
```

**Step 2 — Calibration Problem**
One JEE-style problem for the selected chapter. Student attempts it. No result shown — this seeds the profile silently.

```
┌────────────────────────────────────────────────────┐
│  📐 Quick warm-up — no pressure, no score          │
│                                                    │
│  [Problem text]                                    │
│                                                    │
│  Your attempt:  ___________________________        │
│                 ___________________________        │
│                                                    │
│  [ Submit & Continue → ]   [ Skip for now ]        │
└────────────────────────────────────────────────────┘
```

**What happens on submit:**
- Adaptive Profile Agent ingests the attempt
- Infers `depth_preference`, seeds `gap_frequency` for this chapter
- No verdict shown to student — profile is silent

**On complete → Screen 4 (Session Hub)**

---

## Screen 4 — Session Hub

**Home between sessions. The student's base camp.**

```
┌─────────────────────────────────────────────────┐
│  Hi, [Name] ✦                        [Profile]  │
│                                                 │
│  ── TODAY'S REVISION QUEUE ──                   │
│  Based on decay score × gap frequency           │
│                                                 │
│  1. Non-inertial frames         [Start →]       │
│  2. Pseudo-force applications   [Start →]       │
│  3. Angular momentum            [Start →]       │
│                                                 │
│  ── OR START FRESH ──                           │
│  [ Choose a chapter → ]                         │
│                                                 │
│  ── RECENT SESSIONS ──                          │
│  Laws of Motion · 47 min · 3 concepts closed    │
│  [ Resume ] [ View Summary ]                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Decisions here:**
- Tap a revision queue item → Screen 4a (Chapter Brief), chapter pre-selected
- `Choose a chapter` → Chapter picker sheet → Screen 4a
- `Resume` → Screen 5 (Session Screen, session restored from checkpoint)
- `View Summary` → Screen 6 (Session Summary, read-only)
- `Profile` icon → Screen 7 (Profile View)

---

## Screen 4a — Chapter Brief View

**Shown once per chapter, before the first session on it. Generates on demand.**

```
┌──────────────────────────────────────────────────────┐
│  ✦ LAWS OF MOTION                                    │
│  Chapter Brief — generated for you                   │
│                                                      │
│  CENTRAL QUESTIONS                                   │
│  • Why does F=ma take that form and not another?     │
│  • When does Newton's third law feel wrong?          │
│  • What breaks when you pick a non-inertial frame?   │
│                                                      │
│  DEPENDENCY ORDER                                    │
│  Vectors → Free Body Diagrams → Newton I → Newton II │
│  → Newton III → Non-inertial frames                  │
│                                                      │
│  ARCHETYPE SIGNATURES (3 types to recognise)         │
│  ◆ Tension problems    ◆ Pseudo-force problems       │
│  ◆ Constraint motion                                 │
│                                                      │
│  COMMON MISCONCEPTIONS                               │
│  • Heavier objects don't fall faster (still appears) │
│  • Normal force ≠ reaction to gravity                │
│                                                      │
│  [ Let's Start → ]                                   │
└──────────────────────────────────────────────────────┘
```

`Let's Start →` → Screen 5 (Session Screen, new session)

---

## Screen 5 — Session Screen

**The core. Three-panel layout (see frontend.md). All agent flows live here.**

```
┌──────────────────┬────────────────────────┬──────────────┐
│  LEFT SIDEBAR    │   CENTER CHAT          │  RIGHT PANEL │
│                  │                        │              │
│  Chapter chip    │  Message thread        │  Drift Ring  │
│  Agent roster    │  Active agent badge    │  IDMS live   │
│  Session timer   │  Input bar             │  Profile     │
└──────────────────┴────────────────────────┴──────────────┘
```

**Session always starts via the Orchestrator.** Student types their first message. Orchestrator reads it + profile and routes to the appropriate agent. From here the session branches into one of five agent flows.

---

## Agent Flow A — Socratic Flow

**Triggered when:** student is stuck, first entering a problem, or Orchestrator detects confusion.

```
Student input
    │
    ▼
ORCHESTRATOR routes → SOCRATIC AGENT
    │
    ▼
┌─────────────────────────────────────────┐
│  Entry Protocol — 4 steps               │
│                                         │
│  Step 1: "What is the problem giving?"  │
│  Step 2: "What is it asking for?"       │
│  Step 3: "What connects the two?"       │
│  Step 4 (if stuck): Visual Opening Move │
└──────────────────────┬──────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
  Student bridges             Student can't bridge
  (Step 3 answer              after Step 4
   sufficient)
          │                         │
          ▼                         ▼
  DIAGRAM GATE                Route back to
  ─────────────               Step 1 with
  "Describe your              different angle
   setup before
   we calculate."
          │
    ┌─────┴──────┐
    ▼             ▼
Diagram        No diagram
described      described
    │             │
    ▼             ▼
Unlock          Stay in
calculation     Socratic
routing         loop
    │
    ▼
IDMS CHECK → profile_update → END
```

**UI state during Socratic flow:**
- Left sidebar: Socratic Agent lit up pink, pulsing dot
- Chat: agent messages have blue left-border
- Input bar placeholder: `"Describe your thinking — what do you see in this problem?"`
- Diagram Gate activated → a soft pink banner appears above the input: `"Describe your diagram setup first 🎨"`

---

## Agent Flow B — Concept Cinema Flow

**Triggered when:** student needs to learn a concept from scratch.

```
ORCHESTRATOR routes → CINEMA AGENT
    │
    ▼
┌───────────────────────────────────────────────────┐
│  5-Beat Sequence                                  │
│                                                   │
│  BEAT 1 ─ Intuition Hook (no math)           ✓   │
│           "Why does a spinning skater                │
│            speed up when arms pull in?"           │
│                                                   │
│  BEAT 2 ─ Analogy Bridge                     ✓   │
│           Structural analogy to familiar idea     │
│                                                   │
│  BEAT 3 ─ Checkpoint  ← GATE                 ⏸   │
│           Student must respond before Beat 4      │
│           unlocks. "In your own words — why?"     │
│                ↓                                  │
│         Student response                         │
│                ↓                                  │
│    ┌───────────┴────────────┐                     │
│    ▼                        ▼                     │
│  ADEQUATE              NOT ADEQUATE               │
│  → Beat 4 unlocks      → Re-ask with              │
│                          different angle          │
│                                                   │
│  BEAT 4 ─ Formalism (formula arrives here)   ✓   │
│  BEAT 5 ─ Why This Form                      ✓   │
│                                                   │
└───────────────────────────────────────────────────┘
    │
    ▼
IDMS CHECK → profile_update → END
```

**UI state during Cinema flow:**
- Center panel switches to dark Cinema mode (`#1A1A2E` bg) with film-strip beat indicators
- Beat 3: padlock icon appears on Beat 4 panel — bounces and disappears when student submits adequate response
- Beat labels visible at top of panel: `● ● ⏸ ○ ○` (filled = complete, paused = waiting, empty = not yet)
- Beats 4–5 are visually "behind a curtain" until Beat 3 clears

---

## Agent Flow C — Gap Explainer Flow

**Triggered when:** student has a solution attempt with a missed logical step.

```
Student submits attempt
    │
    ▼
ORCHESTRATOR routes → GAP EXPLAINER AGENT
    │
    ▼
Agent receives: student attempt + standard solution (from DB)
    │
    ▼
Identifies single logical transition that was skipped
    │
    ▼
┌─────────────────────────────────┐
│  WHAT YOU KNEW                  │
│  [one sentence]                 │
│                                 │
│  THE GAP                        │
│  [one sentence — logical move]  │
│                                 │
│  WHAT IT UNLOCKED               │
│  [one sentence]                 │
└─────────────────────────────────┘
    │
    ▼
Student reads → responds with follow-up or confirms
    │
    ├── Follow-up question → back to Orchestrator (re-routes)
    └── Confirms → CLOSURE CHECK triggered
              │
              ▼
        Closure Agent Flow (see Flow D)
    │
    ▼
IDMS CHECK → profile_update → END
```

**UI state during Gap flow:**
- Agent messages have coral left-border
- The three-part response renders as three distinct cards stacked vertically inside the message bubble, each with its own pink label eyebrow (`WHAT YOU KNEW` / `THE GAP` / `WHAT IT UNLOCKED`)
- `THE GAP` card has a subtle hot coral background tint — it's the point

---

## Agent Flow D — Closure Check Flow

**Triggered when:** student claims to understand a concept, or after a Gap Explainer resolution.

```
ORCHESTRATOR routes → CLOSURE AGENT
    │
    ▼
Closure question delivered:
"In your own words — why does [concept] work this way?"
    │
    ▼
Student responds
    │
    ▼
Agent evaluates against COVERED / CLOSED distinction
    │
    ├─── COVERED ──────────────────────────────────────────┐
    │    (student can state, not explain WHY)               │
    │         │                                             │
    │         ▼                                             │
    │    Follow-up question targeting specific gap          │
    │    Student responds → re-evaluated                    │
    │    Loops until CLOSED or max 3 rounds → Socratic      │
    │                                                       │
    └─── CLOSED ───────────────────────────────────────────┘
              │
              ▼
         Concept chip animates into profile panel (pop-in spring)
         "✓ Energy Conservation" chip added to right panel
         Next concept that builds on this one is surfaced
              │
              ▼
         IDMS CHECK → profile_update → END
```

**UI state during Closure flow:**
- Agent messages have pink left-border
- `COVERED` verdict: message card has a soft sandy background, follow-up question in pink bold
- `CLOSED` verdict: message card has a white background with a pink checkmark badge top-right, concept chip animates into the profile panel on the right
- Profile panel updates live: gap bar for this concept fills from current % → higher

---

## Agent Flow E — Anti-Overing Flow

**Triggered when:** Orchestrator detects pattern-matching, or student solves correctly but can't explain method selection.

```
ORCHESTRATOR routes → ANTI-OVERING AGENT
    │
    ▼
Agent selects tool based on context:
    │
    ├── WRONG PATH SIMULATOR
    │   "Here's a solution that gets the wrong answer.
    │    Find the step where the reasoning fails."
    │         │
    │         ▼
    │   Student identifies step → Agent evaluates
    │   ● Correct identification → Structural Transfer next
    │   ● Missed it → Hint + re-ask
    │
    ├── STRUCTURAL TRANSFER
    │   Two structurally identical but visually different problems shown
    │   "What's the shared structure?"
    │         │
    │         ▼
    │   Student identifies principle → evaluated
    │   ● Correct → Metacognitive Review
    │   ● Incorrect → Socratic routing
    │
    └── METACOGNITIVE REVIEW
        "What signal in the problem made you choose
         energy conservation over momentum?"
              │
              ▼
        ┌─────────────────────────────────────┐
        │  PROCEDURE SUCCESS / PRINCIPLE FAIL │  ← most dangerous state
        │  Student got answer, wrong reason   │
        └──────────────────┬──────────────────┘
                           │
                           ▼
              Flag in profile + route to Cinema
              for the underlying principle
                           │
                           ▼
        ┌──────────────────────────┐
        │  PRINCIPLE CLOSED        │
        │  Method selection sound  │
        └──────────────────────────┘
              │
              ▼
         IDMS CHECK → profile_update → END
```

**UI state during Anti-Overing flow:**
- Agent messages have mint/green left-border
- Wrong Path Simulator: the "wrong solution" renders in a distinct card with a subtle red-pink tint and a 🔍 icon — visually flagged as "find the error"
- Structural Transfer: two problem cards side-by-side (stacked on mobile), connected by a pink double-arrow `⟷`
- `PROCEDURE SUCCESS / PRINCIPLE FAILURE` verdict: a coral chip animates onto the profile panel — not punitive, just tracked

---

## IDMS Check — After Every Agent Turn

**Not a screen — a system node that runs invisibly after every agent response.**

```
Agent produces response
    │
    ▼
IDMS.check_and_intervene(state)
    │
    ├── drift_magnitude < 0.72 ──────────────────────────┐
    │                                                     │
    │   No intervention. State passes through.            │
    │                                                     │
    └── drift_magnitude ≥ 0.72 ──────────────────────────┘
              │
              ▼
        ┌────────────────────────────────────┐
        │  DRIFT ALERT STATE                 │
        │                                   │
        │  • Drift Ring → coral flash        │
        │  • Banner: "Recalibrating ✦"       │
        │  • Proxy Agent runs independently  │
        │  • Gate value computed             │
        │  • Perturbation injected           │
        │  • Behavioral anchors re-applied   │
        └────────────────────┬───────────────┘
                             │
                             ▼
                    Proxy Agent → profile_update
                             │
                             ▼
                  Session resumes normally
                  Banner auto-dismisses (4s)
                  Drift Ring transitions back to pink
```

**UI changes during Drift Alert:**

| Element | Normal state | Drift Alert state |
|---|---|---|
| Drift Ring | Pink pulse, slow breathe | Coral flash, `drift-glow` shadow |
| Ring center value | e.g. `0.34` | e.g. `0.81` in coral |
| Top banner | Hidden | `⚡ Recalibrating the session ✦` (coral, 4s) |
| Active agent border | Agent color | Coral during re-anchor |
| Agent badge | Normal | `IDMS INTERVENING` chip appears, fades |
| IDMS panel rows | Normal values | Gate value row highlighted pink |

---

## Screen 6 — Session Summary

**Shown at end of session or via "View Summary" from Session Hub.**

```
┌─────────────────────────────────────────────────┐
│  Laws of Motion · 47 min                        │
│  ──────────────────────────────────────────     │
│                                                 │
│  CONCEPTS CLOSED (3)                            │
│  ✓ Free Body Diagrams                           │
│  ✓ Newton's Second Law                          │
│  ✓ Normal Force ≠ gravity reaction              │
│                                                 │
│  CONCEPTS COVERED, NOT CLOSED (2)               │
│  ◯ Non-inertial frames    → added to queue      │
│  ◯ Pseudo-force setup     → added to queue      │
│                                                 │
│  DRIFT EPISODES   2                             │
│  SOCRATIC ROUNDS (avg)    3.4                   │
│  AGENT DISTRIBUTION                             │
│  Socratic 42% · Cinema 28% · Gap 18%            │
│  Closure 8% · Anti-Overing 4%                   │
│                                                 │
│  [ Back to Hub ]   [ Resume Problem ]           │
└─────────────────────────────────────────────────┘
```

Drift Episodes shown as a small timeline strip at the bottom — thin horizontal bar, pink baseline, coral spikes at drift events.

---

## Screen 7 — Profile View

**Student's full behavioral model. Read-only. Updated silently by the system.**

```
┌─────────────────────────────────────────────────┐
│  YOUR PROFILE                                   │
│  Built from behavior, not self-report.          │
│  ──────────────────────────────────────────     │
│                                                 │
│  DEPTH PREFERENCE                               │
│  Derivation-first  ████████░░  78%              │
│                                                 │
│  TOP BREAKING POINTS                            │
│  1. Non-inertial frame selection                │
│  2. Newton III pair identification              │
│  3. Sign convention in rotational systems       │
│                                                 │
│  RECURRING ERROR PATTERNS                       │
│  • Pseudo-force direction (6 times)             │
│  • Free body diagram omission (4 times)         │
│                                                 │
│  CLOSED CONCEPTS   ██████████████████  14       │
│  COVERED, NOT CLOSED  ████████  8               │
│                                                 │
│  EXPLANATION STYLE                              │
│  Analogy-first  ●●●●○○  (inferred from          │
│                          follow-up patterns)    │
│                                                 │
└─────────────────────────────────────────────────┘
```

Progress bars fill in `#FF3EA5`. Barred items (breaking points) have a small coral dot. All labels: Poppins 11px caps, Deep Tan.

---

## State Persistence Rules

| State | Persisted | Where |
|---|---|---|
| Session message history | Yes | SQLite via LangGraph checkpointer |
| Active beat (Cinema) | Yes | LangGraph state |
| Drift magnitude | Session only | Redis |
| Trigger map | Session only | Redis |
| Student profile | Permanent | PostgreSQL |
| Revision queue | Permanent | PostgreSQL, recomputed on login |
| Chapter briefs | Cached 7 days | PostgreSQL |

**Resume behavior:** if a student closes the tab mid-session, `Resume` on the Session Hub restores from LangGraph checkpoint — they land back at the exact message, active beat, and drift state.

---

## Error & Edge State Handling

| Situation | UI response |
|---|---|
| Agent timeout (> 8s) | Spinner → `"Thinking hard — give it a moment ☀️"` after 4s |
| Beat 3 response inadequate (3rd attempt) | Cinema re-routes to Socratic for the concept instead |
| Socratic loop (5+ rounds, no breakthrough) | Orchestrator surfaces Gap Explainer for the specific stuck point |
| Closure loop (3× COVERED, no CLOSED) | Concept flagged, Cinema route triggered for underlying principle |
| IDMS drift persists after 2 interventions | Orchestrator prompts: `"Let's take a different angle on this."` and re-routes to Cinema |
| Network error | Toast: `"Lost the signal — reconnecting 🌊"` with pink loading dot |
| Empty first message | Input border pulses pink, placeholder: `"Anything — a question, a problem, even 'I don't know where to start'"` |

---

*LearnFlow — Training Principles, Not Procedures.*
*Designed for the beach. Built for the exam hall.* 🌊🎀
