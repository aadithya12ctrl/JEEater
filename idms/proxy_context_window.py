from typing import Any, Dict, List

class ProxyContextWindow:
    def __init__(self, drift_threshold: float = 0.72, noise_tolerance: float = 0.15):
        self.drift_threshold = drift_threshold
        self.noise_tolerance = noise_tolerance
        self.window: List[Dict[str, Any]] = []
        self.residual_scores: List[float] = []
        self.episode_count: int = 0       # how many drift episodes this session
        self.episode_lengths: List[int] = []  # length of each past episode
    
    def should_extend(self, new_score: float) -> bool:
        if not self.residual_scores:
            return True
        recent_mean = sum(self.residual_scores[-5:]) / len(self.residual_scores[-5:])
        return abs(new_score - recent_mean) < self.noise_tolerance
    
    def add(self, message: Dict[str, Any], residual_score: float):
        if self.should_extend(residual_score):
            self.window.append(message)
            self.residual_scores.append(residual_score)
        else:
            self.episode_lengths.append(len(self.window))
            self.episode_count += 1
            self.reset(message, residual_score)
    
    def reset(self, seed_message: Dict[str, Any], seed_score: float):
        self.window = [seed_message]
        self.residual_scores = [seed_score]
    
    @property
    def drift_signal(self) -> float:
        if not self.residual_scores:
            return 0.0
        return sum(self.residual_scores) / len(self.residual_scores)
    
    @property
    def drift_velocity(self) -> float:
        if len(self.residual_scores) < 2:
            return 0.0
        n = len(self.residual_scores)
        x = list(range(n))
        x_mean = (n - 1) / 2
        y_mean = self.drift_signal
        numerator = sum((x[i] - x_mean) * (self.residual_scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        return numerator / (denominator + 1e-8)
    
    @property
    def is_accelerating(self) -> bool:
        return self.drift_velocity > 0.05

    def to_dict(self) -> Dict[str, Any]:
        return {
            "drift_threshold": self.drift_threshold,
            "noise_tolerance": self.noise_tolerance,
            "window": self.window,
            "residual_scores": self.residual_scores,
            "episode_count": self.episode_count,
            "episode_lengths": self.episode_lengths
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxyContextWindow":
        pcw = cls(
            drift_threshold=data.get("drift_threshold", 0.72),
            noise_tolerance=data.get("noise_tolerance", 0.15)
        )
        pcw.window = data.get("window", [])
        pcw.residual_scores = data.get("residual_scores", [])
        pcw.episode_count = data.get("episode_count", 0)
        pcw.episode_lengths = data.get("episode_lengths", [])
        return pcw
