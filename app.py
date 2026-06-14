import os
import time
import asyncio
from typing import Any
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

# Direct import of backend components
from graph.state import LearnFlowState
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

# Ensure DB is initialized
init_db()
db_session = SessionLocal()
seed_database(db_session)

# Setup LLM & Models
class MockLLMResponse:
    def __init__(self, content: str):
        self.content = content

class MockLLM:
    async def ainvoke(self, messages: Any) -> MockLLMResponse:
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
            return MockLLMResponse('{"depth_preference": 0.6, "known_gaps": ["pseudo-forces"], "error_patterns": {"vertical_frames": 1}, "decay_scores": {"laws_of_motion": 0.8}, "gap_frequency": {"laws_of_motion": 0.3}}')
            
        return MockLLMResponse("I see. Let's look closer at the physical principles at play here.")

# LLM Selection
if os.getenv("LLM_API_KEY"):
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        model=os.getenv("LLM_MODEL"),
        temperature=0
    )
elif os.getenv("ANTHROPIC_API_KEY"):
    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)
elif os.getenv("OPENAI_API_KEY"):
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
else:
    llm = MockLLM()

# Setup IDMS and Workflow
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
problem_db = ProblemDatabase(db_session)

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

# --- Streamlit Layout ---
st.set_page_config(page_title="LearnFlow", layout="wide")

