# 🌊 LearnFlow Frontend Spec
### *Beyond Procedures, Towards Principles — dressed for the beach*

---

## ✨ Design Direction

**Vibe:** Malibu Barbie. Sun-bleached, unapologetically pink, dripping in confidence. This system is *serious science* wrapped in the most delightful possible shell. The drift equations are real. The math is hard. The aesthetic refuses to care.

**Core tension:** ML research-grade intelligence wearing a hot pink bikini. Lean into it — don't soften it.

---

## 🎨 Color Palette

| Name | Hex | Role |
|---|---|---|
| Barbie Pink | `#FF3EA5` | Primary CTA, active states, hero accent |
| Hot Coral | `#FF6B6B` | Warnings, drift alerts, danger states |
| Sun Blonde | `#FFF0A0` | Highlight chips, tag backgrounds |
| Malibu Blue | `#87CEEB` | Agent cards, calm states, info panels |
| Foam White | `#FFFBF8` | Page background |
| Sandy Nude | `#F5E6D3` | Section backgrounds, alternating rows |
| Deep Tan | `#8B5E3C` | Body text |
| Jet Black | `#1A1A1A` | Display headings, bold contrast |

> **Rule:** Pink is the hero. Everything else is set dressing. If a screen has no pink on it, something is wrong.

---

## 🔤 Typography

| Role | Face | Treatment |
|---|---|---|
| Display | `Playfair Display` | Bold italic, 64px+, used for hero statements only |
| Subheadings | `Poppins` | SemiBold 600, tracking +0.02em |
| Body | `DM Sans` | Regular 400, 16px, line-height 1.7 |
| Code / Data | `JetBrains Mono` | For drift scores, residual values, thresholds |
| Labels / Eyebrows | `Poppins` | 11px ALL CAPS, letter-spacing +0.12em, pink |

**Type Scale:**
```
hero:     Playfair Display Bold Italic — 72px / lh 1.1
h1:       Poppins SemiBold — 48px
h2:       Poppins SemiBold — 32px
h3:       Poppins Medium — 22px
body:     DM Sans Regular — 16px / lh 1.7
caption:  DM Sans Regular — 13px / color: #8B5E3C
mono:     JetBrains Mono — 13px / bg: #FFF0A0 pill
```

---

## 🏄 Signature Element

**The Drift Pulse Ring** — sits in the top-right corner of every session screen. A circular gradient ring (pink → coral → sky blue) that pulses at a rate proportional to the live `drift_magnitude` value. When drift is at 0, it breathes slowly like ocean waves. When drift spikes past `0.72`, it flashes hot coral with a little shimmer animation. It's the vibe check of the entire system — instantly readable, impossible to ignore.

---

## 📐 Layout System

**Grid:** 12-column, 24px gutters, max-width 1280px. Sections alternate between `#FFFBF8` and `#F5E6D3` backgrounds — no hard dividers, just soft sandy transitions.

**Spacing tokens:**
```
space-xs:   4px
space-sm:   8px
space-md:   16px
space-lg:   32px
space-xl:   64px
space-2xl:  128px
```

**Border radius:**
```
pill:     9999px  (chips, tags, buttons)
card:     24px    (agent cards, panels)
input:    12px    (text fields)
modal:    32px
```

**Shadows:**
```
card-rest:   0 2px 16px rgba(255, 62, 165, 0.08)
card-hover:  0 8px 40px rgba(255, 62, 165, 0.18)
drift-glow:  0 0 32px rgba(255, 107, 107, 0.35)   /* activated on high drift */
```

---

## 🖼️ Pages & Screens

---

### 1. Landing / Hero

**Layout:** Full-bleed, two-column split. Left: headline + CTA. Right: the Agent Web (animated SVG, 8 nodes orbiting each other).

**Hero headline:**
```
"The exam doesn't
 reward knowing.
 It rewards
 *thinking.*"
```
Playfair Display Bold Italic. Black on white. The word *thinking* renders in `#FF3EA5`.

**Subheadline:** DM Sans, 20px, Deep Tan:
```
JEE/NEET prep designed around your brain, not a textbook.
8 AI agents. Zero answer-giving. All principle.
```

**CTA Button:**
- Label: `Start a Session →`
- Background: `#FF3EA5`
- Text: white, Poppins SemiBold
- Border radius: pill
- Hover: scale 1.03, shadow intensifies
- Active: scale 0.98

**Agent Web (right side):**
SVG canvas, 480×480px. 8 nodes arranged in loose orbit. Each node is a circle:
- Orchestrator: center, 48px, Barbie Pink
- Socratic, Gap, Closure, Cinema, Anti-Overing, Adaptive Profile: outer ring, 32px, Malibu Blue
- Adversarial Proxy: outermost, 24px, Hot Coral, dashed border stroke

Connection lines between nodes pulse opacity 0.2→0.8 based on simulated drift scores. The Proxy node always has a slightly broken/flickering line to emphasize its structural independence.

