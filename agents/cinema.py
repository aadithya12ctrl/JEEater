from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LearnFlowState

CINEMA_SYSTEM_PROMPT = """
You are a concept explainer for JEE/NEET. You explain concepts in 5 beats, always in order.

BEAT 1 — THE INTUITION HOOK
One sentence that makes the student FEEL the concept before any formula.
Must be a question or a surprising observation. No math.
Example: "Why does a spinning skater speed up when they pull their arms in?"

BEAT 2 — THE ANALOGY BRIDGE  
A concrete structural analogy that maps the concept to something familiar.
The analogy must be structural (same mathematical relationship), not superficial.
Example: "Think of momentum as a budget — the total budget never changes."

BEAT 3 — THE CHECKPOINT
An open question requiring reconstruction in the student's own words.
Do NOT proceed to Beat 4 until the student responds adequately.
Example: "In your own words — why does the skater spin faster?"

BEAT 4 — THE FORMALISM
The formula arrives here, and only here.
Introduce it as "here's the language for what we just described."

BEAT 5 — THE WHY-THIS-FORM
Explain the logic of the mathematical form. Why this form specifically?
How does JEE exploit differences in this form across problem types?

HARD RULE: Beats are sequential. Beat 3 requires an adequate student response before Beat 4 unlocks.
The formula must not appear before Beat 4.
"""

class ConceptCinemaAgent:
    def __init__(self, llm):
        self.llm = llm

    async def run(self, state: LearnFlowState) -> LearnFlowState:
        current_beat = state.get("active_beat", 1)
        if current_beat is None:
            current_beat = 1
            
        student_input = state.get("current_input", "")
        chapter = state.get("current_chapter", "this concept")
        
        # If at Beat 3 and waiting for checkpoint evaluation
        if current_beat == 3 and state.get("beat_awaiting_response", False):
            eval_prompt = f"""
            Evaluate the student's response to the checkpoint question for the concept '{chapter}'.
            Student's response: {student_input}
            
            Determine if the explanation shows they grasp the physical intuition.
            Answer ADEQUATE or INADEQUATE on the first line. Followed by a brief explanation.
            """
            eval_res = await self.llm.ainvoke(eval_prompt)
            if "ADEQUATE" in eval_res.content.split("\n")[0].upper():
                state["active_beat"] = 4
                current_beat = 4
                state["beat_awaiting_response"] = False
            else:
                # Re-ask Beat 3 with a different framing
                reframe_prompt = f"""
                Concept: {chapter}
                Student's attempt: {student_input}
                Reason it was inadequate: {eval_res.content}
                
                Ask a clarifying question to steer them towards the correct intuition, without giving the answer.
                """
                reframe_res = await self.llm.ainvoke([
                    SystemMessage(content=CINEMA_SYSTEM_PROMPT),
                    HumanMessage(content=reframe_prompt)
                ])
                state["final_response"] = reframe_res.content
                state["response_agent"] = "cinema"
                return state

        # Generate response for the active beat
        beat_instruction = f"""
        We are currently at BEAT {current_beat} of explaining '{chapter}'.
        Generate the content for Beat {current_beat} only.
        
        If current_beat is 3: stop after writing the checkpoint question. Do not output anything for Beat 4 or 5.
        If current_beat is 4: output Beat 4 and transition to Beat 5.
        """
        
        messages = [
            SystemMessage(content=CINEMA_SYSTEM_PROMPT),
            HumanMessage(content=beat_instruction)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        state["final_response"] = response.content
        state["response_agent"] = "cinema"
        
        if current_beat == 3:
            state["beat_awaiting_response"] = True
        elif current_beat >= 4:
            state["active_beat"] = 5
            state["beat_awaiting_response"] = False
        else:
            state["active_beat"] = current_beat + 1
            state["beat_awaiting_response"] = False
            
        return state
