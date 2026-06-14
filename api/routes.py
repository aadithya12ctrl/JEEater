import asyncio
import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from data.models import SessionLocal, SessionModel, Student

router = APIRouter()

class SessionStartRequest(BaseModel):
    student_id: str
    chapter: str
    problem_id: str | None = None

class MessageRequest(BaseModel):
    session_id: str
    text: str

@router.post("/session/start")
def start_session(req: SessionStartRequest):
    session_db = SessionLocal()
    try:
        student = session_db.query(Student).filter(Student.id == req.student_id).first()
        if not student:
            student = Student(id=req.student_id)
            session_db.add(student)
            session_db.commit()
            
        session_id = f"sess_{req.student_id}_{int(asyncio.get_event_loop().time())}"
        session_obj = SessionModel(
            id=session_id,
            student_id=req.student_id,
            state_json={
                "session_id": session_id,
                "student_id": req.student_id,
                "current_chapter": req.chapter,
                "current_problem": req.problem_id,
                "message_history": [],
                "current_input": "",
                "next_agent": "orchestrator",
                "active_beat": 1,
                "beat_awaiting_response": False,
                "diagram_described": False,
                "drift_detected": False,
                "drift_magnitude": 0.0,
                "gate_value": 0.0,
                "closure_verdict": None,
                "anti_overing_verdict": None,
                "socratic_rounds": 0,
                "profile_summary": {},
                "revision_queue": [],
                "hint_density": "medium",
                "final_response": "",
                "response_agent": ""
            }
        )
        session_db.add(session_obj)
        session_db.commit()
        return {"session_id": session_id}
    finally:
        session_db.close()

@router.post("/session/message")
async def send_message(req: MessageRequest, request: Request):
    session_db = SessionLocal()
    try:
        session_obj = session_db.query(SessionModel).filter(SessionModel.id == req.session_id).first()
        if not session_obj:
            raise HTTPException(status_code=404, detail="Session not found")
            
        state = session_obj.state_json
        state["current_input"] = req.text
        
        # Get workflow from app state to avoid circular imports
        workflow = request.app.state.workflow
        
        # Run workflow via LangGraph
        config = {"configurable": {"thread_id": req.session_id}}
        final_state = await workflow.ainvoke(state, config)
        
        # Save state
        session_obj.state_json = dict(final_state)
        session_db.add(session_obj)
        session_db.commit()
        
        # SSE Generator
        async def event_generator():
            # Send live metrics
            yield f"data: {json.dumps({'type': 'metrics', 'drift': final_state.get('drift_magnitude', 0.0), 'gate': final_state.get('gate_value', 0.0), 'active_agent': final_state.get('response_agent')})}\n\n"
            
            # Stream final response word by word
            words = final_state.get("final_response", "").split(" ")
            for w in words:
                yield f"data: {json.dumps({'type': 'token', 'token': w + ' '})}\n\n"
                await asyncio.sleep(0.04)
                
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
        
    finally:
        session_db.close()
