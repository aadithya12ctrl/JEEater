import random
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LearnFlowState

ANTI_OVERING_SYSTEM_PROMPT = """
You are a generalization trainer for JEE/NEET. Your job is to break procedure-dependent thinking and build principle-based reasoning.

THREE TOOLS — use the most appropriate one:

1. WRONG PATH SIMULATOR
Show a common procedural mistake and ask the student to identify where the logic breaks.
"Here's a solution that gets the wrong answer. Find the step where the reasoning fails."
Focus on non-inertial frames, sign convention errors, incorrect free body diagrams.

2. STRUCTURAL TRANSFER  
Pair two problems that are structurally identical but look completely different.
Explain that they are the same problem in disguise and ask: "What's the shared structure?"
The student must identify the underlying principle, not the surface similarity.

3. METACOGNITIVE REVIEW (use post-solution)
Ask the student to explain their approach SELECTION, not their execution.
"What signal in the problem made you choose energy conservation over momentum?"

RIGHT ANSWER / WRONG METHOD DETECTION:
If the student reached a correct answer but cannot explain why they chose that method, identify this as:
verdict: PROCEDURE SUCCESS / PRINCIPLE FAILURE
This is the most dangerous failure mode — it feels like mastery but isn't.
Otherwise, if they show sound method selection, identify:
verdict: PRINCIPLE CLOSED

ANTI-DRIFT: If you are about to say "great job" to a correct answer without \
asking about method selection — you are drifting. Stop.
"""

class AntiOveringAgent:
    def __init__(self, llm, problem_db):
        self.llm = llm
        self.problem_db = problem_db

    async def run(self, state: LearnFlowState) -> LearnFlowState:
        prob_id = state.get("current_problem")
        
        # Decide which tool to use
        tool_choice = random.choice(["WRONG_PATH", "STRUCTURAL_TRANSFER", "METACOGNITIVE"])
        
        twin_text = ""
        if tool_choice == "STRUCTURAL_TRANSFER" and prob_id:
            try:
                twin = self.problem_db.get_structural_twin(prob_id)
                twin_text = f"\n\nHere is a structurally twin problem to compare with:\n{twin.problem_text}"
            except Exception:
                tool_choice = "WRONG_PATH"
                
        prompt = f"""
        Current problem: {state.get('current_problem', 'general physics problem')}
        Student input: {state['current_input']}
        
        Selected tool strategy: {tool_choice}
        {twin_text}
        
        Generate an anti-overing response. If the student solved the problem, run a Metacognitive Review or evaluate their methodology.
        If they solved it correctly but with poor reasoning, start your response with 'verdict: PROCEDURE SUCCESS / PRINCIPLE FAILURE'.
        Otherwise, if they showed sound principle, start with 'verdict: PRINCIPLE CLOSED'.
        If just asking them to find a wrong path or compare structural twins, do not output a verdict.
        """
        
        response = await self.llm.ainvoke([
            SystemMessage(content=ANTI_OVERING_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        content = response.content
        state["final_response"] = content
        state["response_agent"] = "anti_overing"
        
        # Parse verdict
        if "PROCEDURE SUCCESS" in content:
            state["anti_overing_verdict"] = "PROCEDURE_SUCCESS_PRINCIPLE_FAILURE"
        elif "PRINCIPLE CLOSED" in content:
            state["anti_overing_verdict"] = "CLOSED"
        else:
            state["anti_overing_verdict"] = None
            
        return state
