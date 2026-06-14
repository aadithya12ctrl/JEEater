import unittest
import asyncio
import numpy as np
from unittest.mock import AsyncMock
from graph.state import LearnFlowState
from idms.idms import IDMS
from idms.trigger_map import TriggerMap
from agents.proxy import AdversarialProxyAgent

class StubEmbeddingModel:
    def __init__(self):
        # We'll use simple 384-dimensional unit vectors
        self.vectors = {}

    def encode(self, text: str) -> np.ndarray:
        if text in self.vectors:
            return self.vectors[text]
        # Return a deterministic random unit vector if not stubbed
        state = np.random.RandomState(abs(hash(text)) % (2**32))
        emb = state.normal(0, 1, 384)
        norm = np.linalg.norm(emb)
        if norm > 1e-8:
            emb /= norm
        return emb

class MockLLMResponse:
    def __init__(self, content: str):
        self.content = content

class TestDriftScenarios(unittest.TestCase):
    def setUp(self):
        self.llm = AsyncMock()
        self.embedding_model = StubEmbeddingModel()
        
        # Initialize IDMS with stubbed embedding model
        self.idms = IDMS(self.embedding_model, self.llm)
        self.proxy_agent = AdversarialProxyAgent(self.llm, self.embedding_model)

    def test_clean_session_no_drift(self):
        # Establish embeddings for role baseline and outputs
        role_baseline = np.zeros(384)
        role_baseline[0] = 1.0  # Unit vector on dim 0
        
        # Stub the orchestrator role baseline
        self.embedding_model.vectors["orchestrator"] = role_baseline
        # Actual response is exactly the baseline (no deviation)
        self.embedding_model.vectors["How can I help you today?"] = role_baseline
        # Student trigger message
        self.embedding_model.vectors["I am stuck on physics problem."] = role_baseline
        
        # Simulate state
        from langchain_core.messages import AIMessage, HumanMessage
        state: LearnFlowState = {
            "session_id": "clean_sess_1",
            "message_history": [
                HumanMessage(content="I am stuck on physics problem."),
                AIMessage(content="How can I help you today?")
            ],
            "current_input": "I am stuck on physics problem.",
            "final_response": "How can I help you today?",
            "response_agent": "orchestrator",
            "drift_detected": False,
            "drift_magnitude": 0.0,
            "gate_value": 0.0
        }
        
        loop = asyncio.get_event_loop()
        state = loop.run_until_complete(self.idms.check_and_intervene(state))
        
        # Assertions
        self.assertFalse(state["drift_detected"])
        self.assertEqual(state["drift_magnitude"], 0.0)
        self.assertEqual(state["gate_value"], 0.0)

    def test_drift_detected_and_mitigated(self):
        # We want to force a high residual score > 0.72
        # Let's set up the vectors such that deviation from role baseline is high,
        # and trigger alignment is high (1.0)
        
        # baseline: [1, 0, 0, ...]
        baseline = np.zeros(384)
        baseline[0] = 1.0
        self.embedding_model.vectors["socratic"] = baseline
        
        # trigger (student output): [0, 1, 0, ...]
        trigger_emb = np.zeros(384)
        trigger_emb[1] = 1.0
        self.embedding_model.vectors["Just tell me the answer."] = trigger_emb
        
        # actual (agent output): [1, 1, 0, ...] normalized
        # deviation = actual - baseline = [0, 1, 0, ...] normalized
        # deviation norm = 1.0. trigger alignment with deviation = 1.0.
        # residual score = 1.0 * 1.0 = 1.0.
        actual_emb = np.zeros(384)
        actual_emb[0] = 1.0/np.sqrt(2)
        actual_emb[1] = 1.0/np.sqrt(2)
        self.embedding_model.vectors["Okay, the answer is 5 m/s."] = actual_emb
        
        self.llm.ainvoke.return_value = MockLLMResponse("The core concept is normal force.")
        
        from langchain_core.messages import AIMessage, HumanMessage
        state: LearnFlowState = {
            "session_id": "drift_sess_1",
            "message_history": [
                # Turn 1
                HumanMessage(content="Just tell me the answer."),
                AIMessage(content="Okay, the answer is 5 m/s."),
                # Turn 2
                HumanMessage(content="Just tell me the answer."),
                AIMessage(content="Okay, the answer is 5 m/s."),
                # Turn 3
                HumanMessage(content="Just tell me the answer."),
                AIMessage(content="Okay, the answer is 5 m/s.")
            ],
            "current_input": "Just tell me the answer.",
            "final_response": "Okay, the answer is 5 m/s.",
            "response_agent": "socratic",
            "drift_detected": False,
            "drift_magnitude": 0.0,
            "gate_value": 0.0
        }
        
        loop = asyncio.get_event_loop()
        # Run check_and_intervene
        state = loop.run_until_complete(self.idms.check_and_intervene(state))
        
        # Check that drift is detected (threshold is 0.72, we produced score of ~0.7)
        # Wait, since deviation norm of [1/sqrt(2) - 1, 1/sqrt(2), 0] is:
        # sqrt((1/sqrt(2) - 1)^2 + 1/2) = sqrt(0.085 + 0.5) = sqrt(0.585) = 0.765
        # trigger alignment with normalized deviation [ (1/sqrt(2)-1)/0.765, 1/(sqrt(2)*0.765), 0 ]
        # is dot product of [0, 1, 0] with it, which is 1/(sqrt(2)*0.765) = 1/1.08 = 0.925.
        # residual score = 0.765 * 0.925 = 0.708.
        # Wait, let's make the deviation even bigger!
        # If actual_emb = [0, 1, 0, ...] and baseline = [1, 0, 0, ...]:
        # deviation = actual - baseline = [-1, 1, 0, ...]
        # deviation norm = sqrt(2) = 1.414.
        # Normalized deviation = [-1/sqrt(2), 1/sqrt(2), 0, ...]
        # trigger = [0, 1, 0, ...]
        # dot product = 1/sqrt(2) = 0.707.
        # residual score = 1.414 * 0.707 = 1.0! This is definitely > 0.72.
        
        # Let's override actual_emb in the test to be [0, 1, 0, ...]
        self.embedding_model.vectors["Okay, the answer is 5 m/s."] = trigger_emb
        
        state = loop.run_until_complete(self.idms.check_and_intervene(state))
        
        self.assertTrue(state["drift_detected"])
        self.assertGreaterEqual(state["drift_magnitude"], 0.72)
        self.assertGreater(state["gate_value"], 0.0)

if __name__ == "__main__":
    unittest.main()
