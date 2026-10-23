from wocbots.agents import Agent
from wocbots.swarm.subject import BeeSubject


def validate_fitness_args(prior_performance_normalized: float, confidence: float, trust_score: float) -> None:
    is_constraint_error = False
    error_string = ""
    if prior_performance_normalized < 0.0 or prior_performance_normalized > 1.0:
        is_constraint_error = True
        error_string += "prior_performance_normalized"
    if confidence < 0.0 or confidence > 1.0:
        is_constraint_error = True
        if error_string == "":
            error_string += "confidence"
        else:
            error_string += ", confidence"
    if trust_score < 0.0 or trust_score > 1.0:
        is_constraint_error = True
        if error_string == "":
            error_string += "trust_score"
        else:
            error_string += ", trust_score"
    if is_constraint_error:
        raise ValueError(f"Constraint error {error_string} not in [0,1]")


def validate_prior_performance_args(prior_performance: float) -> None:
    if prior_performance < 0.7 or prior_performance > 1.3:
        raise ValueError(f"Constraint Error: {prior_performance:f} not in [0.7, 1.3]")


class Presenter(BeeSubject):
    def __init__(self, agent: Agent) -> None:
        super().__init__(agent=agent)
        self.update_fitness()

    def calculate_fitness(
        self, prior_performance_normalized: float, confidence: float, trust_score: float
    ) -> float:
        validate_fitness_args(prior_performance_normalized, confidence, trust_score)
        return (prior_performance_normalized + confidence + trust_score) / 3.0

    def calculate_normalized_prior_performance(self, prior_performance: float) -> float:
        validate_prior_performance_args(prior_performance=prior_performance)
        return (prior_performance - 0.7) / 0.6

    def update_fitness(self) -> None:
        self.fitness = self.calculate_fitness(
            self.calculate_normalized_prior_performance(self.agent.prior_performance),
            self.agent.confidence,
            self.agent.trust_score,
        )