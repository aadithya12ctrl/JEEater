import random
from sqlalchemy.orm import Session
from data.models import Problem, SessionLocal

# ~20 high-quality seed JEE Physics problems grouped by principles for Structural Transfer
SEED_PROBLEMS = [
    # group: momentum_conservation
    {
        "id": "two_block_collision",
        "chapter": "Laws of Motion",
        "principle_tag": "momentum_conservation",
        "difficulty": "Hard",
        "isomorphic_group": "momentum_conservation",
        "problem_text": "A block of mass m moving with velocity v collides elastically head-on with a block of mass 2m at rest. Find the final velocities of both blocks.",
        "standard_solution": "Apply conservation of linear momentum: m*v = m*v1 + 2m*v2. Since the collision is elastic, conservation of kinetic energy also applies: 0.5*m*v^2 = 0.5*m*v1^2 + 0.5*2m*v2^2. Solve the simultaneous equations to find v1 = -v/3 and v2 = 2v/3."
    },
    {
        "id": "ballistic_pendulum",
        "chapter": "Work & Energy",
        "principle_tag": "momentum_conservation",
        "difficulty": "Hard",
        "isomorphic_group": "momentum_conservation",
        "problem_text": "A bullet of mass m is fired horizontally into a large block of wood of mass M suspended like a pendulum. The bullet embeds in the block, and the system swings up to a maximum height h. Find the initial velocity of the bullet.",
        "standard_solution": "First, apply conservation of momentum during the collision: m*v = (m + M)*V_collision. Second, apply conservation of mechanical energy as the pendulum swings up: 0.5*(m + M)*V_collision^2 = (m + M)*g*h. Solve for bullet velocity v = (1 + M/m)*sqrt(2*g*h)."
    },
    {
        "id": "rocket_propulsion",
        "chapter": "Laws of Motion",
        "principle_tag": "momentum_conservation",
        "difficulty": "Hard",
        "isomorphic_group": "momentum_conservation",
        "problem_text": "A rocket of mass M ejects gas at a constant rate r relative to the rocket with a velocity u. Neglecting gravity, find the rocket's velocity as a function of time.",
        "standard_solution": "Use thrust force F_thrust = u * (dM/dt). Since F_ext = 0, dp/dt = 0. Integrating the equation of motion M*(dv/dt) = -u*(dM/dt) gives the Tsiolkovsky rocket equation: v(t) = v0 + u*ln(M0 / M(t))."
    },
    {
        "id": "explosion_recoil",
        "chapter": "Laws of Motion",
        "principle_tag": "momentum_conservation",
        "difficulty": "Medium",
        "isomorphic_group": "momentum_conservation",
        "problem_text": "A shell of mass 3m at rest suddenly explodes into three fragments of equal mass. One fragment flies off along the x-axis with speed v, another along the y-axis with speed v. Find the velocity of the third fragment.",
        "standard_solution": "Since the explosion is internal, external force is zero, conserving momentum. Initial momentum P_initial = 0. Final momentum: P_final = m*v*i + m*v*j + m*V3. Since P_initial = P_final, V3 = -v*i - v*j. The magnitude is v*sqrt(2)."
    },
    # group: energy_conservation
    {
        "id": "loop_the_loop",
        "chapter": "Work & Energy",
        "principle_tag": "energy_conservation",
        "difficulty": "Hard",
        "isomorphic_group": "energy_conservation",
        "problem_text": "A small block of mass m slides from rest down a frictionless track and loops a vertical loop of radius R. What is the minimum release height h above the bottom of the loop so the block doesn't fall off at the top?",
        "standard_solution": "At the top of the loop, the minimum speed v for circular motion requires Normal force >= 0. Centripetal condition: m*v^2 / R = N + m*g. For N=0, v^2 = g*R. Using conservation of mechanical energy between release height h and top of the loop (height 2R): m*g*h = m*g*(2R) + 0.5*m*v^2. Substituting v^2 gives h = 2.5R."
    },
    {
        "id": "spring_block_velocity",
        "chapter": "Work & Energy",
        "principle_tag": "energy_conservation",
        "difficulty": "Medium",
        "isomorphic_group": "energy_conservation",
        "problem_text": "A block of mass m is attached to a horizontal spring of constant k. The spring is compressed by x0 and released. Find the velocity of the block when the spring is at half its maximum compression.",
        "standard_solution": "Frictionless surface, conserving mechanical energy: E_initial = 0.5*k*x0^2. At x0/2, E_final = 0.5*k*(x0/2)^2 + 0.5*m*v^2. E_initial = E_final leads to 0.5*k*x0^2 = 0.125*k*x0^2 + 0.5*m*v^2. Solving for velocity gives v = sqrt(3*k/(4*m)) * x0."
    },
    {
        "id": "falling_block_spring",
        "chapter": "Work & Energy",
        "principle_tag": "energy_conservation",
        "difficulty": "Hard",
        "isomorphic_group": "energy_conservation",
        "problem_text": "A block of mass m is dropped from a height h onto a vertical spring of force constant k. Find the maximum compression of the spring.",
        "standard_solution": "Let the maximum compression be y. Using the lowest point as reference for gravitational potential energy: conservation of energy between start and max compression gives m*g*(h + y) = 0.5*k*y^2. Re-arrange into a quadratic equation: 0.5*k*y^2 - m*g*y - m*g*h = 0, and solve for y."
    },
    # group: non_inertial_frames
    {
        "id": "accelerating_elevator_pendulum",
        "chapter": "Laws of Motion",
        "principle_tag": "non_inertial_frames",
        "difficulty": "Medium",
        "isomorphic_group": "non_inertial_frames",
        "problem_text": "A simple pendulum is hanging inside an elevator accelerating upwards with acceleration 'a'. Find the effective time period of the pendulum.",
        "standard_solution": "In the elevator's frame (non-inertial), a pseudo-force m*a acts downwards in addition to gravity m*g. Thus, the effective acceleration due to gravity is g_eff = g + a. The time period is T = 2*pi*sqrt(L / (g + a))."
    },
    {
        "id": "sliding_block_on_accelerating_wedge",
        "chapter": "Laws of Motion",
        "principle_tag": "non_inertial_frames",
        "difficulty": "Hard",
        "isomorphic_group": "non_inertial_frames",
        "problem_text": "A wedge of angle theta is accelerated horizontally with acceleration 'a'. A small block of mass m is placed on its frictionless incline. Find the condition on 'a' so the block remains stationary relative to the wedge.",
        "standard_solution": "In the wedge's non-inertial frame, a horizontal pseudo-force m*a acts on the block in the opposite direction of acceleration. Balances forces along the incline: m*a*cos(theta) = m*g*sin(theta). Thus, the wedge acceleration must be a = g*tan(theta)."
    },
    {
        "id": "centrifugal_bead_on_wire",
        "chapter": "Laws of Motion",
        "principle_tag": "non_inertial_frames",
        "difficulty": "Hard",
        "isomorphic_group": "non_inertial_frames",
        "problem_text": "A circular wire hoop of radius R rotates about its vertical diameter with constant angular speed omega. A small bead is free to slide on the hoop. Find the angle theta at which the bead remains at rest relative to the hoop.",
        "standard_solution": "In the rotating frame, centrifugal force m*omega^2*r acts horizontally (where r = R*sin(theta)). Forces along the tangent to the hoop balance: m*g*sin(theta) = m*omega^2*R*sin(theta)*cos(theta). Solving gives theta = 0 or cos(theta) = g / (omega^2 * R) if omega^2 > g/R."
    }
]

