import os
import json
import time
from dataclasses import dataclass, asdict
from typing import List
import numpy as np

@dataclass
class DriftEvent:
    session_id: str
    timestamp: float
    drift_magnitude: float
    trigger_pattern_direction: np.ndarray  # dominant PCA direction
    gate_value: float
    proxy_perturbation_norm: float
    agents_affected: List[str]
    anchors_applied: List[str]
    post_intervention_asi: float  # measured 3 turns later

    def to_dict(self) -> dict:
        data = asdict(self)
        if isinstance(self.trigger_pattern_direction, np.ndarray):
            data["trigger_pattern_direction"] = self.trigger_pattern_direction.tolist()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "DriftEvent":
        direction = data.get("trigger_pattern_direction")
        if direction is not None:
            data["trigger_pattern_direction"] = np.array(direction)
        return cls(**data)


class DriftLogger:
    """
    Logs drift events to a JSON Lines or JSON file for analysis and auditing.
    Matches the drift event logging requirements in spec §10 (lines 1540-1556).
    """
    def __init__(self, log_filepath: str = "drift_events.json"):
        self.log_filepath = log_filepath

    def log_event(self, event: DriftEvent):
        """Append a DriftEvent to the log file."""
        event_dict = event.to_dict()
        # Ensure timestamp is set if not provided
        if not event_dict.get("timestamp"):
            event_dict["timestamp"] = time.time()
            
        try:
            # We append as a single JSON line to avoid loading the whole file each time
            with open(self.log_filepath, "a") as f:
                f.write(json.dumps(event_dict) + "\n")
        except Exception as e:
            # Fallback to standard print logging in case of file issues
            print(f"[DriftLogger Error] Failed to log drift event: {e}")
            print(f"[DriftLogger Fallback] Drift Event: {event_dict}")

    def load_events(self, session_id: str = None) -> List[DriftEvent]:
        """Load logged drift events, optionally filtered by session_id."""
        if not os.path.exists(self.log_filepath):
            return []
            
        events = []
        try:
            with open(self.log_filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    event_data = json.loads(line)
                    if session_id is None or event_data.get("session_id") == session_id:
                        events.append(DriftEvent.from_dict(event_data))
        except Exception as e:
            print(f"[DriftLogger Error] Failed to load drift events: {e}")
        return events
