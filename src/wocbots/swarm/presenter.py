from wocbots.agents import Agent

def validate_fitness_args(prior_performance_normalized : float, confidence : float, trust_score : float) -> None:
    is_constraint_error = False
    error_string = ""
    if(prior_performance_normalized < 0.0 or prior_performance_normalized > 1.0):
        is_constraint_error = True
        error_string += "prior_performance_normalized"
    if(confidence < 0.0 or confidence > 1.0):
        is_constraint_error = True
        if (error_string == ""):
            error_string += "confidence"
        else:
            error_string += ", confidence"
    if(trust_score < 0.0 or trust_score > 1.0):
        is_constraint_error = True
        if (error_string == ""):
            error_string += "trust_score"
        else:
            error_string += ", trust_score"
    if(is_constraint_error):
        raise ValueError("Constraint error %s not in [0,1]" % error_string)

def validate_prior_performance_args(prior_performance : float) -> None:
    if(prior_performance < 0.7 or prior_performance > 1.3):
        raise ValueError("Constraint Error: %f not in [0.7, 1.3]" % prior_performance)

class Presenter(Agent):
    def __init__(self, *, features, eval_accuracy, eval_precision, eval_recall, confidence_weights):
        super().__init__(features=features, eval_accuracy=eval_accuracy, eval_precision=eval_precision, eval_recall=eval_recall, confidence_weights=confidence_weights)
        self.update_fitness()
        
    def calculate_fitness(self, prior_performance_normalized : float, confidence : float, trust_score : float) -> float:
        """The §
        """
        validate_fitness_args(prior_performance_normalized, confidence, trust_score)
        return (prior_performance_normalized + confidence + trust_score) / 3.0

    def calculate_normalized_prior_performance(self, prior_performance: float) -> float:
        validate_prior_performance_args(prior_performance=prior_performance)
        return (prior_performance - 0.7) / 0.6

    def update_fitness(self) -> None:
        self.fitness = self.calculate_fitness(self.calculate_normalized_prior_performance(self.prior_performance), self.confidence(), self.trust_score)