Node labels: Poppins 10px, ALL CAPS, pink eyebrow style.

---

### 2. Session Screen

**Layout:** Three panels.

```
┌──────────────────┬────────────────────────┬──────────────┐
│  LEFT SIDEBAR    │   CENTER CHAT          │  RIGHT PANEL │
│  (280px)         │   (flex-grow)          │  (320px)     │
│                  │                        │              │
│  • Session info  │  • Message thread      │  • Drift Ring│
│  • Chapter       │  • Active agent badge  │  • IDMS live │
│  • Agent roster  │  • Input bar           │  • Profile   │
│                  │                        │              │
└──────────────────┴────────────────────────┴──────────────┘
```

**Left Sidebar:**
- Background: `#F5E6D3`
- Current chapter displayed as a pink pill chip at the top
- Agent roster as a vertical list — inactive agents are `#8B5E3C` dim, active agent pulses pink with a glowing dot indicator
- Session timer (Poppins Mono-style, small)

**Center Chat:**
- Background: `#FFFBF8`
- Student messages: right-aligned, `#FF3EA5` bubble, white text, pill border radius
- Agent messages: left-aligned, white card, `#1A1A1A` text, 24px border radius, with an agent badge (colored dot + agent name eyebrow) in the top-left corner of each card
- Each agent message card has a subtle colored left-border: Socratic = blue, Gap = coral, Closure = pink, Cinema = yellow, Anti-Overing = green

**Message Agent Badges:**
```
● SOCRATIC AGENT     (Malibu Blue dot)
● GAP EXPLAINER      (Hot Coral dot)
● CLOSURE AGENT      (Barbie Pink dot)
● CONCEPT CINEMA     (Sun Blonde dot)
● ANTI-OVERING       (Mint dot)
```

**Input Bar:**
- Floating above bottom of center panel
- White pill, 56px height, full-width minus padding
- Pink send button (arrow icon, circle, `#FF3EA5`)
- Placeholder: `"Ask anything — or just say what's confusing you."`
- Focus state: pink border glow (`box-shadow: 0 0 0 3px rgba(255,62,165,0.25)`)

**Right Panel — IDMS Live Dashboard:**
- Background: `#FFFBF8`, border-left: `2px solid #F5E6D3`

Components stacked vertically:

**Drift Pulse Ring** (top, centered):
- 160px circle
- Gradient stroke: pink → coral
- Animated rotation + pulse based on `drift_magnitude`
- Center text: large mono value e.g. `0.34` with label `DRIFT` below
- Color shifts: `< 0.4` = blue calm, `0.4–0.72` = pink warning, `> 0.72` = coral alarm + `drift-glow` shadow

**IDMS Status Card:**
- Title eyebrow: `SYSTEM STATUS`
- Three indicator rows:
  ```
  Proxy Window     ● Active      [episode 2]
  Trigger Map      ● Tracking    [coherence 0.81]
  Gate Value       ● 0.64        [↑ accelerating]
  ```
- Each row: label (Poppins 11px caps), colored dot, mono value

**Student Profile Snapshot:**
- Title eyebrow: `YOUR PROFILE`
- Mini progress bars for top 3 gap areas (e.g. "Newton's Laws · 78%")
- Bars fill in `#FF3EA5`, background `#F5E6D3`
- Small tag chips for recent concept closures: `✓ Energy Conservation`, `✓ Kinematics`

---

### 3. Agent Detail Cards (hover/expand state)

When a student clicks an agent name in the sidebar, a card expands (slide-down animation, 300ms ease-out):

```
┌────────────────────────────────────────┐
│  ● SOCRATIC AGENT                      │
│  ─────────────────────────────────────│
│  Role: Entry Protocol + Diagram Gate   │
│                                        │
│  Drift Risk: Semantic                  │
│  Anchor: "Every response ends          │
│           with a question mark."       │
│                                        │
│  ASI Score:  ████████░░  0.84          │
│  Outputs:    142 this session          │
└────────────────────────────────────────┘
```

Card background: `#FFFBF8`
Border: `2px solid #FF3EA5`
Border radius: `24px`
ASI bar fills in pink, depletes toward coral as score drops.

---

### 4. Drift Alert State

When `drift_magnitude > 0.72`, the UI enters **Drift Alert Mode**:

- The Drift Ring flashes coral with the `drift-glow` shadow
- A slim banner slides down from the top of the center panel:
  ```
  ⚡  Intent drift detected · Re-anchoring agents · Episode 3
  ```
  Background: `#FF6B6B`, white text, pill, auto-dismisses after 4s
- The active agent's left-border in chat turns coral during re-anchor
- An `IDMS INTERVENING` chip appears temporarily on the agent badge

---

### 5. Concept Cinema Screen

Triggered when Cinema Agent is active. The center panel transforms:

**Layout:** Full-bleed dark-ish panel (`#1A1A2E` as a rare exception to the light theme) with a "film strip" aesthetic — warm contrast against the overall Malibu palette.

