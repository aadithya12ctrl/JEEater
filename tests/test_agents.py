import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from graph.state import LearnFlowState
from agents.socratic import SocraticAgent
from agents.gap_explainer import GapExplainerAgent
from agents.closure import ClosureAgent
from agents.cinema import ConceptCinemaAgent
from agents.anti_overing import AntiOveringAgent

# Helper Mock response
class MockResponse:
    def __init__(self, content):
        self.content = content

class TestAgents(unittest.TestCase):
    def setUp(self):
        self.llm = AsyncMock()

    def test_socratic_agent_diagram_gate_passed(self):
        # Setup mock LLM behavior
        # First call is for checking if diagram is described (returns YES)
        # Second call is for generating the Socratic question
        self.llm.ainvoke.side_effect = [
            MockResponse("YES"),
            MockResponse("How does gravity act here?")
        ]
        
        agent = SocraticAgent(self.llm)
        state: LearnFlowState = {
            "session_id": "test_sess",
            "current_input": "I've drawn a block on a 30 degree incline slide with friction",
            "diagram_described": False,
            "message_history": [],
            "socratic_rounds": 0
        }
        
        loop = asyncio.get_event_loop()
        updated_state = loop.run_until_complete(agent.run(state))
        
        self.assertTrue(updated_state["diagram_described"])
        self.assertEqual(updated_state["final_response"], "How does gravity act here?")
        self.assertEqual(updated_state["socratic_rounds"], 1)

    def test_socratic_agent_diagram_gate_failed(self):
        # Returns NO for diagram check, then asks to describe setup
        self.llm.ainvoke.side_effect = [
            MockResponse("NO"),
            MockResponse("Please draw or describe the visual setup before calculating.")
        ]
        
        agent = SocraticAgent(self.llm)
        state: LearnFlowState = {
            "session_id": "test_sess",
            "current_input": "I don't know the formula for acceleration",
            "diagram_described": False,
            "message_history": [],
            "socratic_rounds": 0
        }
        
        loop = asyncio.get_event_loop()
        updated_state = loop.run_until_complete(agent.run(state))
        
        self.assertFalse(updated_state["diagram_described"])
        self.assertEqual(updated_state["final_response"], "Please draw or describe the visual setup before calculating.")

    def test_gap_explainer_agent(self):
        # Mock problem database
        prob_db = MagicMock()
        problem = MagicMock()
        problem.problem_text = "Block on accelerating elevator"
        problem.standard_solution = "Find normal force using pseudo-forces."
        prob_db.get.return_value = problem
        
        self.llm.ainvoke.return_value = MockResponse(
            "**WHAT YOU KNEW**\nForces on static frames.\n\n**THE GAP**\nMissed elevator acceleration direction.\n\n**WHAT IT UNLOCKED**\nCorrect FBD setup."
        )
        
        agent = GapExplainerAgent(self.llm, prob_db)
        state: LearnFlowState = {
            "current_problem": "prob_1",
            "current_input": "I wrote N = mg.",
            "final_response": "",
            "response_agent": ""
        }
        
        loop = asyncio.get_event_loop()
        updated_state = loop.run_until_complete(agent.run(state))
        
        self.assertIn("**THE GAP**", updated_state["final_response"])
        self.assertEqual(updated_state["response_agent"], "gap_explainer")

    def test_closure_agent_covered(self):
        self.llm.ainvoke.return_value = MockResponse("verdict: COVERED\nWhy does vertical acceleration change the weight?")
        agent = ClosureAgent(self.llm)
        
        state: LearnFlowState = {
            "current_chapter": "Laws of Motion",
            "current_input": "F=ma",
            "closure_verdict": None
        }
        
        loop = asyncio.get_event_loop()
        updated_state = loop.run_until_complete(agent.run(state))
        self.assertEqual(updated_state["closure_verdict"], "COVERED")

    def test_closure_agent_closed(self):
        self.llm.ainvoke.return_value = MockResponse("verdict: CLOSED\nAwesome, that's exactly why!")
        agent = ClosureAgent(self.llm)
        
        state: LearnFlowState = {
            "current_chapter": "Laws of Motion",
            "current_input": "Because the inertial frame requires pseudo-force -ma to balance the acceleration of the elevator",
            "closure_verdict": None
        }
        
        loop = asyncio.get_event_loop()
        updated_state = loop.run_until_complete(agent.run(state))
        self.assertEqual(updated_state["closure_verdict"], "CLOSED")

    def test_concept_cinema_beat_progression(self):
        self.llm.ainvoke.return_value = MockResponse("Why does skater speed up? [Beat 1]")
        agent = ConceptCinemaAgent(self.llm)
        
        state: LearnFlowState = {
            "current_chapter": "Angular Momentum",
            "active_beat": 1,
            "beat_awaiting_response": False
        }
        
        loop = asyncio.get_event_loop()
        updated_state = loop.run_until_complete(agent.run(state))
        self.assertEqual(updated_state["active_beat"], 2)
        self.assertFalse(updated_state["beat_awaiting_response"])

    def test_concept_cinema_beat_checkpoint_gate_passed(self):
        # Beat 3 evaluate returns ADEQUATE
        # Then next call generates beat 4/5 content
        self.llm.ainvoke.side_effect = [
            MockResponse("ADEQUATE - Student explained conservation of momentum correctly"),
            MockResponse("Here is the formula: L = I * w [Beat 4 formalism]")
        ]
        agent = ConceptCinemaAgent(self.llm)
        
        state: LearnFlowState = {
            "current_chapter": "Angular Momentum",
            "active_beat": 3,
            "beat_awaiting_response": True,
            "current_input": "Because bringing arms in reduces moment of inertia, so w must increase to conserve L."
        }
        
        loop = asyncio.get_event_loop()
        updated_state = loop.run_until_complete(agent.run(state))
        self.assertEqual(updated_state["active_beat"], 5)
        self.assertFalse(updated_state["beat_awaiting_response"])
        self.assertIn("L = I * w", updated_state["final_response"])

    def test_anti_overing_agent_procedure_success(self):
        prob_db = MagicMock()
        agent = AntiOveringAgent(self.llm, prob_db)
        
        self.llm.ainvoke.return_value = MockResponse("verdict: PROCEDURE SUCCESS / PRINCIPLE FAILURE\nYou got the answer right, but explain why you selected energy methods.")
        
        state: LearnFlowState = {
            "current_problem": "prob_1",
            "current_input": "I got 5 m/s by plugging into conservation of energy.",
            "anti_overing_verdict": None
        }
        
        loop = asyncio.get_event_loop()
        updated_state = loop.run_until_complete(agent.run(state))
        self.assertEqual(updated_state["anti_overing_verdict"], "PROCEDURE_SUCCESS_PRINCIPLE_FAILURE")

if __name__ == "__main__":
    unittest.main()
