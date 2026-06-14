import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///learnflow.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Student(Base):
    __tablename__ = "students"
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(JSON, default={})

class SessionModel(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    student_id = Column(String, ForeignKey("students.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    state_json = Column(JSON, default={})
    active = Column(Boolean, default=True)

class Problem(Base):
    __tablename__ = "problems"
    id = Column(String, primary_key=True)
    chapter = Column(String, nullable=False)
    principle_tag = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    isomorphic_group = Column(String, nullable=False)
    problem_text = Column(Text, nullable=False)
    standard_solution = Column(Text, nullable=False)

class Profile(Base):
    __tablename__ = "profiles"
    student_id = Column(String, ForeignKey("students.id"), primary_key=True)
    depth_preference = Column(Float, default=0.5)      # 0.0 (application-first) to 1.0 (derivation-first)
    known_gaps = Column(JSON, default=[])               # List of gaps identified
    error_patterns = Column(JSON, default={})           # E.g., {"sign_conventions": 3}
    decay_scores = Column(JSON, default={})             # E.g., {"energy_conservation": 0.9}
    gap_frequency = Column(JSON, default={})            # E.g., {"laws_of_motion": 0.4}

class AgentSignal(Base):
    __tablename__ = "agent_signals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    agent_name = Column(String, nullable=False)
    signal_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ClosureVerdict(Base):
    __tablename__ = "closure_verdicts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    concept = Column(String, nullable=False)
    verdict = Column(String, nullable=False)            # "COVERED" | "CLOSED"
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
