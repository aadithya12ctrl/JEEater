"""
data/isomorphic_pairs.py — Isomorphic Pair Database.

Maps problems to their structural twins across different surface features.
E.g.: two-block collision ↔ ballistic pendulum ↔ rocket propulsion
All are momentum conservation with the same dp/dt structure.

Spec reference: §8 Module 6, lines 1422-1449.
"""

import random
from typing import Optional
from data.problem_db import ProblemDatabase, Problem


class IsomorphicPairDatabase:
    """
    Maps problems to their structural twins across different surface features.

    The key insight: students who can solve one surface variant but not another
    have learned the procedure, not the principle. The isomorphic pair database
    is the Anti-Overing Agent's primary tool for exposing this failure mode.
    """

    pairs = {
        "momentum_conservation": [
            "two_block_collision",
            "ballistic_pendulum",
            "rocket_propulsion",
            "explosion_recoil",
        ],
        "energy_method_vs_newton": [
            "block_on_incline_with_friction",
            "pendulum_with_damping",
            "spring_block_system",
        ],
        "rotational_dynamics": [
            "cylinder_rolling_incline",
            "disc_with_tangential_force",
            "spinning_top_precession",
        ],
        "simple_harmonic_motion": [
            "mass_spring_horizontal",
            "liquid_in_u_tube",
            "floating_block_oscillation",
        ],
        "electrostatics_gauss_law": [
            "infinite_line_charge",
            "uniformly_charged_sphere",
            "parallel_plate_capacitor",
        ],
        "kirchhoffs_laws": [
            "wheatstone_bridge",
            "rc_circuit_transient",
            "multi_loop_circuit",
        ],
        "optics_refraction": [
            "glass_slab_lateral_shift",
            "prism_minimum_deviation",
            "total_internal_reflection",
        ],
        "thermodynamics_first_law": [
            "isothermal_expansion",
            "adiabatic_compression",
            "cyclic_process_pv_diagram",
        ],
    }

    def __init__(self, problem_db: ProblemDatabase):
        self.problem_db = problem_db

    def find_principle(self, problem_id: str) -> Optional[str]:
        """Find the underlying principle group for a problem ID."""
        for principle, problems in self.pairs.items():
            if problem_id in problems:
                return principle
        return None

    def get_structural_twin(self, problem_id: str) -> Optional[Problem]:
        """
        Get a structurally isomorphic problem that shares the same
        underlying principle but has different surface features.
        """
        principle = self.find_principle(problem_id)
        if not principle:
            return None

        twins = self.pairs[principle]
        candidates = [t for t in twins if t != problem_id]
        if not candidates:
            return None

        twin_id = random.choice(candidates)
        return self.problem_db.get(twin_id)

    def get_all_twins(self, problem_id: str) -> list[Problem]:
        """Get all structural twins for a problem."""
        principle = self.find_principle(problem_id)
        if not principle:
            return []

        twins = self.pairs[principle]
        result = []
        for t in twins:
            if t != problem_id:
                prob = self.problem_db.get(t)
                if prob:
                    result.append(prob)
        return result

    def get_principle_name(self, problem_id: str) -> Optional[str]:
        """Get the human-readable principle name for a problem."""
        principle = self.find_principle(problem_id)
        if principle:
            return principle.replace("_", " ").title()
        return None
