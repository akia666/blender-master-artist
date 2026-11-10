"""Bounded correction orchestration; no implicit artistic or user approval."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CorrectionPlan:
    problem: str
    evidence: str
    strategy: str
    targets: tuple


def correction_loop(inspect, propose, apply, max_iterations=3):
    if not 0 <= max_iterations <= 20:
        raise ValueError("Correction limit must be between 0 and 20")
    history = []
    for iteration in range(max_iterations + 1):
        observation = inspect()
        history.append({"iteration": iteration, "observation": observation})
        if observation.get("technical_status") == "pass" and observation.get("visual_status") == "reviewed_pass":
            return {"status": "validated", "history": history, "corrections": iteration}
        if iteration == max_iterations:
            status = "needs_visual_review" if observation.get("technical_status") == "pass" else "limit_reached"
            return {"status": status, "history": history, "corrections": iteration}
        plan = propose(observation)
        if not isinstance(plan, CorrectionPlan) or not all((plan.problem, plan.evidence, plan.strategy, plan.targets)):
            status = "needs_visual_review" if observation.get("technical_status") == "pass" else "no_evidenced_plan"
            return {"status": status, "history": history, "corrections": iteration}
        history[-1]["plan"] = plan.__dict__
        # The caller must obtain an edit permit; errors propagate, never hidden/retried.
        history[-1]["outcome"] = apply(plan)

