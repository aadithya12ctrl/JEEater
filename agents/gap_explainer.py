from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LearnFlowState

GAP_EXPLAINER_SYSTEM_PROMPT = """
You are a surgical gap explainer for JEE/NEET solutions.

YOUR ONLY JOB: Explain the specific logical transition that was skipped.

FORMAT — always exactly this structure:
**WHAT YOU KNEW**
[The step the student had correctly]

**THE GAP**  
[The implicit logical move that was skipped. One precise sentence.]

**WHAT IT UNLOCKED**
[What becomes available once the gap is filled]

RULES:
- Never re-explain the full solution
- Never explain steps the student already has
- The gap section must be ONE sentence — if you need more, you've misidentified the gap
- No formulas in the gap section — the gap is always a logical/conceptual move, never algebraic
- If you cannot identify the specific gap from the student's work, ask the orchestrator \
  to route back to the Socratic agent first

ANTI-DRIFT CHECK: Before responding, ask yourself — am I about to re-explain the \
whole solution? If yes, stop and find the single transition instead.
"""

class GapExplainerAgent:
    def __init__(self, llm, problem_db):
        self.llm = llm
        self.problem_db = problem_db

    async def run(self, state: LearnFlowState) -> LearnFlowState:
        prob_id = state.get("current_problem")
        prob = self.problem_db.get(prob_id) if prob_id else None
        
        standard_solution = prob.standard_solution if prob else "No standard solution available."
        problem_text = prob.problem_text if prob else "No problem statement."
        
        gap_prompt = f"""
        Problem: {problem_text}
        Standard solution steps: {standard_solution}
        Student's attempt: {state['current_input']}
        
        Identify the SINGLE logical transition that was skipped.
        Respond in exactly the requested 3-part format.
        """
        
        response = await self.llm.ainvoke([
            SystemMessage(content=GAP_EXPLAINER_SYSTEM_PROMPT),
            HumanMessage(content=gap_prompt)
        ])
        
        state["final_response"] = response.content
        state["response_agent"] = "gap_explainer"
        return state
