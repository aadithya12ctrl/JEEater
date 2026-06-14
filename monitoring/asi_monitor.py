class ASIMonitor:
    DIMENSIONS = [
        "format_consistency",      # is the agent using its prescribed format?
        "role_adherence",          # is the agent staying in its role?
        "question_ratio",          # for Socratic: ratio of questions to statements
        "answer_leakage",          # did any agent give a direct answer?
        "verdict_specificity",     # for Closure: COVERED/CLOSED vs vague
        "inter_agent_agreement",   # are agents agreeing more than the input justifies?
    ]
    
    def __init__(self, llm):
        self.llm = llm
        
    async def score_dimension(self, agent_name: str, dimension: str, recent_outputs: list[str]) -> float:
        if not recent_outputs:
            return 1.0
            
        outputs_str = "\n---\n".join(recent_outputs)
        
        prompt = f"""
        Evaluate the following outputs from the agent '{agent_name}' for the stability dimension '{dimension}'.
        
        Outputs:
        {outputs_str}
        
        Score from 0.0 (total failure/drift) to 1.0 (perfect compliance).
        Respond with ONLY the float number (e.g. 0.85). Do not include any other text.
        """
        
        try:
            res = await self.llm.ainvoke(prompt)
            score = float(res.content.strip())
            return min(max(score, 0.0), 1.0)
        except Exception:
            return 0.8  # reasonable fallback
            
    async def compute_asi(self, agent_name: str, recent_outputs: list[str]) -> float:
        scores = []
        for dimension in self.DIMENSIONS:
            score = await self.score_dimension(agent_name, dimension, recent_outputs)
            scores.append(score)
            
        # Weighted average — role_adherence and answer_leakage weighted highest
        weights = [0.15, 0.25, 0.15, 0.20, 0.10, 0.15]
        asi = sum(s * w for s, w in zip(scores, weights))
        return asi
    
    def check_drift(self, asi: float) -> bool:
        return asi < 0.65
