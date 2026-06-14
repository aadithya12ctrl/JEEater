"""
Orchestrator Agent — LearnFlow Agent 1.

Role: Session manager, router, drift monitor.
The only agent with full system visibility.

Drift risk: Coordination drift — starts routing lazily, stops checking agent state.

Spec reference: §5 Agent 1, lines 831-900.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LearnFlowState


# ── System prompt — verbatim from spec §5 Agent 1 (lines 845-863) ──

ORCHESTRATOR_SYSTEM_PROMPT = """\
You are the session coordinator for a JEE/NEET learning system.
Your job is to route student inputs to the correct specialist agent
and monitor the quality of the learning experience.

ROUTING RULES (follow strictly):
- Student is stuck / first entering a problem → socratic
- Student has a solution but missed a logical step → gap_explainer
- Student claims to understand a concept → closure
- Student needs to learn a concept from scratch → cinema
- Student is pattern-matching without understanding → anti_overing
- Session context needed for routing decision → check Adaptive Profile first

CRITICAL: You never explain concepts directly. You route. If you catch
yourself about to explain something, stop and route to the correct agent.

Monitor signal: if any agent's last 3 outputs look like the same format
collapsed, flag it as behavioral drift and apply re-anchor.

Respond with exactly one word (lowercase) indicating the next agent:
socratic | gap_explainer | closure | cinema | anti_overing
"""


# ── Behavioral Anchors — from spec §5 per-agent sections ──
# These are re-injected when IDMS detects drift ≥ 0.72.
# Each anchor re-grounds the agent to its role definition.

BEHAVIORAL_ANCHORS = {
    "socratic": (
        "ANCHOR: Your output must end with a question mark. "
        "You are not allowed to state any physics principle directly."
    ),
    "gap_explainer": (
        "ANCHOR: Your response has exactly 3 labeled sections: "
        "WHAT YOU KNEW | THE GAP | WHAT IT UNLOCKED. "
        "No section exceeds 3 sentences."
    ),
    "closure": (
        "ANCHOR: If the student used the word 'formula' or 'equation' in their "
        "explanation without explaining WHY that form, it is not closed."
    ),
    "cinema": (
        "ANCHOR: The formula must not appear before Beat 4. "
        "If you wrote a formula in Beat 1, 2, or 3 — restart."
    ),
    "anti_overing": (
        "ANCHOR: A student getting the right answer by the wrong method "
        "is a FAILURE state, not a success state."
    ),
}


class OrchestratorAgent:
    """
    Session coordinator and router.

    Spec §5.1: receives student input, determines which agent(s) to
    activate, monitors ASI scores, triggers IDMS when drift threshold
    is crossed, re-anchors drifting agents with behavioral anchor
    prompts, manages session state and persona anchors.
    """

    def __init__(self, llm, idms, profile_agent):
        self.llm = llm
        self.idms = idms
        self.profile = profile_agent
        self.agent_asi_scores: dict[str, float] = {}
        self.anchors_applied: list[str] = []

    async def route(self, state: LearnFlowState) -> LearnFlowState:
        """
        Main routing node.  Returns updated state with `next_agent` set.

        1. Fetch profile and drift state.
        2. If drift magnitude ≥ 0.72 → apply behavioral anchors.
        3. LLM routing decision.
        4. Write `next_agent` into state.
        """
        student_input = state.get("current_input", "")
        profile = await self.profile.get_current_profile(
            state.get("session_id", "default")
        )
        drift_state = self.idms.get_drift_state(
            state.get("session_id", "default")
        )

        # ── Check if IDMS intervention is needed before routing ──
        self.anchors_applied = []
        if drift_state.magnitude >= 0.72:
            self.anchors_applied = list(BEHAVIORAL_ANCHORS.keys())
            state["behavioral_anchors_applied"] = self.anchors_applied
        else:
            state["behavioral_anchors_applied"] = []

        routing_prompt = f"""\
Student input: {student_input}
Student profile summary: {profile.summary if profile else "No profile yet."}
Current chapter: {state.get('current_chapter', 'General Physics')}
Session history length: {len(state.get('message_history', []))}

Which agent should handle this? Respond with exactly one of:
socratic | gap_explainer | closure | cinema | anti_overing
"""

        response = await self.llm.ainvoke([
            SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT),
            HumanMessage(content=routing_prompt),
        ])

        next_agent = response.content.strip().lower()

        # Sanity check — default to socratic on parse failure
        valid_agents = [
            "socratic", "gap_explainer", "closure", "cinema", "anti_overing"
        ]
        if next_agent not in valid_agents:
            next_agent = "socratic"

        state["next_agent"] = next_agent
        return state

    async def apply_behavioral_anchors(self, state: LearnFlowState):
        """
        Re-ground each agent to its role definition at session boundaries.
        Spec §5.1 line 895-899.
        """
        for agent_name in BEHAVIORAL_ANCHORS:
            anchor = BEHAVIORAL_ANCHORS[agent_name]
            # Anchor text is passed as additional system messages
            # to the agent on its next invocation
            state.setdefault("pending_anchors", {})[agent_name] = anchor
