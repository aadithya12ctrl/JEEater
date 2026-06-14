import numpy as np

def decompose(representation: np.ndarray, drift_direction: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    drift_norm = np.linalg.norm(drift_direction)
    if drift_norm > 1e-8:
        drift_direction_norm = drift_direction / drift_norm
    else:
        drift_direction_norm = drift_direction
    
    drift_magnitude = np.dot(representation, drift_direction_norm)
    drift_component = drift_magnitude * drift_direction_norm
    clean_component = representation - drift_component
    
    return clean_component, drift_component

def recover(clean_component: np.ndarray, drift_component: np.ndarray) -> np.ndarray:
    return clean_component + drift_component

def drift_magnitude_scalar(representation: np.ndarray, drift_direction: np.ndarray) -> float:
    drift_norm = np.linalg.norm(drift_direction)
    if drift_norm > 1e-8:
        drift_direction_norm = drift_direction / drift_norm
    else:
        drift_direction_norm = drift_direction
    return float(np.dot(representation, drift_direction_norm))
