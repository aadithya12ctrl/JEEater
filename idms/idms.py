import numpy as np
from typing import Dict, Any
from idms.proxy_context_window import ProxyContextWindow
from idms.trigger_map import TriggerMap
from idms.gate import InputDependentGate
from graph.state import LearnFlowState

class DriftState:
    def __init__(self, magnitude: float):
        self.magnitude = magnitude

class IDMS:
    def __init__(self, embedding_model, llm):
        self.embedding_model = embedding_model
        self.llm = llm
        self.gate = InputDependentGate(embedding_model)
        self.trigger_maps: Dict[str, TriggerMap] = {}
        self.proxy_windows: Dict[str, ProxyContextWindow] = {}
        
    def _get_session_components(self, state: LearnFlowState) -> tuple[TriggerMap, ProxyContextWindow]:
        session_id = state.get("session_id", "default")
        
        if state.get("trigger_map_state"):
            trigger_map = TriggerMap.from_dict(state["trigger_map_state"])
        elif session_id in self.trigger_maps:
            trigger_map = self.trigger_maps[session_id]
        else:
            trigger_map = TriggerMap("orchestrator", "student")
            self.trigger_maps[session_id] = trigger_map
            
        if state.get("proxy_context_window"):
            proxy_window = ProxyContextWindow.from_dict({
                "window": state["proxy_context_window"], 
                "residual_scores": [m.get("score", 0.0) for m in state["proxy_context_window"] if "score" in m]
            })
        elif session_id in self.proxy_windows:
            proxy_window = self.proxy_windows[session_id]
        else:
            proxy_window = ProxyContextWindow()
            self.proxy_windows[session_id] = proxy_window
            
        return trigger_map, proxy_window

    def _save_session_components(self, state: LearnFlowState, trigger_map: TriggerMap, proxy_window: ProxyContextWindow):
        session_id = state.get("session_id", "default")
        self.trigger_maps[session_id] = trigger_map
        self.proxy_windows[session_id] = proxy_window
        state["trigger_map_state"] = trigger_map.to_dict()
        state["proxy_context_window"] = proxy_window.to_dict()["window"]

    async def check_and_intervene(self, state: LearnFlowState) -> LearnFlowState:
        trigger_map, proxy_window = self._get_session_components(state)
        
        # Compute residual score from latest exchange
        history = state.get("message_history", [])
        if len(history) >= 2:
            agent_b_output = history[-2].content if hasattr(history[-2], "content") else history[-2].get("content", "")
            agent_a_actual = state.get("final_response", "")
            
            residual_score = trigger_map.compute_residual_score(
                agent_b_output=agent_b_output,
                agent_a_actual_response=agent_a_actual
            )
            
            last_msg = history[-1]
            msg_dict = {
                "content": last_msg.content if hasattr(last_msg, "content") else last_msg.get("content", ""), 
                "score": residual_score
            }
            proxy_window.add(msg_dict, residual_score)
        
        drift_magnitude = proxy_window.drift_signal
        state["drift_magnitude"] = drift_magnitude
        
        if drift_magnitude >= 0.72:
            state["drift_detected"] = True
            drift_direction = trigger_map.get_trigger_pattern()
            
            # Compute gate value
            gate_value = self.gate.compute(
                current_input=state.get("current_input", ""),
                drift_direction=drift_direction,
                drift_velocity=proxy_window.drift_velocity,
                pattern_coherence=trigger_map.pattern_coherence
            )
            state["gate_value"] = gate_value
        else:
            state["drift_detected"] = False
            state["gate_value"] = 0.0
            state["proxy_reframe"] = None
            state["perturbation_norm"] = 0.0
            
        self._save_session_components(state, trigger_map, proxy_window)
        return state
        
    def get_drift_state(self, session_id: str = "default") -> DriftState:
        if session_id in self.proxy_windows:
            return DriftState(magnitude=self.proxy_windows[session_id].drift_signal)
        return DriftState(magnitude=0.0)
