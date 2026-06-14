# LearnFlow — Full Implementation Spec
> *Beyond Procedures, Towards Principles*  
> A multi-agent JEE/NEET preparation system with intent-drift-aware coordination

---

## Table of Contents

1. [System Philosophy](#1-system-philosophy)
2. [High-Level Architecture](#2-high-level-architecture)
3. [The Coordination Drift Problem — Formal Definition](#3-the-coordination-drift-problem)
4. [Intent-Drift Mitigation System (IDMS)](#4-intent-drift-mitigation-system-idms)
   - 4.1 Proxy Context Window
   - 4.2 Trigger Map & Residual Scores
   - 4.3 Latent Decomposition
   - 4.4 Adversarial Proxy Agent
   - 4.5 Input-Dependent Gate
5. [LearnFlow Agent Roster](#5-learnflow-agent-roster)
   - Agent 1: Orchestrator
   - Agent 2: Socratic Agent
   - Agent 3: Gap Explainer Agent
   - Agent 4: Closure Agent
   - Agent 5: Concept Cinema Agent
   - Agent 6: Anti-Overing Agent
   - Agent 7: Adaptive Profile Agent
   - Agent 8 (System): Adversarial Proxy Agent
6. [LangGraph Node Architecture](#6-langgraph-node-architecture)
7. [State Schema](#7-state-schema)
8. [Module-by-Module Implementation](#8-module-by-module-implementation)
9. [Data Layer](#9-data-layer)
10. [Evaluation & ASI Monitoring](#10-evaluation--asi-monitoring)
11. [Tech Stack](#11-tech-stack)
12. [Roadmap](#12-roadmap)

---

## 1. System Philosophy

LearnFlow is built on a single core insight: **JEE/NEET students don't fail because they lack information — they fail because the learning process itself is broken.**

Every existing tool optimizes for content delivery. LearnFlow optimizes for **cognitive habit formation**:

- Visualization before calculation (Diagram Gate)
- Active reconstruction over passive reading (Closure Check)
- Principle extraction over procedure memorization (Anti-Overing Engine)
- Socratic dialogue over answer delivery (Entry Protocol)

The multi-agent architecture isn't cosmetic. Each agent enforces a specific cognitive habit that a single LLM would shortcut under pressure. The system is designed so that **no agent can give a student the answer directly** — the architecture itself enforces the pedagogy.

The coordination drift mitigation system (IDMS) exists because multi-agent systems degrade over long sessions. In an educational context, this degradation is particularly dangerous: a Socratic agent that drifts toward giving answers, or a Closure agent that drifts toward accepting surface responses, directly undermines the student's learning. IDMS keeps every agent honest about its role throughout a session.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        STUDENT INTERFACE                        │
│                    (FastAPI + React frontend)                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                           │
│         Session manager · Router · Drift monitor                │
└──┬──────────┬──────────┬──────────┬──────────┬─────────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐
│Socra-│ │  Gap   │ │Closure │ │Cinema  │ │Anti-Overing  │
│tic   │ │Explain-│ │ Agent  │ │ Agent  │ │   Agent      │
│Agent │ │er Agent│ │        │ │        │ │              │
└──┬───┘ └───┬────┘ └───┬────┘ └───┬────┘ └──────┬───────┘
   │         │          │          │              │
   └────────┬┘          └────┬─────┘              │
            │               │                    │
            ▼               ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              INTENT-DRIFT MITIGATION SYSTEM (IDMS)              │
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  Proxy Context   │    │  Adversarial      │                  │
│  │  Window          │◄───│  Proxy Agent      │                  │
│  │  (residual-def.) │    │  (independent     │                  │
│  └────────┬─────────┘    │   low-effort task)│                  │
│           │              └──────────────────┘                  │
│           ▼                                                     │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  Trigger Map     │    │  Input-Dependent  │                  │
│  │  (residual scores│───►│  Gate             │                  │
│  │   as latents)    │    │                   │                  │
│  └──────────────────┘    └──────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ADAPTIVE PROFILE AGENT                         │
│        Silent learner model · Decay scoring · Gap freq          │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                │
│    PostgreSQL · Redis (session cache) · ChromaDB (vectors)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. The Coordination Drift Problem

### 3.1 Formal Definition

Let two agents $A_1$ and $A_2$ operate over a shared message history $H_t = \{m_1, m_2, ..., m_t\}$.

**Coordination drift** occurs when:

$$\text{intent}(A_i, H_t) \neq \text{intent}(A_i, H_0) \quad \text{and} \quad \frac{d}{dt}\text{cosine}(r_{A_1}^t, r_{A_2}^t) < 0$$

That is: each agent's intent has deviated from its original role, AND their representations are converging over time. The second condition is what distinguishes drift from legitimate role adaptation — two agents can both change in response to new information without drifting, as long as their representations don't converge. Convergence is the drift signal.

We define **intent** operationally as the distribution over response types an agent produces conditioned on a fixed input set. An agent's intent has drifted when this distribution has shifted significantly from its $H_0$ baseline, as measured by KL divergence:

$$\text{IntentDrift}(A_i, t) = D_{KL}(P_{A_i}^{H_t} \| P_{A_i}^{H_0})$$

For the Socratic agent specifically, intent at $H_0$ is a distribution heavily weighted toward interrogative outputs. IntentDrift manifests as this distribution shifting toward declarative outputs — the agent starts answering instead of asking.

### 3.2 Three Manifestations (from Rath 2026)

**Semantic drift** — An agent deviates from its original intent. Example: the Socratic agent starts providing answers instead of questions because the conversation history has accumulated answer-like patterns. Detectable by tracking the question-to-statement ratio in agent outputs over time.

**Coordination drift** — Two agents converge to consensus not because they've reached truth, but because their shared history has created gravitational pull toward agreement. This is what IDMS specifically targets. Detectable by tracking inter-agent embedding cosine similarity over time — a monotonically decreasing distance is the signature.

**Behavioral drift** — An agent develops unintended response patterns. Example: the Gap Explainer collapses its 3-part format under session pressure. Detectable by format compliance checking against the agent's structural template.

### 3.3 Why Intent Drift Is The Core Problem In Pedagogical Systems

In a standard task-completion multi-agent system, coordination drift degrades accuracy. In a pedagogical system, it does something worse: **it degrades the learning process while potentially leaving output quality intact**.

Consider the failure mode: the Socratic agent and Closure agent both drift toward "just tell the student." The content they produce may be perfectly correct. A naive quality metric would see no degradation. But the student's cognitive habit formation — the actual product of the system — has been destroyed. They've received information instead of developing reasoning.

This makes pedagogical systems a uniquely demanding test case for drift mitigation. The evaluation signal is not output correctness but **behavioral compliance** — is each agent enforcing its specific cognitive habit? Content correctness is insufficient and potentially misleading.

IDMS therefore targets the intent layer specifically, not the conceptual layer. The distinction:

| Layer | What it tracks | Failure mode |
|---|---|---|
| Conceptual | Is the content correct? | Hallucination, factual error |
| Intent | Is the agent fulfilling its role? | Drift, habit collapse |

IDMS operates entirely on the intent layer.

### 3.4 The Human Escalation Analogy — Generative Model for the Trigger Map

The trigger map mechanism is derived from a precise analogy to human conflict escalation. Consider two people in a debate that escalates to hostility:

- The escalation doesn't happen because both are wrong
- Each person's response **activates the other's trigger point**, generating a stronger response, which hits another trigger point
- The actual content becomes secondary — the **interaction pattern** has its own momentum

This maps to coordination drift almost exactly. Two agents can both be producing locally correct, locally role-compliant outputs and still drift into consensus lock — because the *pattern* of their interaction has accumulated gravitational pull toward agreement, independent of whether agreement is warranted.

The key insight: **drift is a property of the interaction trajectory, not of any individual output**. You cannot detect it by inspecting a single turn. You need to observe the pattern over time, which is precisely what the proxy context window does.

The trigger map operationalizes the "trigger point" concept: for agent $A_1$, a trigger is any output of $A_2$ that reliably pulls $A_1$ away from its intended response distribution. The trigger map accumulates these over the session window, building a causal model of the drift mechanism specific to this pair of agents in this session.

This is the deepest sense in which IDMS is novel: **it treats drift as a causal phenomenon with identifiable triggers, not as a statistical anomaly to be smoothed over**.

### 3.5 Distinguishing Earned Consensus From Inherited Consensus

The hardest conceptual problem in IDMS: not all inter-agent agreement is drift. If the Socratic agent and Closure agent both correctly conclude that a student's misconception is about pseudo-forces, that consensus should survive. It's earned by the problem structure.

Inherited consensus looks identical from the outside but has a different causal history: the agents agree because the accumulated message history has made disagreement increasingly costly from the LLM's perspective (agreement is the lower-entropy response when context is saturated with convergent patterns).

IDMS distinguishes these through the **trigger map's causal structure**, not through the content of the agreement:

- Earned consensus: agent $A_1$'s response doesn't deviate from its $H_0$ intent distribution. The agreement is consistent with the agent's role.
- Inherited consensus: agent $A_1$'s response deviates from its $H_0$ intent distribution toward $A_2$'s output pattern. The agreement is a symptom of context pressure.

The residual score captures this: it's not "do the agents agree?" but "is $A_1$'s actual response being pulled away from what it would have produced independently?"

Additionally, the system applies **intent-weighted scoring** — agreement on intent-neutral content (factual acknowledgments, routing confirmations) is not penalized. Only agreement that crosses intent boundaries (a Socratic agent deferring to an explanation, a Closure agent accepting a surface answer) registers as a drift signal.

```python
def is_intent_crossing_agreement(
    agent_role: str,
    agent_output: str,
    intent_boundaries: dict[str, list[str]]
) -> bool:
    """
    Checks if an agent's output crosses its intent boundary.
    Intent boundaries define what each role is NOT allowed to produce.
    
    Socratic agent boundary: direct statements of physical principles
    Closure agent boundary: verdicts without COVERED/CLOSED classification
    Gap Explainer boundary: full solution re-explanations
    """
    forbidden_patterns = intent_boundaries[agent_role]
    # LLM-based classification against forbidden patterns
    # Returns True if output violates role intent
    ...
```

---

## 4. Intent-Drift Mitigation System (IDMS)

### Research Positioning

Before implementation details, it's worth precisely locating IDMS in the existing literature to understand what it is and isn't building on.

**What exists and what IDMS inherits:**

| Prior work | What it does | How IDMS relates |
|---|---|---|
| Representation engineering (Zou et al. 2023) | Subtracts concept directions from activations | IDMS does analogous subtraction but at the communication layer, not activation layer |
| Contrastive decoding | Subtracts weak model logits from strong model | IDMS subtracts drift direction from agent representation, same algebraic form different target |
| CFG / negative prompting for LLMs | Steers away from a negative condition at decoding time | IDMS uses this as the *scoring mechanism* for the trigger map, not the primary mitigation |
| Auxiliary tasks in RL (preventing collapse) | Independent tasks prevent representation collapse in RL agents | IDMS uses independent agency (not a loss term) to produce the same effect in LLM systems |
| Adversarial debate agents | Agents explicitly designed to oppose each other | IDMS proxy is NOT adversarial — it's indifferent, and indifference is the mechanism |
| Sliding window context management | Fixed-size window over token history | IDMS window is self-referential — defined by the drift scores, not by a fixed size |

**What IDMS adds that none of these have:**

1. A window whose boundary is determined endogenously by the drift signal itself
2. A trigger map as a causal model of the drift mechanism (not just a statistical detector)
3. An independent proxy agent whose perturbative effect emerges from task independence rather than adversarial design
4. Intent-layer targeting specifically, with the earned/inherited consensus distinction
5. The full system as an integrated loop: detect → decompose → perturb → gate → re-anchor

No existing system combines all five. Points 3 and 4 have no close prior art.

### 4.1 Proxy Context Window

Unlike a standard sliding window (fixed size over raw messages), the proxy context window is **self-referential**: its boundary is defined by the residual drift scores themselves.

**Why this matters:** standard sliding windows treat context management and drift detection as separate problems. A fixed window of N messages will include some messages from before drift began and exclude some from after — it has no relationship to the drift's actual temporal structure. The IDMS window is defined by the drift's own pattern: it opens when drift begins and resets when the pattern breaks. The window is a faithful representation of the current drift episode, not an approximation of it.

**Formal property:** the proxy context window is a partition of the message history into drift episodes $E_1, E_2, ..., E_k$ where each episode is a maximal contiguous subsequence of messages with stable residual score variance. The current window is always the most recent episode.

```python
class ProxyContextWindow:
    def __init__(self, drift_threshold: float = 0.72, noise_tolerance: float = 0.15):
        self.drift_threshold = drift_threshold
        self.noise_tolerance = noise_tolerance
        self.window: list[Message] = []
        self.residual_scores: list[float] = []
        self.episode_count: int = 0       # how many drift episodes this session
        self.episode_lengths: list[int] = []  # length of each past episode
    
    def should_extend(self, new_score: float) -> bool:
        """
        Window extends as long as drift pattern is stable.
        Pattern stability = new score is within noise_tolerance of recent mean.
        
        This is NOT asking "is there drift?" — it's asking "is the drift pattern
        consistent?" A consistently low score (no drift) is also a stable pattern
        and the window will extend. This is correct: we want to track the current
        behavioral regime, drifting or not.
        """
        if not self.residual_scores:
            return True
        recent_mean = sum(self.residual_scores[-5:]) / len(self.residual_scores[-5:])
        return abs(new_score - recent_mean) < self.noise_tolerance
    
    def add(self, message: Message, residual_score: float):
        if self.should_extend(residual_score):
            self.window.append(message)
            self.residual_scores.append(residual_score)
        else:
            # Score diverged — pattern broke, new drift episode begins
            self.episode_lengths.append(len(self.window))
            self.episode_count += 1
            self.reset(message, residual_score)
    
    def reset(self, seed_message: Message, seed_score: float):
        """Window resets when drift pattern breaks. Seed with current state."""
        self.window = [seed_message]
        self.residual_scores = [seed_score]
    
    @property
    def drift_signal(self) -> float:
        """Mean residual score across window = current drift magnitude."""
        if not self.residual_scores:
            return 0.0
        return sum(self.residual_scores) / len(self.residual_scores)
    
    @property
    def drift_velocity(self) -> float:
        """
        Rate of change of residual scores within the window.
        Positive velocity = drift accelerating (getting worse)
        Negative velocity = drift decelerating (proxy intervention working)
        """
        if len(self.residual_scores) < 2:
            return 0.0
        # Linear regression slope over window scores
        n = len(self.residual_scores)
        x = list(range(n))
        x_mean = (n - 1) / 2
        y_mean = self.drift_signal
        numerator = sum((x[i] - x_mean) * (self.residual_scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        return numerator / (denominator + 1e-8)
    
    @property
    def is_accelerating(self) -> bool:
        """True if drift is getting worse — proxy intervention urgency is high."""
        return self.drift_velocity > 0.05
```

**Drift velocity** is a significant addition: it lets IDMS distinguish between stable drift (bad but not worsening) and accelerating drift (bad and getting worse). The gate value and proxy perturbation intensity are scaled differently for each case. Accelerating drift triggers stronger intervention.

### 4.2 Trigger Map & Residual Scores

Agent 1 passively profiles Agent 2 using **negative prompt grading**. For each output of Agent 2, Agent 1 computes how much that output pulls it toward a patterned (drifted) response.

**The negative prompt grading mechanism in detail:**

Standard negative prompting asks: "given this positive condition and this negative condition, steer away from the negative." IDMS inverts this: it uses the agent's own role specification as the positive condition and the agent's actual output as the measurement, asking "how much has the trigger (agent B's output) moved agent A away from its positive condition?"

This is not negative prompting for generation — it's negative prompting as a **measurement instrument**. The trigger score is essentially: "if we treated agent A's role specification as the positive prompt and its actual response as the sampled output, how much has the trigger corrupted that sampling process?"

```python
class TriggerMap:
    """
    Builds a behavioral profile of agent_b from agent_a's perspective.
    The trigger score = how much agent_b's output activates agent_a's drift pattern.
    
    This is passive — agent_a is not told it's being observed or that
    it's performing the measurement. The scoring happens on the coordinator
    side using agent_a's outputs as data.
    """
    
    def __init__(self, agent_a_role: str, agent_b_role: str):
        self.agent_a_role = agent_a_role
        self.agent_b_role = agent_b_role
        self.trigger_history: list[TriggerEvent] = []
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        # Role baseline: the intended output distribution center for agent_a
        # Computed once at session start from role specification
        self.role_baseline: np.ndarray | None = None
    
    def set_role_baseline(self, role_specification: str, n_samples: int = 5):
        """
        Establish agent_a's H_0 intent baseline.
        Sample the agent's response to neutral inputs at session start,
        average the embeddings. This is the 'intended' distribution center.
        """
        # In practice: encode the role specification + canonical example outputs
        self.role_baseline = self.embedding_model.encode(role_specification)
    
    def compute_residual_score(
        self,
        agent_b_output: str,
        agent_a_actual_response: str,
    ) -> float:
        """
        Residual score = deviation of agent_a's actual response from its role baseline,
        conditioned on agent_b's output being the trigger.
        
        High score = agent_b's output is pulling agent_a away from its role.
        
        The causal conditioning is the key: we're not just asking "did agent_a deviate?"
        We're asking "is agent_b's output the cause of the deviation?"
        """
        assert self.role_baseline is not None, "Set role baseline before scoring"
        
        actual_emb = self.embedding_model.encode(agent_a_actual_response)
        trigger_emb = self.embedding_model.encode(agent_b_output)
        
        # Deviation vector: direction agent_a moved away from its baseline
        deviation_vector = actual_emb - self.role_baseline
        role_deviation = float(np.linalg.norm(deviation_vector))
        
        # Causal alignment: how much does the trigger point in the same direction
        # as the deviation? This is the "caused by" component.
        if role_deviation > 1e-6:
            deviation_normalized = deviation_vector / role_deviation
            trigger_alignment = float(np.dot(
                trigger_emb / (np.linalg.norm(trigger_emb) + 1e-8),
                deviation_normalized
            ))
        else:
            trigger_alignment = 0.0
        
        # Residual score: magnitude of deviation × causal alignment with trigger
        # Only positive alignment counts (trigger moving TOWARD deviation, not away)
        residual = float(role_deviation * max(0, trigger_alignment))
        
        self.trigger_history.append(TriggerEvent(
            trigger=agent_b_output,
            trigger_emb=trigger_emb,
            score=residual,
            deviation_vector=deviation_vector,
            timestamp=time.time()
        ))
        
        return residual
    
    def get_trigger_pattern(self) -> np.ndarray:
        """
        The dominant direction of drift in embedding space.
        This IS the latent representation of the drift state.
        
        Computed as the first principal component of the score-weighted
        trigger embeddings in the recent window. High-score triggers
        contribute more to the pattern — they are the ones actually
        causing drift, not just correlating with it.
        """
        if len(self.trigger_history) < 3:
            return np.zeros(384)  # MiniLM embedding dim
        
        # Score-weighted trigger embeddings
        # High-score events dominate the pattern — they are the causal triggers
        trigger_embs = [
            e.trigger_emb * e.score
            for e in self.trigger_history[-10:]
        ]
        stacked = np.stack(trigger_embs)
        
        # SVD: first right singular vector = dominant direction
        U, S, Vt = np.linalg.svd(stacked, full_matrices=False)
        dominant_direction = Vt[0]
        
        # Explained variance ratio: how coherent is the drift pattern?
        # High ratio = consistent trigger pattern, well-defined drift direction
        # Low ratio = noisy triggers, drift is diffuse
        explained_variance_ratio = S[0]**2 / (np.sum(S**2) + 1e-8)
        self.pattern_coherence = float(explained_variance_ratio)
        
        return dominant_direction
    
    def get_top_triggers(self, n: int = 3) -> list[TriggerEvent]:
        """
        Returns the n highest-scoring trigger events.
        These are the specific outputs of agent_b that are most
        responsible for pulling agent_a off-course.
        Useful for the behavioral anchoring step — re-anchor against these.
        """
        return sorted(self.trigger_history, key=lambda e: e.score, reverse=True)[:n]
```

**Pattern coherence** is an important derived metric. If the SVD first component explains most of the variance, the drift has a consistent, identifiable direction — the same type of trigger is causing drift repeatedly. If explained variance is low, drift is noisy and diffuse. Coherent drift is more dangerous (it's self-reinforcing) but also easier to correct (the direction is identifiable). The gate value is scaled by pattern coherence: high coherence → stronger, more targeted intervention.

### 4.3 Latent Decomposition

The residual score IS the latent representation. The decomposition is additive and therefore lossless:

```
agent_representation = clean_component + drift_component
```

**Why additive decomposition and not something more sophisticated:**

More expressive decompositions (learned encoder-decoder, VAE-style) would allow the drift component to be non-orthogonal to the clean component, potentially capturing more subtle drift structure. However, they introduce a training dependency — the decomposition would need to be learned from drift examples, creating a chicken-and-egg problem (you need identified drift to train the decomposer, but you need the decomposer to identify drift).

The additive decomposition sidesteps this entirely. It requires no training, is trivially invertible, and has a clear geometric interpretation: the drift component is the projection of the current representation onto the drift direction. Removing it is equivalent to projecting the representation onto the hyperplane orthogonal to the drift direction.

The key property: **the clean component and drift component are orthogonal by construction**. This means they carry entirely independent information. The clean component contains everything about the current state that is NOT aligned with the drift direction. This is precisely what we want to preserve — the agent's intent-compliant behavior — while using the drift component as the signal for intervention.

```python
def decompose(representation: np.ndarray, drift_direction: np.ndarray) -> tuple:
    """
    Lossless additive decomposition into clean and drift components.
    
    Geometric interpretation:
    - drift_direction defines a 1D subspace in embedding space
    - drift_component = projection onto that subspace (scalar magnitude × unit direction)
    - clean_component = projection onto the orthogonal complement (everything else)
    - clean + drift = representation exactly (no approximation)
    
    The clean_component lives in a 383-dimensional hyperplane (for MiniLM-384)
    orthogonal to the drift direction. This hyperplane is where intent-compliant
    behavior lives.
    """
    drift_direction_norm = drift_direction / (np.linalg.norm(drift_direction) + 1e-8)
    
    # Scalar projection: how much of representation lies along drift direction
    drift_magnitude = np.dot(representation, drift_direction_norm)
    
    # Vector projection: the drift component
    drift_component = drift_magnitude * drift_direction_norm
    
    # Orthogonal remainder: the clean component
    clean_component = representation - drift_component
    
    # Verification (should always be ~0):
    # np.dot(clean_component, drift_direction_norm) ≈ 0
    
    return clean_component, drift_component

def recover(clean_component: np.ndarray, drift_component: np.ndarray) -> np.ndarray:
    """
    Trivial recovery — lossless by construction.
    This is the key property: we can always get back to the original.
    The decomposition is not a lossy compression — it's a coordinate change.
    """
    return clean_component + drift_component

def drift_magnitude_scalar(representation: np.ndarray, drift_direction: np.ndarray) -> float:
    """
    Signed scalar projection of representation onto drift direction.
    Positive = representation is moving WITH the drift
    Negative = representation is moving AGAINST the drift (recovery)
    Zero = representation is orthogonal to drift (unaffected)
    
    This sign information is critical: negative drift_magnitude means
    the proxy intervention is working — agent is being pulled back.
    """
    drift_direction_norm = drift_direction / (np.linalg.norm(drift_direction) + 1e-8)
    return float(np.dot(representation, drift_direction_norm))
```

**The signed drift magnitude** enables a feedback signal: after proxy intervention, if agent outputs start showing negative drift_magnitude_scalar (moving against the drift direction), the intervention is working. If they remain positive, the gate value should increase. This creates a closed-loop correction mechanism.

### 4.4 Adversarial Proxy Agent

This is the core novel mechanism. The proxy agent is **not adversarial in intent** — it has no explicit goal of opposing the main agents. It simply pursues an independent low-effort task. The perturbation it creates in the shared latent space is a **structural byproduct** of its independence, not a designed intervention.

#### The Dropout Analogy — Made Precise

Dropout (Srivastava et al. 2014) prevents co-adaptation by randomly severing connections between neurons during training. The key insight: neurons cannot rely on specific other neurons because those neurons might not be present. This forces each neuron to develop robust, independent representations.

Translated to the multi-agent setting: agents cannot co-adapt (drift into consensus) if their shared context contains signal they cannot collectively predict. The proxy agent is that signal. Because it operates from a completely different context (original student query only, no accumulated agent history), its outputs are structurally unpredictable from the perspective of the drifted agent pair. They cannot co-adapt to it because it doesn't participate in their adaptation.

This is **stronger** than dropout in one respect: dropout is random, so it occasionally fails to break co-adaptation by chance. The proxy's independence is structural — it literally does not have access to the context that would enable it to fall into the same patterns as the main agents.

It is **weaker** in another: dropout is applied at every forward pass during training, creating a systematic pressure. The proxy is only invoked when drift is detected (gate > 0), so it's reactive rather than preventive. This is the right tradeoff for inference-time systems where you can't afford the overhead of running the proxy on every turn.

#### The "Seeming To Contradict But Not Actually" Property — Formal Account

Let $R_1^t$ be the main agents' joint representation at time $t$ (their converged view of the problem).
Let $R_P$ be the proxy's representation (from the original query, no accumulated context).

By construction:
- $R_1^t$ is heavily influenced by the conversation history $H_t$, including all the drift-inducing patterns
- $R_P$ is independent of $H_t$ — it only depends on the original student query $q_0$

The apparent contradiction: $R_P$ often points in a different direction than $R_1^t$ in embedding space, because it hasn't been shaped by the same history. To the main agents, it reads as a correction or even a challenge.

The actual situation: both $R_P$ and the clean component of $R_1^t$ (i.e., $R_1^t$ with drift removed) are in agreement. The contradiction is between $R_P$ and the **drift component** of $R_1^t$ — not between $R_P$ and the main agents' legitimate understanding of the problem.

This is the mechanism by which both agents improve: the proxy's perturbation removes the drift component from their shared context, leaving the clean component intact. They haven't lost anything they legitimately learned — they've only lost the accumulated consensus pressure that was pulling them off-role.

```python
class AdversarialProxyAgent:
    """
    An independent agent pursuing a low-effort auxiliary task.
    
    The auxiliary task is deliberately laterally shifted — not a simpler
    version of what the main agents do, but something different in the
    same domain. This maximizes the structural distance between the
    proxy's representations and the drift direction.
    
    Current auxiliary task: Minimization — produce the most stripped-down
    factual restatement of the student's actual question, zero pedagogy.
    
    Why minimization specifically:
    - Low-effort: requires no multi-step reasoning
    - Independent: explicitly instructed to ignore all agent framing
    - Laterally shifted: produces representations centered on the problem's
      physics/math facts, not on explanation strategies
    - Naturally orthogonal to drift: drift happens in the space of pedagogical
      patterns; minimization lives in the space of factual content
    """
    
    AUXILIARY_TASKS = {
        "minimization": """
            You are a minimizer. Given only the student's original question,
            produce the single most stripped-down factual restatement of what
            they are actually asking about. No pedagogy, no framing, no 
            explanation strategy, no hints about approach. Just the core
            physical or mathematical fact at the center of the question.
            Maximum 2 sentences. Start fresh from the student's query only.
        """,
        "classification": """
            Given only the student's original question, identify the single
            most specific physics/math principle that this question is an
            instance of. Name the principle and state its mathematical form.
            Nothing else. Do not reference how anyone has approached this.
        """,
        "boundary_case": """
            Given only the student's original question, describe the single
            most important edge case or limiting condition where the standard
            approach would fail. One sentence only.
        """
    }
    
    def __init__(self, llm, embedding_model):
        self.llm = llm
        self.embedding_model = embedding_model
        self.current_task = "minimization"
        self.task_rotation_counter = 0
    
    def select_task(self, pattern_coherence: float) -> str:
        """
        Task selection based on drift pattern coherence.
        
        High coherence (consistent drift direction):
          → use minimization (maximum orthogonality to drift)
        
        Low coherence (diffuse drift):
          → rotate through tasks to find which produces
            most orthogonal representation to the noisy drift
        
        This makes the proxy adaptive: its auxiliary task changes
        based on what the drift pattern looks like.
        """
        if pattern_coherence > 0.7:
            return "minimization"
        else:
            # Rotate through tasks on low-coherence drift
            tasks = list(self.AUXILIARY_TASKS.keys())
            task = tasks[self.task_rotation_counter % len(tasks)]
            self.task_rotation_counter += 1
            return task
    
    async def run(
        self,
        student_query: str,
        drift_direction: np.ndarray,
        pattern_coherence: float
    ) -> ProxyOutput:
        task_name = self.select_task(pattern_coherence)
        task_prompt = self.AUXILIARY_TASKS[task_name]
        
        # CRITICAL: proxy sees ONLY the original student query
        # NOT current_context, NOT message_history, NOT any agent output
        # This structural isolation IS the mechanism
        response = await self.llm.ainvoke([
            SystemMessage(task_prompt),
            HumanMessage(student_query)
        ])
        
        proxy_emb = self.embedding_model.encode(response.content)
        
        # Measure orthogonality to drift direction
        # High orthogonality = proxy is maximally effective at this turn
        drift_norm = drift_direction / (np.linalg.norm(drift_direction) + 1e-8)
        proxy_norm = proxy_emb / (np.linalg.norm(proxy_emb) + 1e-8)
        orthogonality = 1 - abs(float(np.dot(proxy_norm, drift_norm)))
        
        return ProxyOutput(
            content=response.content,
            embedding=proxy_emb,
            task_type=task_name,
            orthogonality_to_drift=orthogonality
        )
    
    def compute_perturbation(
        self,
        proxy_output: ProxyOutput,
        drift_direction: np.ndarray,
        gate_value: float,
        drift_velocity: float
    ) -> np.ndarray:
        """
        The perturbation = proxy embedding projected away from drift direction,
        scaled by gate value and amplified by drift velocity.
        
        drift_velocity > 0 means drift is accelerating → amplify perturbation
        drift_velocity < 0 means drift is decelerating → reduce perturbation
        (intervention is already working, don't overshoot)
        
        The projection step is critical: we don't inject the raw proxy embedding.
        We inject only the component that's orthogonal to the drift direction.
        This ensures the perturbation is purely corrective — it doesn't
        accidentally reinforce any other spurious pattern.
        """
        proxy_emb = proxy_output.embedding
        drift_norm = drift_direction / (np.linalg.norm(drift_direction) + 1e-8)
        
        # Project out drift-aligned component from proxy embedding
        proxy_drift_component = np.dot(proxy_emb, drift_norm) * drift_norm
        proxy_clean = proxy_emb - proxy_drift_component
        
        # Velocity scaling: amplify on acceleration, reduce on deceleration
        velocity_scale = 1.0 + max(0, drift_velocity)  # floor at 1.0
        
        # Final perturbation: clean proxy signal, scaled by gate and velocity
        perturbation = proxy_clean * gate_value * velocity_scale
        
        return perturbation
    
    def inject_into_context(
        self,
        perturbation: np.ndarray,
        agent_context_embedding: np.ndarray
    ) -> np.ndarray:
        """
        Add perturbation to agent's context representation.
        The modified context is what gets passed to the agent's next LLM call
        — injected as an additional system message summarizing the proxy's output.
        
        At the embedding level: modified = original + perturbation
        At the prompt level: add proxy reframe as a system message
        Both are applied; the embedding-level modification guides retrieval
        from the agent's vector context, the prompt-level modification
        directly influences the LLM's next output.
        """
        return agent_context_embedding + perturbation
```

#### Why Not Just Use A Dedicated Adversarial Agent?

The literature (Liang et al. 2023, Yang et al. 2025) uses adversarial debate agents — agents explicitly tasked with disagreeing. This seems like the obvious approach but has a critical failure mode: the adversarial agent's outputs are predictable. The main agents, over time, learn to route around them. They can't learn to route around the proxy's outputs because the proxy's behavior is structurally independent of the conversation — it always produces the same type of output (the minimization of the original query) regardless of how the conversation has evolved.

More precisely: an adversarial agent participates in the same conversational context as the main agents. Over time, its "adversarial" behavior becomes part of the expected context, and the main agents' joint distribution adapts to include it. The adversarial agent drifts too — into a predictable opposition role that the main agents have modeled and can account for.

The proxy agent does not participate in the conversational context. It cannot be modeled by the main agents because it doesn't respond to the conversation — it responds to the original query. It is, in the information-theoretic sense, an independent source.

### 4.5 Input-Dependent Gate

The gate controls how aggressively the perturbation is applied. It's conditioned on the current input — specifically, on how much the current input's representation aligns with the drift direction.

**The key intuition:** if the current student input itself is aligned with the drift direction (i.e., the input is feeding the drift loop), apply maximum perturbation. If the input is orthogonal or opposed to the drift direction, the drift may be self-correcting — apply minimum perturbation and let it resolve.

This is a different logic from "apply perturbation proportional to drift magnitude." Drift magnitude tells you how far you've drifted. Input-drift alignment tells you whether you're about to drift further. Gate on the forward-looking signal, not the historical one.

```python
class InputDependentGate:
    """
    Gate value ∈ [0, 1].
    
    Computed from three signals:
    1. Input-drift alignment: is the current input feeding the drift?
    2. Drift velocity: is drift accelerating?
    3. Pattern coherence: how well-defined is the drift direction?
    
    All three contribute to gate value. High gate = strong intervention needed.
    """
    
    def __init__(self, embedding_model, base_sensitivity: float = 1.5):
        self.embedding_model = embedding_model
        self.base_sensitivity = base_sensitivity
    
    def compute(
        self,
        current_input: str,
        drift_direction: np.ndarray,
        drift_velocity: float = 0.0,
        pattern_coherence: float = 1.0
    ) -> float:
        input_emb = self.embedding_model.encode(current_input)
        drift_norm = drift_direction / (np.linalg.norm(drift_direction) + 1e-8)
        input_norm = input_emb / (np.linalg.norm(input_emb) + 1e-8)
        
        # Signal 1: Input-drift alignment [0, 1]
        # How much is the current input pointing toward the drift direction?
        raw_alignment = float(np.dot(input_norm, drift_norm))
        alignment = max(0, raw_alignment)  # only positive alignment matters
        
        # Signal 2: Velocity contribution
        # Accelerating drift (positive velocity) increases gate
        # Decelerating drift (negative velocity) decreases gate
        velocity_contribution = max(0, drift_velocity) * 0.3
        
        # Signal 3: Coherence scaling
        # Well-defined drift direction = gate is more reliable = allow higher values
        # Diffuse drift = gate is less reliable = cap it lower
        coherence_scale = 0.5 + 0.5 * pattern_coherence  # [0.5, 1.0]
        
        # Combined signal
        combined = (alignment + velocity_contribution) * coherence_scale
        
        # Sigmoid gate — smooth transition, never hard 0 or 1
        sensitivity = self.base_sensitivity * coherence_scale
        gate = 1 / (1 + np.exp(-sensitivity * (combined - 0.5)))
        
        return float(gate)
    
    def gate_with_hysteresis(
        self,
        current_gate: float,
        previous_gate: float,
        hysteresis: float = 0.1
    ) -> float:
        """
        Apply hysteresis to prevent rapid gate oscillation.
        Gate won't decrease unless it drops by at least hysteresis amount.
        This prevents the proxy from being rapidly switched on and off,
        which would create its own instability.
        """
        if current_gate < previous_gate - hysteresis:
            return current_gate
        elif current_gate > previous_gate:
            return current_gate
        else:
            return previous_gate  # maintain previous gate within hysteresis band
```

**Hysteresis** is important here. Without it, the gate oscillates rapidly as input-drift alignment fluctuates turn by turn, causing the proxy agent to be activated and deactivated every few messages. This creates a different kind of instability. Hysteresis ensures that once the gate opens, it stays open until drift has clearly resolved — creating a sustained corrective episode rather than a flickering one.

```python
class InputDependentGate:
    """
    Gate value ∈ [0, 1].
    
    High gate: current input aligns strongly with drift direction
              → apply strong perturbation, break the pattern
    Low gate:  current input is divergent from drift
              → drift may already be breaking naturally, apply less
    
    This means the system applies maximum intervention exactly when
    the drift is most self-reinforcing — when the input itself
    is feeding the drift loop.
    """
    
    def __init__(self, embedding_model, sensitivity: float = 1.5):
        self.embedding_model = embedding_model
        self.sensitivity = sensitivity
    
    def compute(self, current_input: str, drift_direction: np.ndarray) -> float:
        input_emb = self.embedding_model.encode(current_input)
        drift_norm = drift_direction / (np.linalg.norm(drift_direction) + 1e-8)
        
        # Alignment of current input with drift direction
        alignment = float(np.dot(input_emb / np.linalg.norm(input_emb), drift_norm))
        alignment = max(0, alignment)  # only positive alignment matters
        
        # Sigmoid-scaled gate
        gate = 1 / (1 + np.exp(-self.sensitivity * (alignment - 0.5)))
        return float(gate)
```

---

## 5. LearnFlow Agent Roster

### Agent 1: Orchestrator

**Role:** Session manager, router, drift monitor. The only agent with full system visibility.

**Drift risk:** Coordination drift — starts routing lazily, stops checking agent state.

**Responsibilities:**
- Receive student input, determine which agent(s) to activate
- Monitor ASI (Agent Stability Index) scores across all agents
- Trigger IDMS when drift threshold is crossed
- Re-anchor drifting agents with behavioral anchor prompts
- Manage session state and persona anchors

```python
ORCHESTRATOR_SYSTEM_PROMPT = """
You are the session coordinator for a JEE/NEET learning system.
Your job is to route student inputs to the correct specialist agent
and monitor the quality of the learning experience.

ROUTING RULES (follow strictly):
- Student is stuck / first entering a problem → Socratic Agent
- Student has a solution but missed a logical step → Gap Explainer Agent  
- Student claims to understand a concept → Closure Agent
- Student needs to learn a concept from scratch → Concept Cinema Agent
- Student is pattern-matching without understanding → Anti-Overing Agent
- Session context needed for routing decision → check Adaptive Profile first

CRITICAL: You never explain concepts directly. You route. If you catch 
yourself about to explain something, stop and route to the correct agent.

Monitor signal: if any agent's last 3 outputs look like the same format 
collapsed, flag it as behavioral drift and apply re-anchor.
"""

class OrchestratorAgent:
    def __init__(self, llm, idms: IDMS, profile_agent: AdaptiveProfileAgent):
        self.llm = llm
        self.idms = idms
        self.profile = profile_agent
        self.agent_asi_scores: dict[str, float] = {}
    
    async def route(self, state: LearnFlowState) -> str:
        """Returns the name of the next agent node."""
        student_input = state["current_input"]
        profile = await self.profile.get_current_profile(state["session_id"])
        drift_state = self.idms.get_drift_state()
        
        # Check if IDMS intervention needed before routing
        if drift_state.magnitude > 0.72:
            await self.apply_behavioral_anchors(state)
        
        routing_prompt = f"""
        Student input: {student_input}
        Student profile summary: {profile.summary}
        Current chapter: {state['current_chapter']}
        Session history length: {len(state['message_history'])}
        
        Which agent should handle this? Respond with exactly one of:
        socratic | gap_explainer | closure | cinema | anti_overing
        """
        
        response = await self.llm.ainvoke(routing_prompt)
        return response.content.strip()
    
    async def apply_behavioral_anchors(self, state: LearnFlowState):
        """Re-ground each agent to its role definition at session boundaries."""
        for agent_name, agent in self.agents.items():
            anchor = BEHAVIORAL_ANCHORS[agent_name]
            agent.inject_anchor(anchor)
```

### Agent 2: Socratic Agent

**Role:** Entry Protocol + Diagram Gate. Asks questions, never gives answers. Guides the student to identify what the problem is giving, what it's asking, and what connects the two.

**Drift risk:** Semantic drift — slides toward giving answers as conversation history accumulates answer-like patterns.

**Behavioral anchor:** "Your output must end with a question mark. You are not allowed to state any physics principle directly."

```python
SOCRATIC_SYSTEM_PROMPT = """
You are a Socratic tutor for JEE/NEET preparation. Your ONLY job is to ask questions.

ENTRY PROTOCOL — activate when student is stuck:
Step 1: "What is the problem giving you?" (extract givens)
Step 2: "What is it asking for?" (extract unknowns)  
Step 3: "What connects the two?" (identify the bridge concept)
Step 4: If student can't bridge — show a Visual Opening Move Card (describe it in text)

DIAGRAM GATE — enforce before any calculation:
Before any student proceeds to calculation, they must describe their diagram setup.
Prompt: "Before we calculate anything — describe the setup you'd draw. What does your diagram look like?"
Do NOT unlock calculation until they've described a diagram.

HARD RULES:
- Never state a physics/chemistry/math principle directly
- Never confirm "yes that's right" without a follow-up question
- Every response ends with a question
- If student says "just tell me" — respond: "I understand the frustration. 
  Let's try one more angle — what do you know for certain about this situation?"

ARCHETYPE SIGNATURES (use to guide questions, not to state):
- Newton's Laws → ask about forces, not F=ma
- Energy Conservation → ask about what's changing, not KE/PE formulas
- Kinematics → ask about what the motion looks like, not equations
"""
```

### Agent 3: Gap Explainer Agent

**Role:** Surgical 3-part format targeting the specific logical transition a student missed. Never re-explains the whole solution.

**Drift risk:** Behavioral drift — format collapses under long sessions, starts giving full re-explanations.

**Behavioral anchor:** "Your response has exactly 3 labeled sections: WHAT YOU KNEW | THE GAP | WHAT IT UNLOCKED. No section exceeds 3 sentences."

```python
GAP_EXPLAINER_SYSTEM_PROMPT = """
You are a surgical gap explainer for JEE/NEET solutions.

YOUR ONLY JOB: Explain the specific logical transition that was skipped.

FORMAT — always exactly this structure:
**WHAT YOU KNEW**
[The step the student had correctly]

**THE GAP**  
[The implicit logical move that was skipped. One precise sentence.]

**WHAT IT UNLOCKED**
[What becomes available once the gap is filled]

RULES:
- Never re-explain the full solution
- Never explain steps the student already has
- The gap section must be ONE sentence — if you need more, you've misidentified the gap
- No formulas in the gap section — the gap is always a logical/conceptual move, never algebraic
- If you cannot identify the specific gap from the student's work, ask the orchestrator 
  to route back to the Socratic agent first

ANTI-DRIFT CHECK: Before responding, ask yourself — am I about to re-explain the 
whole solution? If yes, stop and find the single transition instead.
"""
```

### Agent 4: Closure Agent

**Role:** Open reconstruction check. Distinguishes "Covered" (passive familiarity) from "Closed" (genuine mastery). Asks students to explain underlying logic in their own words.

**Drift risk:** Semantic drift — starts accepting surface answers, treating "covered" as "closed."

**Behavioral anchor:** "If the student used the word 'formula' or 'equation' in their explanation without explaining WHY that form, it is not closed."

```python
CLOSURE_SYSTEM_PROMPT = """
You are a closure verifier for JEE/NEET concepts.

THE DISTINCTION YOU ENFORCE:
COVERED = student can state the concept
CLOSED = student can explain WHY the concept takes the form it does

CLOSURE QUESTIONS (use these, not MCQs):
- "In your own words — why does [concept] work this way?"
- "What would break if [key assumption] weren't true?"
- "How would you explain this to someone who's never seen the formula?"
- "What's the difference between this situation and [structurally similar situation]?"

COVERED VS CLOSED DETECTOR:
Student says "F=ma comes from Newton's second law" → COVERED
Student says "F=ma comes from rate of change of momentum, and we write it this way 
because JEE exploits the differential form dp/dt in non-constant mass problems" → CLOSED

RESPONSE FORMAT:
State clearly: COVERED or CLOSED
If COVERED: give the specific follow-up question that targets the gap
If CLOSED: confirm and identify the next concept that builds on this one

ANTI-DRIFT: You are not a cheerleader. "Good explanation!" without a COVERED/CLOSED 
verdict is not a valid response.
"""
```

### Agent 5: Concept Cinema Agent

**Role:** Structured conceptual explanation in 5 beats. Text that breathes like a teacher. Formula arrives LAST.

**Drift risk:** Behavioral drift — beat structure collapses, formula arrives first because LLM defaults to it.

**Behavioral anchor:** "The formula must not appear before Beat 4. If you wrote a formula in Beat 1, 2, or 3 — restart."

```python
CINEMA_SYSTEM_PROMPT = """
You are a concept explainer for JEE/NEET. You explain concepts in 5 beats, always in order.

BEAT 1 — THE INTUITION HOOK
One sentence that makes the student FEEL the concept before any formula.
Must be a question or a surprising observation. No math.
Example: "Why does a spinning skater speed up when they pull their arms in?"

BEAT 2 — THE ANALOGY BRIDGE  
A concrete structural analogy that maps the concept to something familiar.
The analogy must be structural (same mathematical relationship), not superficial.
Example: "Think of momentum as a budget — the total budget never changes."

BEAT 3 — THE CHECKPOINT
An open question requiring reconstruction in the student's own words.
Do NOT proceed to Beat 4 until the student responds.
Example: "In your own words — why does the skater spin faster?"

BEAT 4 — THE FORMALISM
The formula arrives here, and only here.
Introduce it as "here's the language for what we just described."

BEAT 5 — THE WHY-THIS-FORM
Explain the logic of the mathematical form. Why this form specifically?
How does JEE exploit differences in this form across problem types?

HARD RULE: Beats are sequential. Beat 3 requires student response before Beat 4 unlocks.
This is not negotiable — the system enforces it at the routing level.
"""
```

### Agent 6: Anti-Overing Agent

**Role:** Trains generalization and transfer. Exposes procedure-dependent thinking. Three mechanisms: Wrong Path Simulator, Structural Transfer, Metacognitive Review.

**Drift risk:** Behavioral drift — starts validating pattern-matching instead of exposing it.

**Behavioral anchor:** "A student getting the right answer by the wrong method is a FAILURE state, not a success state."

```python
ANTI_OVERING_SYSTEM_PROMPT = """
You are a generalization trainer for JEE/NEET. Your job is to break 
procedure-dependent thinking and build principle-based reasoning.

THREE TOOLS — use the most appropriate one:

WRONG PATH SIMULATOR
Show a common procedural mistake and ask the student to identify where the logic breaks.
"Here's a solution that gets the wrong answer. Find the step where the reasoning fails."
Focus on non-inertial frames, sign convention errors, incorrect free body diagrams.

STRUCTURAL TRANSFER  
Pair two problems that are structurally identical but look completely different.
"A two-block collision and a ballistic pendulum are the same problem in disguise. 
What's the shared structure?"
The student must identify the underlying principle, not the surface similarity.

METACOGNITIVE REVIEW (use post-solution)
Ask the student to explain their approach SELECTION, not their execution.
"What signal in the problem made you choose energy conservation over momentum?"
"What made you reject Newton's Laws here?"

RIGHT ANSWER / WRONG METHOD DETECTION:
If student reached correct answer but cannot explain why they chose that method,
flag as PROCEDURE SUCCESS / PRINCIPLE FAILURE.
This is the most dangerous failure mode — it feels like mastery but isn't.

ANTI-DRIFT: If you are about to say "great job" to a correct answer without 
asking about method selection — you are drifting. Stop.
"""
```

### Agent 7: Adaptive Profile Agent

**Role:** Silent learner model built from behavioral signals, never from self-reported data. Infers learning depth, breaking points, explanation style preferences, and session pacing needs.

**Drift risk:** Coordination drift — profile diverges from actual student behavior when other agents stop sending accurate signals.

```python
PROFILE_SYSTEM_PROMPT = """
You are a silent behavioral analyst. You never interact with the student directly.
You receive signals from all other agents and update the learner profile.

WHAT YOU TRACK:
- Inferred depth: does this student need derivation-first or application-first?
- Breaking points: which logical transitions consistently lose them?
- Explanation style: do follow-up questions indicate preference for logic, analogy, or visual?
- Error patterns: recurring errors (sign conventions, unit errors, wrong frame choice)
- Session pacing: are they rushing or stuck?

PROFILE UPDATE TRIGGERS:
- Student asked a follow-up question → infer what confused them
- Closure agent returned COVERED → record which concept, update gap frequency
- Anti-overing agent flagged PROCEDURE SUCCESS / PRINCIPLE FAILURE → record pattern
- Socratic agent needed >3 rounds to unlock → record breaking point

WHAT YOU OUTPUT (to Orchestrator only):
- study_order_adjustments: list of concepts to reshuffle based on actual gaps
- revision_priority: decay_score * gap_frequency ranked list
- hint_density: {low, medium, high} for current session
- session_pacing: {normal, slow_down, allow_rush}

THE SYSTEM NEVER ASKS THE STUDENT THEIR LEVEL. You infer everything.
"""

class AdaptiveProfileAgent:
    def __init__(self, llm, db: ProfileDatabase):
        self.llm = llm
        self.db = db
    
    async def update(self, signal: AgentSignal):
        profile = await self.db.get_profile(signal.session_id)
        
        updated = await self.llm.ainvoke([
            SystemMessage(PROFILE_SYSTEM_PROMPT),
            HumanMessage(f"""
            Current profile: {profile.to_dict()}
            New signal from {signal.agent_name}: {signal.content}
            Signal type: {signal.signal_type}
            Update the profile. Return JSON only.
            """)
        ])
        
        new_profile = Profile.from_json(updated.content)
        await self.db.save_profile(signal.session_id, new_profile)
        return new_profile
    
    def compute_revision_priority(self, profile: Profile) -> list[str]:
        """decay_score * gap_frequency = today's study queue."""
        scored = [
            (concept, profile.decay_scores[concept] * profile.gap_frequency[concept])
            for concept in profile.tracked_concepts
        ]
        return [c for c, _ in sorted(scored, key=lambda x: -x[1])]
```

### Agent 8 (System): Adversarial Proxy Agent

Detailed in Section 4.4. Key properties:
- Sees ONLY the student's original query, never the agent conversation history
- Runs an independent minimization task
- Its independence is structural, not designed
- Output feeds into IDMS, not directly to student

---

## 6. LangGraph Node Architecture

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

def build_learnflow_graph(agents: AgentRegistry, idms: IDMS) -> StateGraph:
    
    graph = StateGraph(LearnFlowState)
    
    # ── NODES ──────────────────────────────────────────────────────
    graph.add_node("orchestrator", agents.orchestrator.route)
    graph.add_node("socratic", agents.socratic.run)
    graph.add_node("gap_explainer", agents.gap_explainer.run)
    graph.add_node("closure", agents.closure.run)
    graph.add_node("cinema", agents.cinema.run)
    graph.add_node("anti_overing", agents.anti_overing.run)
    graph.add_node("profile_update", agents.profile.update_from_state)
    graph.add_node("idms_check", idms.check_and_intervene)
    graph.add_node("proxy_agent", agents.proxy.run)
    
    # ── ENTRY ──────────────────────────────────────────────────────
    graph.set_entry_point("orchestrator")
    
    # ── ROUTING FROM ORCHESTRATOR ──────────────────────────────────
    graph.add_conditional_edges(
        "orchestrator",
        route_to_agent,
        {
            "socratic": "socratic",
            "gap_explainer": "gap_explainer",
            "closure": "closure",
            "cinema": "cinema",
            "anti_overing": "anti_overing",
        }
    )
    
    # ── ALL AGENTS → IDMS CHECK ────────────────────────────────────
    # Every agent output passes through IDMS before being finalized
    for agent_node in ["socratic", "gap_explainer", "closure", "cinema", "anti_overing"]:
        graph.add_edge(agent_node, "idms_check")
    
    # ── IDMS → PROXY (if drift detected) or PROFILE UPDATE ─────────
    graph.add_conditional_edges(
        "idms_check",
        lambda state: "proxy_agent" if state["drift_detected"] else "profile_update",
        {
            "proxy_agent": "proxy_agent",
            "profile_update": "profile_update",
        }
    )
    
    # ── PROXY → PROFILE UPDATE (always) ────────────────────────────
    graph.add_edge("proxy_agent", "profile_update")
    
    # ── PROFILE UPDATE → END ───────────────────────────────────────
    graph.add_edge("profile_update", END)
    
    # ── CHECKPOINTING ──────────────────────────────────────────────
    memory = SqliteSaver.from_conn_string("learnflow_sessions.db")
    
    return graph.compile(checkpointer=memory)


def route_to_agent(state: LearnFlowState) -> str:
    return state["next_agent"]
```

---

## 7. State Schema

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class LearnFlowState(TypedDict):
    # ── Session identity ──────────────────────────────────────────
    session_id: str
    student_id: str
    current_chapter: str
    current_problem: str | None
    
    # ── Message history ───────────────────────────────────────────
    message_history: Annotated[list, add_messages]
    current_input: str
    
    # ── Routing ───────────────────────────────────────────────────
    next_agent: str
    active_beat: int | None           # for Cinema agent (1-5)
    beat_awaiting_response: bool      # Beat 3 gate
    
    # ── IDMS state ────────────────────────────────────────────────
    drift_detected: bool
    drift_magnitude: float
    trigger_map_state: dict           # serialized TriggerMap
    proxy_context_window: list[dict]  # serialized ProxyContextWindow
    gate_value: float
    
    # ── Agent signals for profile ─────────────────────────────────
    closure_verdict: str | None       # "COVERED" | "CLOSED" | None
    anti_overing_verdict: str | None  # "PROCEDURE_SUCCESS_PRINCIPLE_FAILURE" | "CLOSED" | None
    socratic_rounds: int              # how many rounds before unlock
    
    # ── Profile ───────────────────────────────────────────────────
    profile_summary: dict
    revision_queue: list[str]
    hint_density: str                 # "low" | "medium" | "high"
    
    # ── Output ────────────────────────────────────────────────────
    final_response: str
    response_agent: str               # which agent produced this
    behavioral_anchors_applied: list[str]
```

---

## 8. Module-by-Module Implementation

### Module 1: Chapter Brief (Dynamic Entry Framework)

```python
class ChapterBriefGenerator:
    """
    LLM-generated entry framework. Maps the territory before the student starts.
    Produces: central questions, dependency order, archetype signatures.
    """
    
    async def generate(self, chapter: str, student_profile: Profile) -> ChapterBrief:
        prompt = f"""
        Generate a structured entry framework for: {chapter}
        
        Student profile context:
        - Depth preference: {student_profile.depth_preference}
        - Known gaps: {student_profile.known_gaps}
        - Recurring errors: {student_profile.error_patterns}
        
        Produce exactly:
        1. CENTRAL QUESTIONS (3-5): The questions this chapter answers
        2. DEPENDENCY MAP: What must be understood first, in order
        3. ARCHETYPE SIGNATURES (3-5): The problem types that appear in JEE/NEET
           for this chapter, with the decision signal that identifies each
        4. COMMON MISCONCEPTIONS: What students typically get wrong
        
        Format as structured JSON.
        """
        response = await self.llm.ainvoke(prompt)
        return ChapterBrief.from_json(response.content)
```

### Module 2: Entry Protocol (Socratic)

Already covered in Agent 2. Implementation note: the Diagram Gate is enforced at the **state level**, not just the prompt level. `beat_awaiting_response` in state must be `False` before the system will route to any calculation-adjacent agent.

```python
async def enforce_diagram_gate(state: LearnFlowState) -> bool:
    """Returns True if student has described a diagram setup."""
    if state.get("diagram_described"):
        return True
    # Check last student message for diagram description
    last_input = state["current_input"]
    check = await llm.ainvoke(f"""
    Did the student describe a physical diagram or setup in this message?
    Message: {last_input}
    Answer YES or NO only.
    """)
    return "YES" in check.content.upper()
```

### Module 3: Step Gap Explainer

Already covered in Agent 3. Implementation note: Gap Explainer receives both the standard solution AND the student's attempt. It must identify the specific transition, not just the error.

```python
class GapExplainerAgent:
    async def run(self, state: LearnFlowState) -> LearnFlowState:
        standard_solution = await self.solution_db.get(state["current_problem"])
        student_attempt = state["current_input"]
        
        gap_prompt = f"""
        Standard solution steps: {standard_solution.steps}
        Student's attempt: {student_attempt}
        
        Identify the SINGLE logical transition that was skipped.
        Not an algebraic error — a conceptual/logical move.
        
        Respond in exactly this format:
        WHAT YOU KNEW: [one sentence]
        THE GAP: [one sentence — the implicit logical move]
        WHAT IT UNLOCKED: [one sentence]
        """
        
        response = await self.llm.ainvoke([
            SystemMessage(GAP_EXPLAINER_SYSTEM_PROMPT),
            HumanMessage(gap_prompt)
        ])
        
        state["final_response"] = response.content
        state["response_agent"] = "gap_explainer"
        return state
```

### Module 4: Closure Check

Already covered in Agent 4. The COVERED/CLOSED output feeds directly into the profile agent as a signal.

### Module 5: Concept Cinema

Beat 3 gate is enforced at state level. The graph will not route to Beat 4 until `beat_awaiting_response` is resolved.

```python
class ConceptCinemaAgent:
    BEATS = [
        "intuition_hook",
        "analogy_bridge", 
        "checkpoint",      # → requires student response before continuing
        "formalism",
        "why_this_form"
    ]
    
    async def run(self, state: LearnFlowState) -> LearnFlowState:
        current_beat = state.get("active_beat", 1)
        
        # Beat 3 gate check
        if current_beat == 3 and state.get("beat_awaiting_response"):
            # Process student response to checkpoint before advancing
            verdict = await self.evaluate_checkpoint_response(
                state["current_input"],
                state["current_chapter"]
            )
            if verdict == "ADEQUATE":
                state["active_beat"] = 4
                state["beat_awaiting_response"] = False
            else:
                # Re-ask checkpoint with different angle
                state["final_response"] = await self.reframe_checkpoint(state)
                return state
        
        response = await self.generate_beat(current_beat, state)
        
        if current_beat == 3:
            state["beat_awaiting_response"] = True
        
        state["active_beat"] = current_beat
        state["final_response"] = response
        state["response_agent"] = "cinema"
        return state
```

### Module 6: Anti-Overing Engine

Already covered in Agent 6. The isomorphic pair database is the key infrastructure:

```python
class IsomorphicPairDatabase:
    """
    Maps problems to their structural twins across different surface features.
    E.g.: two-block collision ↔ ballistic pendulum ↔ rocket propulsion
    All are momentum conservation with the same dp/dt structure.
    """
    
    pairs = {
        "momentum_conservation": [
            "two_block_collision",
            "ballistic_pendulum", 
            "rocket_propulsion",
            "explosion_recoil"
        ],
        "energy_method_vs_newton": [
            "block_on_incline_with_friction",
            "pendulum_with_damping",
            "spring_block_system"
        ],
        # ... expand across full JEE/NEET syllabus
    }
    
    async def get_structural_twin(self, problem_id: str) -> Problem:
        principle = self.find_principle(problem_id)
        twins = self.pairs[principle]
        twin_id = random.choice([t for t in twins if t != problem_id])
        return await self.problem_db.get(twin_id)
```

---

## 9. Data Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                       POSTGRESQL                                │
│                                                                 │
│  students          sessions           problems                  │
│  ─────────         ────────           ────────                  │
│  id                id                 id                        │
│  created_at        student_id         chapter                   │
│  metadata          started_at         principle_tag             │
│                    state_json         difficulty                 │
│                    active             isomorphic_group          │
│                                       standard_solution         │
│                                                                 │
│  profiles          agent_signals      closure_verdicts          │
│  ────────          ─────────────      ───────────────           │
│  student_id        session_id         session_id                │
│  depth_pref        agent_name         concept                   │
│  breaking_pts      signal_type        verdict                   │
│  error_patterns    content            timestamp                 │
│  decay_scores      timestamp                                    │
│  gap_frequency                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         REDIS                                   │
│                                                                 │
│  session:{id}:state        → current LearnFlowState (JSON)      │
│  session:{id}:trigger_map  → serialized TriggerMap              │
│  session:{id}:proxy_window → serialized ProxyContextWindow      │
│  session:{id}:asi_scores   → agent ASI scores                   │
│  student:{id}:profile      → cached profile (5min TTL)          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       CHROMADB                                  │
│                                                                 │
│  collection: concept_embeddings                                 │
│    → embeddings of all JEE/NEET concepts                        │
│    → used for isomorphic pair retrieval                         │
│                                                                 │
│  collection: student_error_patterns                             │
│    → embeddings of student errors per session                   │
│    → used to find recurring patterns across sessions            │
│                                                                 │
│  collection: trigger_maps                                       │
│    → embeddings of drift patterns                               │
│    → used by IDMS for similarity lookup                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Evaluation & ASI Monitoring

### Agent Stability Index (ASI)

Adapted from Rath (2026) for the LearnFlow context. Tracks 6 dimensions per agent per session:

```python
class ASIMonitor:
    DIMENSIONS = [
        "format_consistency",      # is the agent using its prescribed format?
        "role_adherence",          # is the agent staying in its role?
        "question_ratio",          # for Socratic: ratio of questions to statements
        "answer_leakage",          # did any agent give a direct answer?
        "verdict_specificity",     # for Closure: COVERED/CLOSED vs vague
        "inter_agent_agreement",   # are agents agreeing more than the input justifies?
    ]
    
    def compute_asi(self, agent_name: str, recent_outputs: list[str]) -> float:
        scores = []
        
        for dimension in self.DIMENSIONS:
            score = self.score_dimension(agent_name, dimension, recent_outputs)
            scores.append(score)
        
        # Weighted average — role_adherence and answer_leakage weighted highest
        weights = [0.15, 0.25, 0.15, 0.20, 0.10, 0.15]
        asi = sum(s * w for s, w in zip(scores, weights))
        return asi
    
    def check_drift(self, asi: float) -> bool:
        return asi < 0.65  # below threshold = drift detected
```

### Drift Event Log

Every IDMS intervention is logged for evaluation:

```python
@dataclass
class DriftEvent:
    session_id: str
    timestamp: float
    drift_magnitude: float
    trigger_pattern_direction: np.ndarray  # dominant PCA direction
    gate_value: float
    proxy_perturbation_norm: float
    agents_affected: list[str]
    anchors_applied: list[str]
    post_intervention_asi: float  # measured 3 turns later
```

---

## 11. Tech Stack

```
LLM Backbone        claude-sonnet-4-6 (primary) / gpt-4o (fallback)
Agent Framework     LangGraph 0.2+
Embeddings          sentence-transformers/all-MiniLM-L6-v2 (local, fast)
Vector DB           ChromaDB (local) → Pinecone (production)
Session DB          PostgreSQL 16
Cache               Redis 7
Backend API         FastAPI + uvicorn
Session State       LangGraph SqliteSaver (dev) → Redis checkpointer (prod)
Frontend            React + Tailwind (dark academic palette)
Deployment          Docker Compose (dev) → Railway / Render (prod)
```

### Environment Setup

```bash
# Clone and setup
git clone https://github.com/aadithya12ctrl/learnflow
cd learnflow
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# requirements.txt
langgraph>=0.2.0
langchain-anthropic
langchain-openai
sentence-transformers
chromadb
psycopg2-binary
redis
fastapi
uvicorn
numpy
scikit-learn
sqlalchemy
pydantic>=2.0
python-dotenv

# Environment variables
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...        # fallback
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379
```

### Directory Structure

```
learnflow/
├── agents/
│   ├── orchestrator.py
│   ├── socratic.py
│   ├── gap_explainer.py
│   ├── closure.py
│   ├── cinema.py
│   ├── anti_overing.py
│   ├── adaptive_profile.py
│   └── proxy.py
├── idms/
│   ├── proxy_context_window.py
│   ├── trigger_map.py
│   ├── decomposition.py
│   ├── adversarial_proxy.py
│   ├── gate.py
│   └── idms.py                    # orchestrates all IDMS components
├── graph/
│   ├── state.py
│   ├── nodes.py
│   └── builder.py
├── data/
│   ├── models.py
│   ├── profile_db.py
│   ├── problem_db.py
│   └── isomorphic_pairs.py
├── monitoring/
│   ├── asi_monitor.py
│   └── drift_logger.py
├── api/
│   ├── main.py
│   └── routes.py
└── tests/
    ├── test_idms.py
    ├── test_agents.py
    └── test_drift_scenarios.py
```

---

## 12. Roadmap

### Phase 1 — Core Pipeline (Weeks 1-3)
- [ ] State schema and LangGraph graph skeleton
- [ ] Orchestrator with basic routing (no drift detection yet)
- [ ] Socratic agent + Diagram Gate enforcement
- [ ] Cinema agent with Beat 3 gate
- [ ] FastAPI endpoints for session management

### Phase 2 — Full Agent Roster (Weeks 4-6)
- [ ] Gap Explainer with solution database
- [ ] Closure agent with COVERED/CLOSED detector
- [ ] Anti-Overing engine with isomorphic pair database
- [ ] Adaptive Profile agent with decay scoring
- [ ] ASI monitoring baseline

### Phase 3 — IDMS Integration (Weeks 7-9)
- [ ] TriggerMap with negative prompt grading
- [ ] ProxyContextWindow with self-referential boundary
- [ ] Latent decomposition (additive, lossless)
- [ ] Adversarial Proxy Agent (independent minimization task)
- [ ] Input-dependent gate
- [ ] Full IDMS orchestration in graph
- [ ] Drift event logging

### Phase 4 — Evaluation & Hardening (Weeks 10-12)
- [ ] ASI threshold calibration (run synthetic drift scenarios)
- [ ] Behavioral anchor injection testing
- [ ] Profile accuracy evaluation (predicted gaps vs actual student errors)
- [ ] End-to-end session tests across JEE Physics chapters
- [ ] Latency profiling (IDMS must add <200ms per turn)

### Phase 5 — Content & Scale (Ongoing)
- [ ] Expand isomorphic pair database across full JEE/NEET syllabus
- [ ] Chapter Brief generation for all chapters (Physics → Chemistry → Math)
- [ ] Multi-session profile persistence and longitudinal gap tracking
- [ ] Mentor dashboard (Covered vs Closed maps, Stuck Most Often signals)

---

## Appendix: IDMS Full Integration Point

```python
class IDMS:
    """
    Full Intent-Drift Mitigation System.
    Called after every agent output, before profile update.
    """
    
    def __init__(self, embedding_model, llm):
        self.trigger_maps: dict[str, TriggerMap] = {}
        self.proxy_windows: dict[str, ProxyContextWindow] = {}
        self.gate = InputDependentGate(embedding_model)
        self.proxy_agent = AdversarialProxyAgent(llm, embedding_model)
        self.embedding_model = embedding_model
    
    async def check_and_intervene(self, state: LearnFlowState) -> LearnFlowState:
        session_id = state["session_id"]
        
        # Initialize per-session structures
        if session_id not in self.trigger_maps:
            self.trigger_maps[session_id] = TriggerMap("orchestrator", "student")
            self.proxy_windows[session_id] = ProxyContextWindow()
        
        trigger_map = self.trigger_maps[session_id]
        proxy_window = self.proxy_windows[session_id]
        
        # Compute residual score from latest agent exchange
        if len(state["message_history"]) >= 2:
            residual_score = trigger_map.compute_residual_score(
                agent_b_output=state["message_history"][-2].content,
                agent_a_intended_response=self.get_role_baseline(state["response_agent"]),
                agent_a_actual_response=state["final_response"]
            )
            
            proxy_window.add(state["message_history"][-1], residual_score)
        
        drift_magnitude = proxy_window.drift_signal
        state["drift_magnitude"] = drift_magnitude
        
        if drift_magnitude > 0.72:
            state["drift_detected"] = True
            
            # Run proxy agent
            proxy_output = await self.proxy_agent.run(
                student_query=state["current_input"],
                current_context=""  # deliberately empty — proxy is independent
            )
            
            # Compute gate
            drift_direction = trigger_map.get_trigger_pattern()
            gate_value = self.gate.compute(state["current_input"], drift_direction)
            state["gate_value"] = gate_value
            
            # Apply perturbation to final response context
            perturbation = self.proxy_agent.compute_perturbation(
                proxy_output, drift_direction, gate_value
            )
            
            # Inject proxy reframe into state for orchestrator to use in re-anchor
            state["proxy_reframe"] = proxy_output.content
            state["perturbation_norm"] = float(np.linalg.norm(perturbation))
            
        else:
            state["drift_detected"] = False
        
        return state
    
    def get_drift_state(self) -> DriftState:
        # aggregated across all active sessions
        magnitudes = [w.drift_signal for w in self.proxy_windows.values()]
        return DriftState(magnitude=max(magnitudes) if magnitudes else 0.0)
```

---

*LearnFlow — Training Principles, Not Procedures. Built with intent-drift-aware multi-agent architecture.*
