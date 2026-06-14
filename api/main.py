import os
import json
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Safe LangChain imports with Mock fallbacks
try:
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

from data.models import init_db, SessionLocal, SessionModel, Student
from data.problem_db import ProblemDatabase, seed_database
from idms.idms import IDMS
from idms.trigger_map import MockEmbeddingModel
from agents.orchestrator import OrchestratorAgent
from agents.socratic import SocraticAgent
from agents.gap_explainer import GapExplainerAgent
from agents.closure import ClosureAgent
from agents.cinema import ConceptCinemaAgent
from agents.anti_overing import AntiOveringAgent
from agents.adaptive_profile import AdaptiveProfileAgent
from graph.builder import build_learnflow_graph, AgentRegistry

app = FastAPI(title="LearnFlow Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MockLLMResponse:
    def __init__(self, content: str):
        self.content = content

class MockLLM:
    async def ainvoke(self, messages: Any) -> MockLLMResponse:
        # Simple simulated responses based on system prompt / query contents
        prompt_str = ""
        user_str = ""
        if isinstance(messages, list):
            for m in messages:
                if hasattr(m, "content"):
                    if "tutor" in m.content or "Socratic" in m.content:
                        prompt_str = "socratic"
                    elif "gap" in m.content or "surgical" in m.content:
                        prompt_str = "gap"
                    elif "closure" in m.content or "verifier" in m.content:
                        prompt_str = "closure"
                    elif "cinema" in m.content or "beats" in m.content:
                        prompt_str = "cinema"
                    elif "generalization" in m.content or "anti_overing" in m.content:
                        prompt_str = "anti_overing"
                    elif "coordinator" in m.content:
                        prompt_str = "orchestrator"
                    elif "analyst" in m.content:
                        prompt_str = "profile"
                    
                    if "Student input" in m.content or "Student's attempt" in m.content:
                        user_str = m.content
        else:
            if "route" in str(messages) or "specialist" in str(messages):
                prompt_str = "orchestrator"
            user_str = str(messages)

        if prompt_str == "orchestrator":
            # Simple routing logic
            user_lower = user_str.lower()
            if "stuck" in user_lower or "start" in user_lower or "don't know" in user_lower:
                return MockLLMResponse("socratic")
            elif "solution" in user_lower or "attempt" in user_lower:
                return MockLLMResponse("gap_explainer")
            elif "understand" in user_lower or "know why" in user_lower:
                return MockLLMResponse("closure")
            elif "concept" in user_lower or "explain" in user_lower:
                return MockLLMResponse("cinema")
            else:
                return MockLLMResponse("anti_overing")
                
        elif prompt_str == "socratic":
            return MockLLMResponse("Interesting! What forces do you see acting on this body? Describe the setup before calculating.")
            
        elif prompt_str == "gap":
            return MockLLMResponse("**WHAT YOU KNEW**\nYou correctly identified the force components on the incline.\n\n**THE GAP**\nYou assumed the normal force is always m*g*cos(theta), skipping the elevator's vertical acceleration component.\n\n**WHAT IT UNLOCKED**\nFilling this gap allows you to set up the correct pseudo-force equation along the vertical axis.")
            
        elif prompt_str == "closure":
            return MockLLMResponse("verdict: COVERED\nThat is a good definition, but in your own words, why does the elevator's upward acceleration increase the effective gravity?")
            
        elif prompt_str == "cinema":
            return MockLLMResponse("Imagine being in an elevator that suddenly shoots upward. You feel pressed into the floor, right? This is the intuition of pseudo-forces. Why does this acceleration feel like extra gravity? (Beat 3 checkpoint - explain in your own words)")
            
        elif prompt_str == "anti_overing":
            return MockLLMResponse("verdict: PRINCIPLE CLOSED\nYour selection of the energy conservation method is sound because external non-conservative forces do zero work.")
            
        elif prompt_str == "profile":
            return MockLLMResponse(json.dumps({
                "depth_preference": 0.6,
                "known_gaps": ["pseudo-forces in vertical frames"],
                "error_patterns": {"vertical_frames": 1},
                "decay_scores": {"laws_of_motion": 0.8},
                "gap_frequency": {"laws_of_motion": 0.3}
            }))
            
        return MockLLMResponse("I see. Let's look closer at the physical principles at play here.")

# LLM Selection
if os.getenv("LLM_API_KEY"):
    llm = ChatOpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        model=os.getenv("LLM_MODEL"),
        temperature=0
    )
elif os.getenv("ANTHROPIC_API_KEY"):
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)
elif os.getenv("OPENAI_API_KEY"):
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
else:
    llm = MockLLM()

# Shared structures
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

if os.getenv("EMBEDDING_MODEL") and HAS_SENTENCE_TRANSFORMERS:
    try:
        embedding_model = SentenceTransformer(os.getenv("EMBEDDING_MODEL"))
    except Exception:
        embedding_model = MockEmbeddingModel()
else:
    embedding_model = MockEmbeddingModel()

idms = IDMS(embedding_model, llm)
profile_agent = AdaptiveProfileAgent(llm)

db = SessionLocal()
problem_db = ProblemDatabase(db)

from agents.proxy import AdversarialProxyAgent

agents = AgentRegistry(
    orchestrator=OrchestratorAgent(llm, idms, profile_agent),
    socratic=SocraticAgent(llm),
    gap_explainer=GapExplainerAgent(llm, problem_db),
    closure=ClosureAgent(llm),
    cinema=ConceptCinemaAgent(llm),
    anti_overing=AntiOveringAgent(llm, problem_db),
    profile=profile_agent,
    proxy=AdversarialProxyAgent(llm, embedding_model)
)

workflow = build_learnflow_graph(agents, idms)
db.close()

app.state.workflow = workflow

from api.routes import router as api_router
app.include_router(api_router)

@app.on_event("startup")
def startup_event():
    init_db()
    session_db = SessionLocal()
    try:
        seed_database(session_db)
    finally:
        session_db.close()

