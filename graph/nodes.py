"""
graph/nodes.py — Thin node wrappers for the LangGraph graph.

Each function accepts and returns LearnFlowState, matching the
signature expected by StateGraph.add_node().

Spec reference: §6 LangGraph Node Architecture, lines 1168-1234.
"""

from graph.state import LearnFlowState


def route_to_agent(state: LearnFlowState) -> str:
    """Routing function used by orchestrator conditional edges."""
    return state["next_agent"]


def idms_route(state: LearnFlowState) -> str:
    """
    Conditional edge after idms_check.
    If drift_detected → proxy_agent (run independent perturbation task).
    Otherwise         → profile_update (skip proxy, proceed normally).
    Spec line 1213.
    """
    if state.get("drift_detected", False):
        return "proxy_agent"
    return "profile_update"
