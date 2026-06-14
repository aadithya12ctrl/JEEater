import numpy as np

class InputDependentGate:
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
        
        drift_norm_val = np.linalg.norm(drift_direction)
        if drift_norm_val > 1e-8:
            drift_norm = drift_direction / drift_norm_val
        else:
            drift_norm = drift_direction
            
        input_norm_val = np.linalg.norm(input_emb)
        if input_norm_val > 1e-8:
            input_norm = input_emb / input_norm_val
        else:
            input_norm = input_emb
        
        # Signal 1: Input-drift alignment [0, 1]
        raw_alignment = float(np.dot(input_norm, drift_norm))
        alignment = max(0.0, raw_alignment)
        
        # Signal 2: Velocity contribution
        velocity_contribution = max(0.0, drift_velocity) * 0.3
        
        # Signal 3: Coherence scaling
        coherence_scale = 0.5 + 0.5 * pattern_coherence  # [0.5, 1.0]
        
        # Combined signal
        combined = (alignment + velocity_contribution) * coherence_scale
        
        # Sigmoid gate
        sensitivity = self.base_sensitivity * coherence_scale
        gate = 1.0 / (1.0 + np.exp(-sensitivity * (combined - 0.5)))
        
        return float(gate)
    
    def gate_with_hysteresis(
        self,
        current_gate: float,
        previous_gate: float,
        hysteresis: float = 0.1
    ) -> float:
        if current_gate < previous_gate - hysteresis:
            return current_gate
        elif current_gate > previous_gate:
            return current_gate
        else:
            return previous_gate
