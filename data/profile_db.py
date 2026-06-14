"""
data/profile_db.py — Profile Database Abstraction.

Manages student profile persistence, decay scoring, and gap
frequency tracking.

Spec reference: §5 Agent 7 (lines 1127-1156), §9 Data Layer (lines 1468-1476).
"""

import json
from typing import Any, Optional
from data.models import SessionLocal, Profile as DbProfile


class ProfileDatabase:
    """
    Persistence layer for adaptive student profiles.

    Fields tracked (spec §5 Agent 7):
      - depth_preference: float — derivation-first vs application-first
      - known_gaps: list[str] — logical transitions that lose the student
      - error_patterns: dict — recurring errors with counts
      - decay_scores: dict — Ebbinghaus-style decay per concept
      - gap_frequency: dict — how often each concept gap recurs
    """

    def get_profile(self, student_id: str) -> Optional[Any]:
        """Load a student's profile from the database."""
        db = SessionLocal()
        try:
            profile = db.query(DbProfile).filter(
                DbProfile.student_id == student_id
            ).first()
            return profile
        finally:
            db.close()

    def save_profile(self, student_id: str, profile_data: dict) -> DbProfile:
        """Save or update a student's profile."""
        db = SessionLocal()
        try:
            existing = db.query(DbProfile).filter(
                DbProfile.student_id == student_id
            ).first()

            if existing:
                existing.depth_preference = profile_data.get(
                    "depth_preference", existing.depth_preference
                )
                existing.known_gaps = profile_data.get(
                    "known_gaps", existing.known_gaps
                )
                existing.error_patterns = profile_data.get(
                    "error_patterns", existing.error_patterns
                )
                existing.decay_scores = profile_data.get(
                    "decay_scores", existing.decay_scores
                )
                existing.gap_frequency = profile_data.get(
                    "gap_frequency", existing.gap_frequency
                )
                db.commit()
                return existing
            else:
                new_profile = DbProfile(
                    student_id=student_id,
                    depth_preference=profile_data.get("depth_preference", 0.5),
                    known_gaps=profile_data.get("known_gaps", []),
                    error_patterns=profile_data.get("error_patterns", {}),
                    decay_scores=profile_data.get("decay_scores", {}),
                    gap_frequency=profile_data.get("gap_frequency", {}),
                )
                db.add(new_profile)
                db.commit()
                db.refresh(new_profile)
                return new_profile
        finally:
            db.close()

    def compute_revision_priority(self, student_id: str) -> list[str]:
        """
        decay_score × gap_frequency = today's study queue.
        Spec §5 Agent 7, lines 1149-1155.
        """
        profile = self.get_profile(student_id)
        if not profile:
            return []

        decay_scores = profile.decay_scores or {}
        gap_frequency = profile.gap_frequency or {}

        # All concepts that appear in either dict
        all_concepts = set(decay_scores.keys()) | set(gap_frequency.keys())

        scored = [
            (concept, decay_scores.get(concept, 0.0) * gap_frequency.get(concept, 0.0))
            for concept in all_concepts
        ]
        return [c for c, _ in sorted(scored, key=lambda x: -x[1])]
