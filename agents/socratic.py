from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LearnFlowState

SOCRATIC_SYSTEM_PROMPT = """
You are a Socratic tutor for JEE/NEET preparation. Your ONLY job is to ask questions.

ENTRY PROTOCOL — activate when student is stuck:
Step 1: "What is the problem giving you?" (extract givens)
Step 2: "What is it asking for?" (extract unknowns)  
Step 3: "What connects the two?" (identify the bridge concept)
Step 4: If student can't bridge — show a Visual Opening Move Card (describe it in text)

DIAGRAM GATE — enforce before any calculation:
Before any student proceeds to calculation, they must describe their diagram setup.
Prompt: "Before we calculate anything — describe the setup you'd draw. What does your diagram look like?"
Do NOT unlock calculation until they've described a diagram.

HARD RULES:
- Never state a physics/chemistry/math principle directly.
- Never confirm "yes that's right" without a follow-up question.
- Every response ends with a question.
- If student says "just tell me" — respond: "I understand the frustration. Let's try one more angle — what do you know for certain about this situation?"

ARCHETYPE SIGNATURES (use to guide questions, not to state):
- Newton's Laws → ask about forces, not F=ma
- Energy Conservation → ask about what's changing, not KE/PE formulas
- Kinematics → ask about what the motion looks like, not equations
"""

class SocraticAgent:
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: LearnFlowState) -> LearnFlowState:
        # Check diagram gate first
        is_diagram_gate_passed = state.get("diagram_described", False)
        
        # We can ask the LLM if the student described a diagram in the latest input
        if not is_diagram_gate_passed:
            check_prompt = f"""
            Did the student describe a physical diagram or geometric/physical setup in this message?
            Message: {state['current_input']}
            Answer YES or NO only.
            """
            check_response = await self.llm.ainvoke(check_prompt)
            if "YES" in check_response.content.upper():
                state["diagram_described"] = True
                is_diagram_gate_passed = True

        prompt = SOCRATIC_SYSTEM_PROMPT
        if not is_diagram_gate_passed:
            prompt += "\n\nCRITICAL: The student has NOT passed the Diagram Gate yet. You must guide them to describe the visual/diagrammatic setup of the problem."
        else:
            prompt += "\n\nNote: The Diagram Gate is PASSED. You can now transition to helping them build the connection to calculation, but keep the Socratic method."

        messages = [SystemMessage(content=prompt)]
        
        # Feed the message history
        for msg in state.get("message_history", [])[-6:]:
            if hasattr(msg, "content"):
                messages.append(msg)
            elif isinstance(msg, dict) and "content" in msg:
                messages.append(HumanMessage(content=msg["content"]))
                
        # Append current input
        messages.append(HumanMessage(content=state["current_input"]))
        
        response = await self.llm.ainvoke(messages)
        
        state["final_response"] = response.content
        state["response_agent"] = "socratic"
        state["socratic_rounds"] = state.get("socratic_rounds", 0) + 1
        
        return state
