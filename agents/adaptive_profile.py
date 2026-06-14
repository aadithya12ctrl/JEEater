import json
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import LearnFlowState
from data.models import SessionLocal, Profile as DbProfile

PROFILE_SYSTEM_PROMPT = """\
You are a silent behavioral analyst. You never interact with the student directly.
You receive signals from all other agents and update the learner profile.

WHAT YOU TRACK:
- Inferred depth: does this student need derivation-first or application-first?
- Breaking points: which logical transitions consistently lose them?
- Explanation style: do follow-up questions indicate preference for logic, analogy, or visual?
- Error patterns: recurring errors (sign conventions, unit errors, wrong frame choice)
- Session pacing: are they rushing or stuck?

PROFILE UPDATE TRIGGERS:
- Student asked a follow-up question → infer what confused them
- Closure agent returned COVERED → record which concept, update gap frequency
- Anti-overing agent flagged PROCEDURE SUCCESS / PRINCIPLE FAILURE → record pattern
- Socratic agent needed >3 rounds to unlock → record breaking point

WHAT YOU OUTPUT (to Orchestrator only):
- study_order_adjustments: list of concepts to reshuffle based on actual gaps
- revision_priority: decay_score * gap_frequency ranked list
- hint_density: {low, medium, high} for current session
- session_pacing: {normal, slow_down, allow_rush}

THE SYSTEM NEVER ASKS THE STUDENT THEIR LEVEL. You infer everything.

Return a valid JSON object with this structure:
{
  "depth_preference": float,
  "known_gaps": list of strings,
  "error_patterns": dict of {string: int},
  "decay_scores": dict of {string: float},
  "gap_frequency": dict of {string: float},
  "hint_density": "low" | "medium" | "high",
  "session_pacing": "normal" | "slow_down" | "allow_rush"
}
Output JSON only. No markdown, no extra text.
"""

class AdaptiveProfileAgent:
    def __init__(self, llm):
        self.llm = llm

    async def update_from_state(self, state: LearnFlowState) -> LearnFlowState:
        student_id = state.get("student_id", "default_student")
        
        # Load profile from DB or make a default one
        db = SessionLocal()
        try:
            profile_model = db.query(DbProfile).filter(DbProfile.student_id == student_id).first()
            if not profile_model:
                profile_model = DbProfile(
                    student_id=student_id,
                    depth_preference=0.5,
                    known_gaps=[],
                    error_patterns={},
                    decay_scores={},
                    gap_frequency={}
                )
                db.add(profile_model)
                db.commit()
                db.refresh(profile_model)
            
            current_profile_dict = {
                "depth_preference": profile_model.depth_preference,
                "known_gaps": profile_model.known_gaps,
                "error_patterns": profile_model.error_patterns,
                "decay_scores": profile_model.decay_scores,
                "gap_frequency": profile_model.gap_frequency
            }
            
            # Synthesize signal
            agent_name = state.get("response_agent", "unknown")
            signal_type = "verdict"
            content = f"Active Agent: {agent_name}. Input: {state.get('current_input')}. Verdicts - Closure: {state.get('closure_verdict')}, Anti-overing: {state.get('anti_overing_verdict')}, Socratic rounds: {state.get('socratic_rounds', 0)}"
            
            prompt = f"""
            Current Profile: {json.dumps(current_profile_dict)}
            New Signal from {agent_name}: {content}
            
            Update the profile based on the new signal. Returns JSON only.
            """
            
            res = await self.llm.ainvoke([
                SystemMessage(content=PROFILE_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ])
            
            raw_content = res.content.strip()
            # Clean potential json formatting backticks
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
            raw_content = raw_content.strip()
            
            updated_dict = json.loads(raw_content)
            
            # Update DB
            profile_model.depth_preference = updated_dict.get("depth_preference", profile_model.depth_preference)
            profile_model.known_gaps = updated_dict.get("known_gaps", profile_model.known_gaps)
            profile_model.error_patterns = updated_dict.get("error_patterns", profile_model.error_patterns)
            profile_model.decay_scores = updated_dict.get("decay_scores", profile_model.decay_scores)
            profile_model.gap_frequency = updated_dict.get("gap_frequency", profile_model.gap_frequency)
            
            db.add(profile_model)
            db.commit()
            
            # Update State
            state["profile_summary"] = updated_dict
            
        except Exception as e:
            print(f"Error in Profile update: {e}")
            # Fallback state sync
            state["profile_summary"] = {
                "depth_preference": 0.5,
                "known_gaps": [],
                "error_patterns": {},
                "decay_scores": {},
                "gap_frequency": {}
            }
        finally:
            db.close()
            
        return state

    async def get_current_profile(self, session_id: str) -> Any:
        # Returns helper class representing profile for routing decisions
        db = SessionLocal()
        try:
            # Simple lookup based on student/session context mapping
            prof = db.query(DbProfile).first() # Fallback to first profile for simple routing
            class ProfileSummary:
                def __init__(self, p):
                    self.summary = f"Depth: {p.depth_preference}, Gaps: {p.known_gaps}, Error patterns: {p.error_patterns}"
            if prof:
                return ProfileSummary(prof)
            return ProfileSummary(DbProfile(depth_preference=0.5, known_gaps=[], error_patterns={}))
        finally:
            db.close()
