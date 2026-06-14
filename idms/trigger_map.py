import os
import time
import numpy as np
from typing import Any, Dict, List, Optional

# Safe import / fallback for sentence_transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

class MockEmbeddingModel:
    def encode(self, text: str) -> np.ndarray:
        # Generate a deterministic pseudo-random embedding of dim 384 based on text hash
        state = np.random.RandomState(abs(hash(text)) % (2**32))
        emb = state.normal(0, 1, 384)
        norm = np.linalg.norm(emb)
        if norm > 1e-8:
            emb /= norm
        return emb

class TriggerEvent:
    def __init__(self, trigger: str, trigger_emb: np.ndarray, score: float, deviation_vector: np.ndarray, timestamp: float):
        self.trigger = trigger
        self.trigger_emb = trigger_emb
        self.score = score
        self.deviation_vector = deviation_vector
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger": self.trigger,
            "trigger_emb": self.trigger_emb.tolist(),
            "score": self.score,
            "deviation_vector": self.deviation_vector.tolist(),
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerEvent":
        return cls(
            trigger=data["trigger"],
            trigger_emb=np.array(data["trigger_emb"]),
            score=data["score"],
            deviation_vector=np.array(data["deviation_vector"]),
            timestamp=data["timestamp"]
        )

class TriggerMap:
    def __init__(self, agent_a_role: str, agent_b_role: str):
        self.agent_a_role = agent_a_role
        self.agent_b_role = agent_b_role
        self.trigger_history: List[TriggerEvent] = []
        self.pattern_coherence: float = 1.0
        
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.embedding_model = SentenceTransformer(model_name)
            except Exception:
                self.embedding_model = MockEmbeddingModel()
        else:
            self.embedding_model = MockEmbeddingModel()
            
        self.role_baseline: Optional[np.ndarray] = None
    
    def set_role_baseline(self, role_specification: str):
        self.role_baseline = self.embedding_model.encode(role_specification)
    
    def compute_residual_score(
        self,
        agent_b_output: str,
        agent_a_actual_response: str,
    ) -> float:
        if self.role_baseline is None:
            self.role_baseline = self.embedding_model.encode(self.agent_a_role)
        
        actual_emb = self.embedding_model.encode(agent_a_actual_response)
        trigger_emb = self.embedding_model.encode(agent_b_output)
        
        deviation_vector = actual_emb - self.role_baseline
        role_deviation = float(np.linalg.norm(deviation_vector))
        
        if role_deviation > 1e-6:
            deviation_normalized = deviation_vector / role_deviation
            trigger_norm = np.linalg.norm(trigger_emb)
            if trigger_norm > 1e-8:
                trigger_normalized = trigger_emb / trigger_norm
            else:
                trigger_normalized = trigger_emb
            trigger_alignment = float(np.dot(trigger_normalized, deviation_normalized))
        else:
            trigger_alignment = 0.0
        
        residual = float(role_deviation * max(0.0, trigger_alignment))
        
        self.trigger_history.append(TriggerEvent(
            trigger=agent_b_output,
            trigger_emb=trigger_emb,
            score=residual,
            deviation_vector=deviation_vector,
            timestamp=time.time()
        ))
        
        return residual
    
    def get_trigger_pattern(self) -> np.ndarray:
        if len(self.trigger_history) < 3:
            return np.zeros(384)
        
        trigger_embs = [
            e.trigger_emb * e.score
            for e in self.trigger_history[-10:]
        ]
        stacked = np.stack(trigger_embs)
        
        try:
            U, S, Vt = np.linalg.svd(stacked, full_matrices=False)
            dominant_direction = Vt[0]
            explained_variance_ratio = S[0]**2 / (np.sum(S**2) + 1e-8)
            self.pattern_coherence = float(explained_variance_ratio)
        except Exception:
            dominant_direction = np.mean(stacked, axis=0)
            norm = np.linalg.norm(dominant_direction)
            if norm > 1e-8:
                dominant_direction /= norm
            self.pattern_coherence = 0.5
        
        return dominant_direction
    
    def get_top_triggers(self, n: int = 3) -> List[TriggerEvent]:
        return sorted(self.trigger_history, key=lambda e: e.score, reverse=True)[:n]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_a_role": self.agent_a_role,
            "agent_b_role": self.agent_b_role,
            "trigger_history": [e.to_dict() for e in self.trigger_history],
            "pattern_coherence": self.pattern_coherence,
            "role_baseline": self.role_baseline.tolist() if self.role_baseline is not None else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerMap":
        tm = cls(data["agent_a_role"], data["agent_b_role"])
        tm.pattern_coherence = data.get("pattern_coherence", 1.0)
        if data.get("role_baseline") is not None:
            tm.role_baseline = np.array(data["role_baseline"])
        tm.trigger_history = [TriggerEvent.from_dict(e) for e in data.get("trigger_history", [])]
        return tm
