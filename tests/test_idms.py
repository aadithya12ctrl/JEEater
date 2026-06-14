import unittest
import numpy as np
from idms.proxy_context_window import ProxyContextWindow
from idms.trigger_map import TriggerMap
from idms.decomposition import decompose, recover, drift_magnitude_scalar
from idms.gate import InputDependentGate

class TestIDMS(unittest.TestCase):
    def test_proxy_context_window_sliding(self):
        pcw = ProxyContextWindow(drift_threshold=0.72, noise_tolerance=0.15)
        # Add stable scores
        for i in range(5):
            pcw.add({"content": f"msg {i}"}, 0.2)
        
        self.assertEqual(len(pcw.window), 5)
        self.assertAlmostEqual(pcw.drift_signal, 0.2)
        self.assertAlmostEqual(pcw.drift_velocity, 0.0)
        
        # Add sudden drift divergence score to break the episode
        pcw.add({"content": "divergent msg"}, 0.8)
        # Window resets on episode break
        self.assertEqual(len(pcw.window), 1)
        self.assertEqual(pcw.episode_count, 1)

    def test_latent_decomposition(self):
        # 384 dimensions
        rep = np.random.randn(384)
        drift_dir = np.random.randn(384)
        
        clean, drift = decompose(rep, drift_dir)
        recovered = recover(clean, drift)
        
        # Lossless check
        np.testing.assert_array_almost_equal(rep, recovered)
        
        # Orthogonality check: dot product of clean component and normalized drift direction should be 0
        drift_norm = drift_dir / np.linalg.norm(drift_dir)
        dot_prod = np.dot(clean, drift_norm)
        self.assertAlmostEqual(dot_prod, 0.0, places=5)
        
        # Signed scalar projection check
        proj = drift_magnitude_scalar(rep, drift_dir)
        self.assertAlmostEqual(proj, np.dot(rep, drift_norm), places=5)

    def test_input_dependent_gate(self):
        class MockModel:
            def encode(self, text):
                # Return constant vector for simple tests
                return np.ones(384) / np.sqrt(384)
                
        model = MockModel()
        gate = InputDependentGate(model)
        
        drift_dir = np.ones(384) / np.sqrt(384)
        # Test compute
        val = gate.compute("some input", drift_dir, drift_velocity=0.1, pattern_coherence=0.8)
        self.assertTrue(0.0 <= val <= 1.0)
        
        # Test hysteresis
        h1 = gate.gate_with_hysteresis(current_gate=0.5, previous_gate=0.55, hysteresis=0.1)
        self.assertEqual(h1, 0.55) # within hysteresis, keep previous
        
        h2 = gate.gate_with_hysteresis(current_gate=0.3, previous_gate=0.55, hysteresis=0.1)
        self.assertEqual(h2, 0.3) # dropped past hysteresis, update

if __name__ == '__main__':
    unittest.main()
