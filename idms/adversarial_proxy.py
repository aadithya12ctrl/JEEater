import numpy as np
from typing import Any, Dict, NamedTuple
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LearnFlowState
from idms.trigger_map import TriggerMap

class ProxyOutput(NamedTuple):
    content: str
    embedding: np.ndarray
    task_type: str
    orthogonality_to_drift: float

class AdversarialProxyAgent:
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
        if pattern_coherence > 0.7:
            return "minimization"
        else:
            tasks = list(self.AUXILIARY_TASKS.keys())
            task = tasks[self.task_rotation_counter % len(tasks)]
            self.task_rotation_counter += 1
            return task
    
    async def run_proxy_task(
        self,
        student_query: str,
        drift_direction: np.ndarray,
        pattern_coherence: float
    ) -> ProxyOutput:
        task_name = self.select_task(pattern_coherence)
        task_prompt = self.AUXILIARY_TASKS[task_name]
        
        response = await self.llm.ainvoke([
            SystemMessage(content=task_prompt),
            HumanMessage(content=student_query)
        ])
        
        proxy_emb = self.embedding_model.encode(response.content)
        
        drift_norm_val = np.linalg.norm(drift_direction)
        if drift_norm_val > 1e-8:
            drift_norm = drift_direction / drift_norm_val
        else:
            drift_norm = drift_direction
            
        proxy_norm_val = np.linalg.norm(proxy_emb)
        if proxy_norm_val > 1e-8:
            proxy_norm = proxy_emb / proxy_norm_val
        else:
            proxy_norm = proxy_emb
            
        orthogonality = 1.0 - abs(float(np.dot(proxy_norm, drift_norm)))
        
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
        proxy_emb = proxy_output.embedding
        
        drift_norm_val = np.linalg.norm(drift_direction)
        if drift_norm_val > 1e-8:
            drift_norm = drift_direction / drift_norm_val
        else:
            drift_norm = drift_direction
        
        proxy_drift_component = np.dot(proxy_emb, drift_norm) * drift_norm
        proxy_clean = proxy_emb - proxy_drift_component
        
        velocity_scale = 1.0 + max(0.0, drift_velocity)
        perturbation = proxy_clean * gate_value * velocity_scale
        
        return perturbation

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

        Spec §4.4 lines 686-702.
        """
        return agent_context_embedding + perturbation

    async def run(self, state: LearnFlowState) -> LearnFlowState:
        # Reconstruct trigger map from state to get the active drift pattern
        if state.get("trigger_map_state"):
            trigger_map = TriggerMap.from_dict(state["trigger_map_state"])
        else:
            trigger_map = TriggerMap("orchestrator", "student")
            
        drift_direction = trigger_map.get_trigger_pattern()
        
        # Run independent proxy task
        proxy_output = await self.run_proxy_task(
            student_query=state.get("current_input", ""),
            drift_direction=drift_direction,
            pattern_coherence=trigger_map.pattern_coherence
        )
        
        # Compute velocity if history exists
        drift_velocity = 0.0
        if state.get("proxy_context_window"):
            scores = [m.get("score", 0.0) for m in state["proxy_context_window"] if "score" in m]
            if len(scores) >= 2:
                drift_velocity = scores[-1] - scores[-2]
                
        # Compute perturbation
        gate_value = state.get("gate_value", 0.0)
        perturbation = self.compute_perturbation(
            proxy_output=proxy_output,
            drift_direction=drift_direction,
            gate_value=gate_value,
            drift_velocity=drift_velocity
        )
        
        # Inject perturbation values back into the state
        state["proxy_reframe"] = proxy_output.content
        state["perturbation_norm"] = float(np.linalg.norm(perturbation))
        
        return state