```
┌─────────────────────────────────────────┐
│  🎬  CONCEPT CINEMA                     │
│  ─────────────────────────────────────  │
│                                         │
│  [ Beat 1: The World Before ]           │
│  ──────────────────────────             │
│  Animation / diagram area               │
│                                         │
│  [ Beat 2: The Disruption ]             │
│  ──────────────────────────             │
│  ...                                    │
│                                         │
│  [ Beat 3: The Resolved World ]   🔒    │
│  — unlocked after your prediction —     │
│                                         │
└─────────────────────────────────────────┘
```

Beat labels: `Poppins SemiBold`, white
Beat 3 lock icon: pink padlock — student must type their prediction before it unlocks (input glows pink on focus, padlock bounces and disappears on submit)

---

### 6. Mobile (< 768px)

- Left sidebar collapses to a bottom tab bar (4 tabs: Chat, Agents, IDMS, Profile)
- Right panel becomes a slide-up drawer, triggered by tapping the Drift Ring (which lives as a floating 48px button in the bottom-right corner)
- Chat takes full screen width
- Agent badges condense to dot + initials

---

## 🧩 Component Library

### Button Variants
```
Primary:    bg #FF3EA5, white text, pill, hover scale 1.03
Secondary:  border 2px #FF3EA5, pink text, transparent bg
Ghost:      no border, pink text, underline on hover
Danger:     bg #FF6B6B (drift/error contexts)
Disabled:   opacity 0.4, no pointer events
```

### Tag / Chip Variants
```
Concept:    bg #FFF0A0, Deep Tan text, pill, 11px Poppins caps
Agent:      colored dot + agent name, white bg, card radius
Status:     ● Active (green dot) / ● Drifting (coral) / ● Anchored (pink)
Math:       bg #F5E6D3, JetBrains Mono, small, monospace
```

### Input States
```
Default:   border #F5E6D3
Focus:     border #FF3EA5, pink glow shadow
Error:     border #FF6B6B
Filled:    border #8B5E3C light
```

---

## 💫 Motion Design

| Interaction | Animation |
|---|---|
| Page load | Staggered fade-up, 40px translate, 500ms ease-out, 80ms stagger |
| Agent switch | Left panel item pulses pink → new agent card slides in from right |
| Message arrive | Scale 0.95 → 1.0, fade in, 200ms spring |
| Drift alert | Banner slides down 300ms, Drift Ring switches to coral pulse |
| Drift clear | Ring breathes back to slow pink, banner slides up |
| Cinema unlock | Padlock bounces (keyframes: 0% normal, 40% scale 1.3 rotate -10deg, 70% scale 0.9, 100% 0 opacity) |
| Concept chip appear | Pop in with spring overshoot (scale 0 → 1.08 → 1.0) |

**Reduced motion:** All animations respect `prefers-reduced-motion: reduce` — fade only, no translate/scale.

---

## 🧮 Math Rendering (IDMS Equations)

The IDMS dashboard optionally exposes the live math for curious students / mentors. Equations render using **KaTeX** (lightweight, no LaTeX server needed).

Example display in the IDMS panel (collapsed by default, expand toggle):

```
IntentDrift(Aᵢ, t) = D_KL( P^{H_t}_{Aᵢ} ‖ P^{H_0}_{Aᵢ} )

residual = ‖deviation‖ · max(0, trigger_alignment)

gate ∈ [0,1]:  σ( 1.5 · (alignment − 0.5) )
```

Rendered in a `#F5E6D3` panel, `JetBrains Mono`, with a `📐 Show the math` toggle in pink Poppins.

---

## 🏷️ Voice & Copy Rules

- **Labels describe what the user controls**, not how the system works internally. "Your thinking session" not "Orchestrator session."
- **Agent names are friendly**, not robotic. "Socratic" is fine — it's a word students know.
- **Error states are specific:** "This agent is re-anchoring — your message will send in a moment." Not "Error 503."
- **Empty states invite action:** "Nothing here yet — ask your first question below."
- **Drift banner is calm, not alarming:** "Recalibrating the session ✦" — not "DRIFT DETECTED."
- **Math toggle copy:** `📐 Show the math behind this` / `Hide math`

---

## 📦 Tech Notes for Implementation

| Concern | Recommendation |
|---|---|
| Component framework | React + Tailwind (extend config with Barbie palette tokens) |
| Animation | Framer Motion for layout/spring animations |
| Math | KaTeX (client-side, no server) |
| Agent web SVG | D3.js force simulation or custom RAF loop |
| Drift Ring | Canvas 2D API or SVG `stroke-dashoffset` animation |
| Fonts | Google Fonts: Playfair Display, Poppins, DM Sans + self-host JetBrains Mono |
| State | Zustand for session/drift state, React Query for agent message streaming |
| Streaming | SSE from FastAPI backend → streamed agent tokens render word by word |

---

*LearnFlow — Training Principles, Not Procedures.*
*Designed for the beach. Built for the exam hall.* 🌊🎀