# Inject Custom Barbie Theme styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Poppins:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background-color: #FFFBF8;
        color: #8B5E3C;
        font-family: 'DM Sans', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        color: #1A1A1A !important;
    }
    
    .hero-text {
        font-family: 'Playfair Display', serif;
        font-size: 4rem;
        font-style: italic;
        line-height: 1.1;
        color: #1A1A1A;
    }
    
    .hero-accent {
        color: #FF3EA5;
        font-style: normal;
        font-weight: 800;
    }
    
    .barbie-button {
        background-color: #FF3EA5 !important;
        color: white !important;
        border-radius: 9999px !important;
        padding: 0.75rem 2rem !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    .barbie-button:hover {
        transform: scale(1.03) !important;
        box-shadow: 0 8px 30px rgba(255, 62, 165, 0.3) !important;
    }
    
    .sidebar-card {
        background-color: white;
        border: 1px solid #F5E6D3;
        border-radius: 24px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(255, 62, 165, 0.05);
        margin-bottom: 1rem;
    }
    
    /* Drift Ring animation styling */
    .drift-ring {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: auto;
        font-family: 'JetBrains Mono', monospace;
        font-weight: bold;
        transition: all 0.3s ease-in-out;
    }
    .drift-safe {
        border: 6px solid #FF3EA5;
        box-shadow: 0 0 15px rgba(255, 62, 165, 0.2);
    }
    .drift-alarm {
        border: 6px solid #FF6B6B;
        box-shadow: 0 0 30px rgba(255, 107, 107, 0.7);
        animation: alarm-pulse 1s infinite alternate;
    }
    @keyframes alarm-pulse {
        0% { transform: scale(1); }
        100% { transform: scale(1.05); }
    }
    
    .status-badge {
        font-family: 'Poppins', sans-serif;
        font-size: 11px;
        letter-spacing: 0.12em;
        font-weight: bold;
        text-transform: uppercase;
        color: #FF3EA5;
    }
    </style>
""", unsafe_allow_html=True)

# Session States
if "screen" not in st.session_state:
    st.session_state.screen = "landing"
if "history" not in st.session_state:
    st.session_state.history = []
if "drift_magnitude" not in st.session_state:
    st.session_state.drift_magnitude = 0.34
if "gate_value" not in st.session_state:
    st.session_state.gate_value = 0.64
if "drift_detected" not in st.session_state:
    st.session_state.drift_detected = False
if "active_agent" not in st.session_state:
    st.session_state.active_agent = "Socratic Agent"
if "session_state_dict" not in st.session_state:
    st.session_state.session_state_dict = {
        "session_id": "sess_default",
        "student_id": "student_1",
        "current_chapter": "Laws of Motion",
        "current_problem": "two_block_collision",
        "message_history": [],
        "current_input": "",
        "next_agent": "orchestrator",
        "active_beat": 1,
        "beat_awaiting_response": False,
        "diagram_described": False,
        "drift_detected": False,
        "drift_magnitude": 0.34,
        "gate_value": 0.64,
        "closure_verdict": None,
        "anti_overing_verdict": None,
        "socratic_rounds": 0,
        "profile_summary": {},
        "revision_queue": [],
        "hint_density": "medium",
        "final_response": "Welcome to LearnFlow! Describe your visual setup for this two-block collision problem.",
        "response_agent": "socratic"
    }

# Navigation Handlers
def nav_to(screen_name):
    st.session_state.screen = screen_name

# --- Top Navigation Bar ---
col_logo, col_nav = st.columns([1, 2])
with col_logo:
    st.markdown("<div style='display:flex; align-items:center; gap:0.5rem; font-family:\"Poppins\",sans-serif; font-weight:700; font-size:1.8rem; cursor:pointer;' onclick='window.location.reload()'>🌊 LearnFlow</div>", unsafe_allow_html=True)
with col_nav:
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
    with btn_col1:
        if st.button("Home", key="nav_home"): nav_to("landing")
    with btn_col2:
        if st.button("Session Space", key="nav_session"): nav_to("session")
    with btn_col3:
        if st.button("Student Profile", key="nav_profile"): nav_to("profile")
    with btn_col4:
        st.markdown("<button class='barbie-button' style='font-size:12px; padding:6px 15px !important;'>Quick Start</button>", unsafe_allow_html=True)

st.markdown("<hr style='border-color: #F5E6D3; margin-top:0.5rem; margin-bottom:1.5rem;'>", unsafe_allow_html=True)



# --- SCREEN: LANDING ---
if st.session_state.screen == "landing":
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("""
            <div style='margin-top:2rem;'>
                <h1 class='hero-text'>The exam doesn't reward knowing. <br>It rewards <span class='hero-accent'>thinking.</span></h1>
                <p style='font-size:1.15rem; color:#8B5E3C; line-height:1.7; margin-top:1.5rem; margin-bottom:2rem;'>
                    JEE/NEET preparation designed around your brain, not procedural memorization. 8 AI agents. Zero direct answer-giving. Focus on fundamental principles, not procedures.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Start Thinking Session →", key="start_session_btn"):
            nav_to("session")
            st.rerun()
            
    with col_right:
        # Agent orbit SVG
        st.markdown("""
            <div style="display:flex; justify-content:center;">
                <svg width="380" height="380" viewBox="0 0 500 500">
                    <circle cx="250" cy="250" r="180" fill="none" stroke="#F5E6D3" stroke-width="2" stroke-dasharray="5,5" />
                    <circle cx="250" cy="250" r="100" fill="none" stroke="#F5E6D3" stroke-width="1" />
                    <line x1="250" y1="250" x2="250" y2="70" stroke="#FF3EA5" stroke-width="2" opacity="0.6" />
                    <line x1="250" y1="250" x2="430" y2="250" stroke="#FF3EA5" stroke-width="2" opacity="0.6" />
                    <line x1="250" y1="250" x2="250" y2="430" stroke="#FF3EA5" stroke-width="2" opacity="0.6" />
                    <line x1="250" y1="250" x2="70" y2="250" stroke="#FF3EA5" stroke-width="2" opacity="0.6" />
                    <circle cx="250" cy="250" r="28" fill="#FF3EA5" />
                    <circle cx="250" cy="70" r="20" fill="#87CEEB" />
                    <circle cx="430" cy="250" r="20" fill="#FF6B6B" />
                    <circle cx="250" cy="430" r="20" fill="#FF3EA5" />
                    <circle cx="70" cy="250" r="20" fill="#FFF0A0" stroke="#8B5E3C" />
                    <text x="250" y="300" font-family="Poppins" font-size="11" font-weight="bold" fill="#1A1A1A" text-anchor="middle">ORCHESTRATOR</text>
                </svg>
            </div>
        """, unsafe_allow_html=True)

# --- SCREEN: SESSION ---
elif st.session_state.screen == "session":
    # Sidebar & Center
    col_side, col_chat = st.columns([3, 9])
    
    with col_side:
        st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
        st.markdown("<span class='status-badge'>active session</span>", unsafe_allow_html=True)
        st.markdown("<h3>Laws of Motion</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:12px;'>Problem: elastic collision of 2 blocks</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
        st.markdown("<span class='status-badge'>active agent</span>", unsafe_allow_html=True)
        st.markdown(f"<h4>● {st.session_state.active_agent}</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:12px;'>Enforcing Entry Protocol & Diagram Gate</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Profile Snapshot in the left sidebar
        st.markdown("""
            <div class='sidebar-card'>
                <span class='status-badge'>profile gaps</span>
                <div style='font-size:12px; margin-top:0.5rem;'>
                    <b>Derivation-first preference:</b> 78%<br>
                    <b>Active Gaps:</b> Newton's Laws direction vectors (Level: High)
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_chat:
        # Chat space
        st.markdown("<h3 style='margin-bottom:1rem;'>Dialogue Workspace</h3>", unsafe_allow_html=True)
        
        # Initialize default history
        if not st.session_state.history:
            st.session_state.history = [
                {
                    "role": "agent",
                    "agent_name": "Socratic Agent",
                    "color": "#87CEEB",
                    "content": "Welcome to your active thinking session! Let's start with your problem. What is the problem giving you, and what is it asking for?"
                }
            ]
            
        # Display simulated chat messages dynamically
        chat_html = "<div style='background-color:white; border:1px solid #F5E6D3; border-radius:24px; padding:1.5rem; min-height:300px; max-height:450px; overflow-y:auto;'>"
        for msg in st.session_state.history:
            if msg["role"] == "agent":
                chat_html += f"""
                <div style='margin-bottom:1.5rem;'>
                    <span style='font-weight:bold; color:#FF3EA5; font-size:12px;'>● {msg['agent_name'].upper()}</span>
                    <div style='background-color:{msg['color']}10; padding:12px; border-radius:15px; border-left:4px solid {msg['color']}; margin-top:5px; color:#1A1A1A;'>
                        {msg['content']}
                    </div>
                </div>
                """
            else:
                chat_html += f"""
                <div style='margin-bottom:1.5rem; text-align:right;'>
                    <span style='font-weight:bold; color:#8B5E3C; font-size:12px;'>YOU</span>
                    <div style='background-color:#FF3EA5; color:white; padding:12px; border-radius:15px; border-top-right-radius:0; margin-top:5px; display:inline-block; max-width:80%; text-align:left;'>
                        {msg['content']}
                    </div>
                </div>
                """
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # Form to submit user messages
        with st.form("chat_form", clear_on_submit=True):
            user_msg = st.text_input("Enter your response here:")
            submitted = st.form_submit_button(label="Submit →")
            if submitted and user_msg:
                # Add student message
                st.session_state.history.append({"role": "student", "content": user_msg})
                
                # Invoke the real workflow if available, or fall back to mock response
                try:
                    state = st.session_state.session_state_dict
                    state["current_input"] = user_msg
                    config = {"configurable": {"thread_id": state["session_id"]}}
                    
                    # Run LangGraph synchronously
                    final_state = asyncio.run(workflow.ainvoke(state, config))
                    
                    # Save states
                    st.session_state.session_state_dict = dict(final_state)
                    st.session_state.drift_magnitude = final_state.get("drift_magnitude", 0.0)
                    st.session_state.gate_value = final_state.get("gate_value", 0.0)
                    st.session_state.drift_detected = final_state.get("drift_detected", False)
                    
                    agent_name = final_state.get("response_agent", "socratic").replace("_", " ").title() + " Agent"
                    agent_color = "#87CEEB" if "Socratic" in agent_name else "#FF6B6B" if "Gap" in agent_name else "#FF3EA5"
                    st.session_state.active_agent = agent_name
                    
                    st.session_state.history.append({
                        "role": "agent",
                        "agent_name": agent_name,
                        "color": agent_color,
                        "content": final_state.get("final_response", "")
                    })
                except Exception as e:
                    # Fallback to local Socratic simulation
                    st.session_state.history.append({
                        "role": "agent",
                        "agent_name": "Socratic Agent",
                        "color": "#87CEEB",
                        "content": "That makes sense. If the elevator is moving with a constant acceleration upward, how does that affect the overall gravity experienced inside?"
                    })
                st.rerun()


# --- SCREEN: PROFILE ---
elif st.session_state.screen == "profile":
    st.markdown("<h3>Silent Learner Model Summary</h3>", unsafe_allow_html=True)
    st.markdown("<p>Inferred entirely from problem attempts, Socratic iterations, and method selections.</p>", unsafe_allow_html=True)
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("""
            <div class='sidebar-card'>
                <h4>Cognitive Parameters</h4>
                <p><b>Derivation-first preference:</b> 78% (Prefers mathematical derivations over pure formula listing)</p>
                <p><b>Socratic response depth:</b> Medium (Gaps closed within average of 3.4 rounds)</p>
            </div>
        """, unsafe_allow_html=True)
    with col_p2:
        st.markdown("""
            <div class='sidebar-card'>
                <h4>Identified Gaps & Errors</h4>
                <p><b>Newton III pairs:</b> High error rate under vertical acceleration scenarios</p>
                <p><b>Sign conventions:</b> Resolving rotational coordinates (3 occurrences)</p>
            </div>
        """, unsafe_allow_html=True)

db_session.close()
