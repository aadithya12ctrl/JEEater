"""
Adversarial Proxy Agent — LearnFlow Agent 8 (System).

This agent is NOT adversarial in intent. It pursues an independent low-effort
auxiliary task. The perturbation it creates in the shared latent space is a
structural byproduct of its independence, not a designed intervention.

Key properties (from spec §4.4):
  - Sees ONLY the student's original query, never the agent conversation history
  - Runs an independent minimization / classification / boundary_case task
  - Its independence is structural, not designed
  - Output feeds into IDMS, not directly to student

The proxy is analogous to dropout in neural networks: agents cannot co-adapt
(drift into consensus) if their shared context contains signal they cannot
collectively predict.  The proxy agent IS that signal.
"""

import numpy as np
from typing import NamedTuple
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LearnFlowState
from idms.trigger_map import TriggerMap


# ── Data structures ───────────────────────────────────────────────

class ProxyOutput(NamedTuple):
    content: str
    embedding: np.ndarray
    task_type: str
    orthogonality_to_drift: float


# ── Agent ─────────────────────────────────────────────────────────

class AdversarialProxyAgent:
    """
    An independent agent pursuing a low-effort auxiliary task.

    The auxiliary task is deliberately laterally shifted — not a simpler
    version of what the main agents do, but something different in the
    same domain.  This maximises the structural distance between the
    proxy's representations and the drift direction.

    Current auxiliary tasks (selected adaptively by pattern coherence):
      - minimization   → stripped-down factual restatement
      - classification → name the principle + mathematical form
      - boundary_case  → describe the key edge case in one sentence
    """

    AUXILIARY_TASKS = {
        "minimization": (
            "You are a minimizer. Given only the student's original question, "
            "produce the single most stripped-down factual restatement of what "
            "they are actually asking about. No pedagogy, no framing, no "
            "explanation strategy, no hints about approach. Just the core "
            "physical or mathematical fact at the center of the question. "
            "Maximum 2 sentences. Start fresh from the student's query only."
        ),
        "classification": (
            "Given only the student's original question, identify the single "
            "most specific physics/math principle that this question is an "
            "instance of. Name the principle and state its mathematical form. "
            "Nothing else. Do not reference how anyone has approached this."
        ),
        "boundary_case": (
            "Given only the student's original question, describe the single "
            "most important edge case or limiting condition where the standard "
            "approach would fail. One sentence only."
        ),
    }

    def __init__(self, llm, embedding_model):
        self.llm = llm
        self.embedding_model = embedding_model
        self.current_task = "minimization"
        self.task_rotation_counter = 0

    # ── Task selection (spec §4.4 select_task) ────────────────────

    def select_task(self, pattern_coherence: float) -> str:
        """
        High coherence (consistent drift direction)
          → minimization (maximum orthogonality to drift)

        Low coherence (diffuse drift)
          → rotate through tasks to find which produces
            the most orthogonal representation to the noisy drift
        """
        if pattern_coherence > 0.7:
            return "minimization"
        tasks = list(self.AUXILIARY_TASKS.keys())
        task = tasks[self.task_rotation_counter % len(tasks)]
        self.task_rotation_counter += 1
        return task

    # ── Core proxy invocation ─────────────────────────────────────

    async def run_proxy_task(
        self,
        student_query: str,
        drift_direction: np.ndarray,
        pattern_coherence: float,
    ) -> ProxyOutput:
        task_name = self.select_task(pattern_coherence)
        task_prompt = self.AUXILIARY_TASKS[task_name]

        # CRITICAL: proxy sees ONLY the original student query.
        # NOT current_context, NOT message_history, NOT any agent output.
        # This structural isolation IS the mechanism.
        response = await self.llm.ainvoke([
            SystemMessage(content=task_prompt),
            HumanMessage(content=student_query),
        ])

        proxy_emb = self.embedding_model.encode(response.content)

        # Measure orthogonality to drift direction
        drift_n = np.linalg.norm(drift_direction)
        drift_norm = drift_direction / (drift_n + 1e-8) if drift_n > 1e-8 else drift_direction
        proxy_n = np.linalg.norm(proxy_emb)
        proxy_norm = proxy_emb / (proxy_n + 1e-8) if proxy_n > 1e-8 else proxy_emb

        orthogonality = 1.0 - abs(float(np.dot(proxy_norm, drift_norm)))

        return ProxyOutput(
            content=response.content,
            embedding=proxy_emb,
            task_type=task_name,
            orthogonality_to_drift=orthogonality,
        )

    # ── Perturbation computation (spec §4.4 compute_perturbation) ─

    def compute_perturbation(
        self,
        proxy_output: ProxyOutput,
        drift_direction: np.ndarray,
        gate_value: float,
        drift_velocity: float,
    ) -> np.ndarray:
        """
        perturbation = proxy embedding projected AWAY from drift direction,
        scaled by gate value and amplified by drift velocity.

        drift_velocity > 0 → drift accelerating → amplify perturbation
        drift_velocity < 0 → drift decelerating → reduce perturbation

        The projection step is critical: we inject only the component
        orthogonal to the drift direction so the perturbation is purely
        corrective — it doesn't accidentally reinforce any other pattern.
        """
        proxy_emb = proxy_output.embedding
        drift_n = np.linalg.norm(drift_direction)
        drift_norm = drift_direction / (drift_n + 1e-8) if drift_n > 1e-8 else drift_direction

        # Project out drift-aligned component from proxy embedding
        proxy_drift_component = np.dot(proxy_emb, drift_norm) * drift_norm
        proxy_clean = proxy_emb - proxy_drift_component

        # Velocity scaling: amplify on acceleration, floor at 1.0
        velocity_scale = 1.0 + max(0.0, drift_velocity)

        return proxy_clean * gate_value * velocity_scale

    # ── Embedding-level context injection (spec §4.4) ─────────────

    @staticmethod
    def inject_into_context(
        perturbation: np.ndarray,
        agent_context_embedding: np.ndarray,
    ) -> np.ndarray:
        """
        At the embedding level:  modified = original + perturbation
        At the prompt level:     add proxy reframe as a system message

        Both are applied; the embedding-level modification guides retrieval
        from the agent's vector context, the prompt-level modification
        directly influences the LLM's next output.
        """
        return agent_context_embedding + perturbation

    # ── LangGraph node entrypoint ─────────────────────────────────

    async def run(self, state: LearnFlowState) -> LearnFlowState:
        """
        Called as a graph node when idms_check detects drift ≥ 0.72.
        Reconstructs trigger-map from serialised state, runs the
        independent proxy task, computes perturbation, and writes
        the reframe + norm back into state for the orchestrator
        to inject as a behavioral anchor.
        """
        # Reconstruct trigger map from serialised state
        if state.get("trigger_map_state"):
            trigger_map = TriggerMap.from_dict(state["trigger_map_state"])
        else:
            trigger_map = TriggerMap("orchestrator", "student")

        drift_direction = trigger_map.get_trigger_pattern()

        # Run the independent proxy task
        proxy_output = await self.run_proxy_task(
            student_query=state.get("current_input", ""),
            drift_direction=drift_direction,
            pattern_coherence=trigger_map.pattern_coherence,
        )

        # Estimate drift velocity from the proxy-window score history
        drift_velocity = 0.0
        pcw_data = state.get("proxy_context_window", [])
        if isinstance(pcw_data, list):
            scores = [m.get("score", 0.0) for m in pcw_data if isinstance(m, dict) and "score" in m]
            if len(scores) >= 2:
                drift_velocity = scores[-1] - scores[-2]

        gate_value = state.get("gate_value", 0.0)

        perturbation = self.compute_perturbation(
            proxy_output=proxy_output,
            drift_direction=drift_direction,
            gate_value=gate_value,
            drift_velocity=drift_velocity,
        )

        # Inject reframe and perturbation norm into state
        state["proxy_reframe"] = proxy_output.content
        state["perturbation_norm"] = float(np.linalg.norm(perturbation))

        return state
