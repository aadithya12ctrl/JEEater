from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LearnFlowState

CLOSURE_SYSTEM_PROMPT = """\
You are a closure verifier for JEE/NEET concepts.

THE DISTINCTION YOU ENFORCE:
COVERED = student can state the concept
CLOSED = student can explain WHY the concept takes the form it does

CLOSURE QUESTIONS (use these, not MCQs):
- "In your own words — why does [concept] work this way?"
- "What would break if [key assumption] weren't true?"
- "How would you explain this to someone who's never seen the formula?"
- "What's the difference between this situation and [structurally similar situation]?"

COVERED VS CLOSED DETECTOR:
Student says "F=ma comes from Newton's second law" → COVERED
Student says "F=ma comes from rate of change of momentum, and we write it this way \
because JEE exploits the differential form dp/dt in non-constant mass problems" → CLOSED

RESPONSE FORMAT:
State clearly: COVERED or CLOSED
If COVERED: give the specific follow-up question that targets the gap
If CLOSED: confirm and identify the next concept that builds on this one

ANTI-DRIFT: You are not a cheerleader. "Good explanation!" without a COVERED/CLOSED \
verdict is not a valid response.
"""

class ClosureAgent:
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: LearnFlowState) -> LearnFlowState:
        concept = state.get("current_chapter", "this concept")
        
        prompt = f"""
        Concept to verify: {concept}
        Student's latest response: {state['current_input']}
        
        Evaluate whether the student has reached genuine CLOSURE (understands the underlying 'why')
        or only COVERAGE (surface-level formula memorization or stating).
        Provide the response in the specified format with 'verdict: COVERED' or 'verdict: CLOSED' on the first line.
        """
        
        response = await self.llm.ainvoke([
            SystemMessage(content=CLOSURE_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        content = response.content
        state["final_response"] = content
        state["response_agent"] = "closure"
        
        # Parse verdict
        first_line = content.split("\n")[0].upper()
        if "CLOSED" in first_line:
            state["closure_verdict"] = "CLOSED"
        else:
            state["closure_verdict"] = "COVERED"
            
        return state