# We will fill out the rest up to 20 to ensure we have a robust database
for i in range(10):
    SEED_PROBLEMS.append({
        "id": f"extra_problem_{i}",
        "chapter": "Kinematics" if i % 2 == 0 else "Work & Energy",
        "principle_tag": "kinematics_equations" if i % 2 == 0 else "power_concept",
        "difficulty": "Medium",
        "isomorphic_group": f"extra_group_{i//2}",
        "problem_text": f"Sample JEE Problem {i}: In a 1D system, find displacement given time-dependent acceleration a(t) = {i}*t.",
        "standard_solution": f"Integrate acceleration once for velocity: v(t) = 0.5*{i}*t^2 + v0. Integrate velocity for displacement: x(t) = {i/6}*t^3 + v0*t + x0."
    })

def seed_database(db: Session):
    for sp in SEED_PROBLEMS:
        existing = db.query(Problem).filter(Problem.id == sp["id"]).first()
        if not existing:
            problem = Problem(
                id=sp["id"],
                chapter=sp["chapter"],
                principle_tag=sp["principle_tag"],
                difficulty=sp["difficulty"],
                isomorphic_group=sp["isomorphic_group"],
                problem_text=sp["problem_text"],
                standard_solution=sp["standard_solution"]
            )
            db.add(problem)
    db.commit()

class ProblemDatabase:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get(self, problem_id: str) -> Problem:
        return self.db.query(Problem).filter(Problem.id == problem_id).first()

    def get_structural_twin(self, problem_id: str) -> Problem:
        prob = self.get(problem_id)
        if not prob:
            raise ValueError(f"Problem {problem_id} not found")
        twins = self.db.query(Problem).filter(
            Problem.isomorphic_group == prob.isomorphic_group,
            Problem.id != problem_id
        ).all()
        if not twins:
            return prob
        return random.choice(twins)
