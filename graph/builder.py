"""
graph/builder.py — LangGraph StateGraph construction.

Matches spec §6 (lines 1168-1234) exactly:
  orchestrator → {socratic|gap_explainer|closure|cinema|anti_overing}
  all agents   → idms_check
  idms_check   → proxy_agent  (if drift_detected)  OR  profile_update
  proxy_agent  → profile_update
  profile_update → END

Checkpointing via SqliteSaver (dev) or MemorySaver (fallback).
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import LearnFlowState
from graph.nodes import route_to_agent, idms_route


class AgentRegistry:
    """Registry of all LearnFlow agent instances."""

    def __init__(self, orchestrator, socratic, gap_explainer, closure,
                 cinema, anti_overing, profile, proxy):
        self.orchestrator = orchestrator
        self.socratic = socratic
        self.gap_explainer = gap_explainer
        self.closure = closure
        self.cinema = cinema
        self.anti_overing = anti_overing
        self.profile = profile
        self.proxy = proxy          # AdversarialProxyAgent — spec requires it


def build_learnflow_graph(agents: AgentRegistry, idms) -> StateGraph:
    """
    Build and compile the full LearnFlow LangGraph.

    Spec §6, lines 1174-1229.
    """
    graph = StateGraph(LearnFlowState)

    # ── NODES ──────────────────────────────────────────────────────
    graph.add_node("orchestrator",  agents.orchestrator.route)
    graph.add_node("socratic",      agents.socratic.run)
    graph.add_node("gap_explainer", agents.gap_explainer.run)
    graph.add_node("closure",       agents.closure.run)
    graph.add_node("cinema",        agents.cinema.run)
    graph.add_node("anti_overing",  agents.anti_overing.run)
    graph.add_node("profile_update", agents.profile.update_from_state)
    graph.add_node("idms_check",    idms.check_and_intervene)
    graph.add_node("proxy_agent",   agents.proxy.run)          # WAS MISSING

    # ── ENTRY ──────────────────────────────────────────────────────
    graph.set_entry_point("orchestrator")

    # ── ROUTING FROM ORCHESTRATOR ──────────────────────────────────
    graph.add_conditional_edges(
        "orchestrator",
        route_to_agent,
        {
            "socratic":      "socratic",
            "gap_explainer": "gap_explainer",
            "closure":       "closure",
            "cinema":        "cinema",
            "anti_overing":  "anti_overing",
        }
    )

    # ── ALL AGENTS → IDMS CHECK ────────────────────────────────────
    # Every agent output passes through IDMS before being finalised
    for agent_node in ["socratic", "gap_explainer", "closure", "cinema", "anti_overing"]:
        graph.add_edge(agent_node, "idms_check")

    # ── IDMS → PROXY (if drift detected) or PROFILE UPDATE ─────────
    # THIS IS THE CRITICAL CONDITIONAL EDGE — was previously a hard edge
    graph.add_conditional_edges(
        "idms_check",
        idms_route,        # returns "proxy_agent" if drift else "profile_update"
        {
            "proxy_agent":    "proxy_agent",
            "profile_update": "profile_update",
        }
    )

    # ── PROXY → PROFILE UPDATE (always) ────────────────────────────
    graph.add_edge("proxy_agent", "profile_update")

    # ── PROFILE UPDATE → END ───────────────────────────────────────
    graph.add_edge("profile_update", END)

    # ── CHECKPOINTING ──────────────────────────────────────────────
    # MemorySaver for simple in-memory session persistence
    memory = MemorySaver()

    return graph.compile(checkpointer=memory)
