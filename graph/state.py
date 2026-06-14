from typing import TypedDict, Annotated, Any, Dict, List
from langgraph.graph.message import add_messages

class LearnFlowState(TypedDict):
    # -- Session identity --
    session_id: str
    student_id: str
    current_chapter: str
    current_problem: str | None
    
    # -- Message history --
    message_history: Annotated[list, add_messages]
    current_input: str
    
    # -- Routing --
    next_agent: str
    active_beat: int | None           # for Cinema agent (1-5)
    beat_awaiting_response: bool      # Beat 3 gate
    diagram_described: bool           # Diagram Gate flag
    
    # -- IDMS state --
    drift_detected: bool
    drift_magnitude: float
    trigger_map_state: Dict[str, Any]           # serialized TriggerMap
    proxy_context_window: List[Dict[str, Any]]  # serialized ProxyContextWindow
    gate_value: float
    proxy_reframe: str | None
    perturbation_norm: float
    
    # -- Agent signals for profile --
    closure_verdict: str | None       # "COVERED" | "CLOSED" | None
    anti_overing_verdict: str | None  # "PROCEDURE_SUCCESS_PRINCIPLE_FAILURE" | "CLOSED" | None
    socratic_rounds: int              # how many rounds before unlock
    
    # -- Profile --
    profile_summary: Dict[str, Any]
    revision_queue: List[str]
    hint_density: str                 # "low" | "medium" | "high"
    
    # -- Output --
    final_response: str
    response_agent: str               # which agent produced this
    behavioral_anchors_applied: List[str]
