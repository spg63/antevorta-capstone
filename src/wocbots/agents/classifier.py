"""W2-02 §5.2 — the classifier seam and its reference wrappers (sklearn MLP, logreg).

The sklearn-facing half of the agent. Spec §5.2 fixes a *small, shallow* per-agent
classifier; this module makes that architecture executable behind a seam so that "what is
inside an agent" stays swappable (the whole point of the crowd — spec §5.2: "the
architecture does not care what's inside an agent"). Two reference variants ship: a
multilayer perceptron (the published reference) and a logistic-regression variant that
exists to *prove* agent internals are interchangeable.

Determinism contract (plan §12-R3 — THIS ticket's standing warning). Everything stochastic
descends from the single harness `numpy.random.Generator` (spec §9.1, the W0-04 one-seed
rule): `fit` draws ONE integer from that Generator for sklearn's `random_state`, so a
crowd trained from one master seed is bit-reproducible. Library nondeterminism is pinned
here, not wished away: BLAS thread count is forced to 1 for the duration of every fit and
predict (`threadpool_limits`), and the logreg solver runs `n_jobs=1`. Same feature subset +
same Generator state ⇒ identical trained metrics, twice (ticket test req 3).

This module calls NO RNG of its own: it only advances the Generator handed to `fit`. The
W0-04 RNG-discipline guard (`tests/unit/test_rng_discipline.py`) forbids `numpy.random.*`
here, and nothing in this file trips it.
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Literal, Protocol, runtime_checkable

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, Field
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from threadpoolctl import threadpool_limits

# The feature matrix / label primitives this layer consumes. Kept concrete (float64 /
# int) so the seam is typed end to end even though sklearn itself is untyped upstream.
FloatMatrix = npt.NDArray[np.float64]
LabelVector = npt.NDArray[np.int_]

# sklearn's `random_state` wants a plain int (or legacy RandomState), never a Generator.
# Draw the seed from [0, 2**31) — comfortably inside every backend's accepted range.
_SEED_UPPER_BOUND = 2**31 - 1

# Logreg solver iteration cap. Unrelated to MLP `epochs` (a different notion): this is just
# "enough for the small per-agent problems to converge", not a tunable of the method.
_LOGREG_MAX_ITER = 1000


def hidden_layer_count(input_size: int) -> int:
    """Number of hidden layers for an agent seeing `input_size` features (spec §5.2).

    Formula is normative: ``max(1, round(0.3 × input_size))`` — 2–3 features → 1 layer,
    10 features → 3 (pinned in tests at 2/3/10 → 1/1/3). `round` is Python's round-half-to-
    even; it only bites at exact halves (e.g. 5 → round(1.5) → 2), none of which are the
    pinned cases, and "shallow as possible while still learning" (spec §5.2) is preserved.
    Do not swap this for a hand-tuned depth table — per-agent architecture tuning is a
    forbidden shortcut (ticket "Forbidden shortcuts").
    """
    if input_size < 1:
        raise ValueError(f"input_size must be >= 1, got {input_size!r}")
    return max(1, round(0.3 * input_size))


def hidden_layer_sizes(spec: ClassifierSpec, input_size: int) -> tuple[int, ...]:
    """The `hidden_layer_sizes` tuple sklearn's MLP expects: `hidden_layer_count` copies of
    the configured hidden width (spec §5.2 default 32). Separated out so the architecture
    is directly testable without a fit."""
    return tuple(spec.hidden_width for _ in range(hidden_layer_count(input_size)))


@dataclass(frozen=True)
class LabeledData:
    """A feature matrix, its binary labels, and the column names — the shape W1-05 hands to
    the agent layer.

    Frozen: a dataset object cannot be mutated out from under a training run. `select`
    is how an agent takes ONLY its assigned feature subset (spec §5.1) — the columns an
    agent was never given are invisible to it, which is what makes a feature-diverse crowd
    a crowd rather than N copies of one model.
    """

    features: tuple[str, ...]
    X: FloatMatrix
    y: LabelVector

    def __post_init__(self) -> None:
        if self.X.ndim != 2:
            raise ValueError(f"X must be 2-D (samples × features), got shape {self.X.shape}")
        if len(self.features) != self.X.shape[1]:
            raise ValueError(
                f"features names ({len(self.features)}) must match X columns ({self.X.shape[1]})"
            )
        if self.y.shape[0] != self.X.shape[0]:
            raise ValueError(f"y length ({self.y.shape[0]}) must match X rows ({self.X.shape[0]})")
        if len(set(self.features)) != len(self.features):
            raise ValueError(f"duplicate feature names in {self.features!r}")

    def select(self, columns: Sequence[str]) -> FloatMatrix:
        """Return the sub-matrix for `columns`, in the order given.

        An unknown column is an error, never a silent drop or an imputed zero — the method
        NEVER imputes (spec §3); a feature an agent expects but the data lacks is a
        construction bug to surface loudly.
        """
        index = {name: i for i, name in enumerate(self.features)}
        try:
            cols = [index[name] for name in columns]
        except KeyError as missing:
            raise KeyError(f"feature {missing.args[0]!r} is not in this dataset") from None
        return self.X[:, cols]


class ClassifierSpec(BaseModel, frozen=True, extra="forbid"):
    """Per-problem classifier configuration (spec §5.2). Config, not code: the reference
    architecture is a set of values here, never hard-coded into an agent.

    Frozen + ``extra="forbid"`` per the O3 ruling — a typo'd field is a `ValidationError`,
    not a silent default. Bounds encode the spec: ``epochs`` in [5, 50] (§5.2, ~20 the
    reference sweet spot); ``hidden_width`` default 32; Adam ``learning_rate`` 0.001;
    ``batch_size`` 32. The logreg variant ignores the MLP-shape knobs by design — that it
    still classifies is the point (§5.2).
    """

    variant: Literal["mlp", "logreg"] = "mlp"
    hidden_width: Annotated[int, Field(ge=1)] = 32
    epochs: Annotated[int, Field(ge=5, le=50)] = 20
    learning_rate: Annotated[float, Field(gt=0.0)] = 0.001
    batch_size: Annotated[int, Field(ge=1)] = 32


@runtime_checkable
class AgentClassifier(Protocol):
    """The classifier seam (spec §11: policies/wrappers are seams).

    `fit` takes the harness Generator and is the ONLY stochastic entry point. `predict`
    gives labels; `predict_proba_class1` gives P(class=1) under one documented convention
    (see the wrappers). Later phases (aggregation, confidence) read the probability; the
    arena reads the label.
    """

    def fit(self, x: FloatMatrix, y: LabelVector, rng: np.random.Generator) -> None: ...

    def predict(self, x: FloatMatrix) -> LabelVector: ...

    def predict_proba_class1(self, x: FloatMatrix) -> FloatMatrix: ...


def build_classifier(spec: ClassifierSpec) -> AgentClassifier:
    """Factory: the reference wrapper for `spec.variant`. The `Literal` type makes any
    other value unconstructible, so the trailing raise is defensive, not reachable."""
    if spec.variant == "mlp":
        return MLPAgentClassifier(spec)
    if spec.variant == "logreg":
        return LogisticRegressionAgentClassifier(spec)
    raise ValueError(f"unknown classifier variant {spec.variant!r}")


def _seed_from(rng: np.random.Generator) -> int:
    """One integer seed for sklearn, drawn from the threaded Generator.

    `rng.integers` is a method on the passed-in Generator, NOT a `numpy.random.*` module
    call — so the single-seed-origin contract (W0-04) holds and the RNG guard stays green.
    Drawing here advances the Generator, so successive agents in a crowd get distinct,
    reproducible seeds.
    """
    return int(rng.integers(0, _SEED_UPPER_BOUND))


def _class1_index(classes: object) -> int:
    """Column of P(class=1) in sklearn's `predict_proba` output: the position of label 1 in
    `classes_`. Raising when there is no positive class (a single-class training slice) is
    correct — P(class=1) is genuinely undefined there, not zero."""
    arr = np.asarray(classes)
    matches = np.flatnonzero(arr == 1)
    if matches.size == 0:
        raise ValueError("classifier saw no positive class (label 1); P(class=1) is undefined")
    return int(matches[0])


class MLPAgentClassifier:
    """Spec §5.2 reference: a small, shallow sklearn `MLPClassifier`.

    Depth = `hidden_layer_count(input_size)`, each layer `hidden_width` wide; Adam at
    `learning_rate`; mini-batch `batch_size`; `epochs` passes (`max_iter`). P(class=1)
    convention: the `predict_proba` column aligned to label 1 via `classes_` (§5.2's "pick
    one and be consistent"). The fit is pinned single-threaded (`threadpool_limits(1)`) so
    it is bit-reproducible from its seed — the plan §12-R3 warning, discharged.
    """

    def __init__(self, spec: ClassifierSpec) -> None:
        self._spec = spec
        self._model: MLPClassifier | None = None
        self._hidden_layer_sizes: tuple[int, ...] | None = None

    def fit(self, x: FloatMatrix, y: LabelVector, rng: np.random.Generator) -> None:
        layers = hidden_layer_sizes(self._spec, x.shape[1])
        model = MLPClassifier(
            hidden_layer_sizes=layers,
            activation="relu",
            solver="adam",
            learning_rate_init=self._spec.learning_rate,
            batch_size=self._spec.batch_size,
            max_iter=self._spec.epochs,
            random_state=_seed_from(rng),
        )
        # §12-R3: pin BLAS threads to 1 so matmul reductions are order-stable ⇒ the fit is
        # deterministic given the seed. A low epoch budget (spec §5.2: 5–50) will often not
        # "converge" in sklearn's sense; that ConvergenceWarning is expected and silenced.
        with threadpool_limits(limits=1), warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            model.fit(x, y)
        self._model = model
        self._hidden_layer_sizes = layers

    def predict(self, x: FloatMatrix) -> LabelVector:
        with threadpool_limits(limits=1):
            return np.asarray(self._require_model().predict(x), dtype=np.int_)

    def predict_proba_class1(self, x: FloatMatrix) -> FloatMatrix:
        model = self._require_model()
        with threadpool_limits(limits=1):
            proba = np.asarray(model.predict_proba(x), dtype=np.float64)
        return proba[:, _class1_index(model.classes_)]

    @property
    def architecture(self) -> tuple[int, ...] | None:
        """The fitted hidden-layer sizes (None before fit) — read-only, for the W2-04
        agent-table report."""
        return self._hidden_layer_sizes

    def _require_model(self) -> MLPClassifier:
        if self._model is None:
            raise RuntimeError("classifier used before fit()")
        return self._model


class LogisticRegressionAgentClassifier:
    """Spec §5.2 alternate: a logistic-regression agent.

    It exists to demonstrate the crowd is agnostic to agent internals — the MLP-shape knobs
    (`hidden_width`, `epochs`, `batch_size`) simply do not apply and are ignored. Seeded
    from the same Generator and pinned `n_jobs=1` + single-thread so it honours the same
    determinism contract (§12-R3).
    """

    def __init__(self, spec: ClassifierSpec) -> None:
        self._spec = spec
        self._model: LogisticRegression | None = None

    def fit(self, x: FloatMatrix, y: LabelVector, rng: np.random.Generator) -> None:
        model = LogisticRegression(
            random_state=_seed_from(rng),
            n_jobs=1,
            max_iter=_LOGREG_MAX_ITER,
        )
        with threadpool_limits(limits=1):
            model.fit(x, y)
        self._model = model

    def predict(self, x: FloatMatrix) -> LabelVector:
        with threadpool_limits(limits=1):
            return np.asarray(self._require_model().predict(x), dtype=np.int_)

    def predict_proba_class1(self, x: FloatMatrix) -> FloatMatrix:
        model = self._require_model()
        with threadpool_limits(limits=1):
            proba = np.asarray(model.predict_proba(x), dtype=np.float64)
        return proba[:, _class1_index(model.classes_)]

    def _require_model(self) -> LogisticRegression:
        if self._model is None:
            raise RuntimeError("classifier used before fit()")
        return self._model
