import pytest

from wocbots.agents import HOLLYWOOD_WEIGHTS
from wocbots.swarm.presenter import Presenter

@pytest.fixture(scope="function")
def presenter_under_test():
     yield Presenter(features=("f0",),
                     eval_accuracy=0.5,
                     eval_precision=0.5,
                     eval_recall=0.5, confidence_weights=HOLLYWOOD_WEIGHTS)

@pytest.mark.parametrize(["prior_performance_normalized", "confidence", "trust_score", "expected_fitness"],[
    (0.0, 0.0, 0.0, 0.0),
    (1.0, 1.0, 1.0, 1.0),
    (1.0, 0.5, 0.0, 0.5)
])

def test_fitness_calc(presenter_under_test, prior_performance_normalized, confidence, trust_score, expected_fitness):
    actual_fitness = presenter_under_test.calculate_fitness(prior_performance_normalized, confidence, trust_score)
    assert(actual_fitness == pytest.approx(expected_fitness))

@pytest.mark.parametrize(["prior_performance_normalized", "confidence", "trust_score", "error_string"],[
    (1.001, 0.0, 0.0, "prior_performance_normalized"),
    (-0.001, 1.0, 1.0, "prior_performance_normalized"),
    (1.0, 1.001, 0.0, "confidence"),
    (0.0, -0.001, 0.0, "confidence"),
    (0.0, 0.0, 1.001, "trust_score"),
    (0.0, 0.0, -0.001, "trust_score"),
    (1.001, 1.001, 0.0, "prior_performance_normalized, confidence"),
    (1.001, 0.0, 1.001, "prior_performance_normalized, trust_score"),
    (0.0, 1.001, 1.001, "confidence, trust_score"),
    (1.001, 1.001, 1.001, "prior_performance_normalized, confidence, trust_score")
])
def test_fitness_constraint_error(presenter_under_test, prior_performance_normalized, confidence, trust_score, error_string):
     with pytest.raises(ValueError) as exception:
          presenter_under_test.calculate_fitness(prior_performance_normalized=prior_performance_normalized, confidence=confidence, trust_score=trust_score)

          assert "Constraint error %s not in [0,1]" % error_string in str(exception.value)

@pytest.mark.parametrize(["prior_performance", "expected_prior_performance_normalized"],[
     (0.7, 0.0),
     (1.3, 1.0),
     (1.0, 0.5)
     ])

def test_normalized_prior_performance_calc(presenter_under_test, prior_performance, expected_prior_performance_normalized):
     actual_normalized_prior_performance = presenter_under_test.calculate_normalized_prior_performance(prior_performance)
     assert(actual_normalized_prior_performance == pytest.approx(expected_prior_performance_normalized))

@pytest.mark.parametrize(["prior_performance", "expected_prior_performance_normalized"],[
     (0.0, -1.0),
     (0.699, -1.0),
     (1.301, -1.0),
     (2.0, -1.0)
     ])

def test_prior_performance_constraint_error(presenter_under_test, prior_performance, expected_prior_performance_normalized):
     with pytest.raises(ValueError) as exception:
          presenter_under_test.calculate_normalized_prior_performance(prior_performance=prior_performance)

          assert "Constraint Error: %f not in [0.7, 1.3]" % prior_performance in str(exception.value)