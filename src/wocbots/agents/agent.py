"""W2-01 — Agent state (spec §2) and the public profile (spec §6.5).

The §2 state table, executable and pinned. State only — no classifier (W2-02), no arena
mechanics (W3), no update rules (W3-03/W3-04/W4-02 own the mechanics that later mutate
this state). Nothing stochastic lands here: no RNG anywhere in this ticket.

Spec bindings: §2 (state table — names, ranges, inits are normative), §5.4 (confidence
blend), §6.5 (public-profile boundary), §6.6 (certainty reset), §6.7 (prior_* semantics).

Profile key note (mini-plan Q1, reported per preamble §0.2): ticket S2 says "prediction";
spec §6.5 and the preamble §7 exact-names rule say `current_prediction`. Spec wins.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

# Sum-to-one tolerance for confidence weights. The weights are per-problem config
# (spec §5.4); a sum off by more than float noise is a config bug.
_WEIGHT_SUM_TOL = 1e-9


class ConfidenceWeights(BaseModel, frozen=True, extra="forbid"):
    """The §5.4 bias weights (w_acc, w_prec, w_rec), summing to 1 (±1e-9).

    These encode "what does this problem care about": Hollywood biases precision; a
    medical dataset would bias recall. Per-problem CONFIG, never hard-coded into Agent.
    Frozen + extra="forbid" per the O3 ruling: a typo'd field is an ERROR, not a silent
    no-op.
    """

    w_acc: Annotated[float, Field(ge=0.0, le=1.0)]
    w_prec: Annotated[float, Field(ge=0.0, le=1.0)]
    w_rec: Annotated[float, Field(ge=0.0, le=1.0)]

    @model_validator(mode="after")
    def _sum_to_one(self) -> ConfidenceWeights:
        total = self.w_acc + self.w_prec + self.w_rec
        if abs(total - 1.0) > _WEIGHT_SUM_TOL:
            raise ValueError(f"weights must sum to 1 (±{_WEIGHT_SUM_TOL}), got {total!r}")
        return self


# Reference weights for Hollywood (spec §5.4): precision weighted highest.
HOLLYWOOD_WEIGHTS = ConfidenceWeights(w_acc=0.3, w_prec=0.5, w_rec=0.2)

# The exact §6.5 public-profile surface. Six fields, nothing else — this boundary is
# what the W8 meta-swarm privacy audit leans on. Widening it is a spec change, not a
# convenience.
_PROFILE_FIELDS = (
    "current_prediction",
    "certainty",
    "confidence",
    "trust_score",
    "prior_performance",
    "features",
)


class Agent:
    """The spec §2 state table, executable. State only — no classifier (W2-02).

    Naming is normative (preamble §7): certainty, trust_score, confidence,
    prior_performance, prior_accuracy — exactly these, no synonyms. The two performance
    notions are DIFFERENT THINGS (spec §2): prior_performance is a multiplier in
    [0.7, 1.3] (influence math); prior_accuracy is a rate in [0, 1] (vote allocation).
    Never swap them.

    Mutability contract:
    - certainty, trust_score, prior_performance, prior_accuracy, current_prediction:
      mutated later by W3-03/W3-04/W4-02 mechanisms.
    - confidence and the eval metrics: fixed after training (spec §2) — read-only
      properties, no setters.

    Replaces the W0-02 constructor-only stub; the seam import path
    `from wocbots.agents import Agent` is unchanged (tighten-never-loosen).
    """

    def __init__(
        self,
        *,
        features: Sequence[str],
        eval_accuracy: float,
        eval_precision: float,
        eval_recall: float,
        confidence_weights: ConfidenceWeights,
    ) -> None:
        # Eval metrics arrive as inputs: where they come from (the train-side eval
        # slice, never the test split — spec §10.5) is W2-02's business (ticket S1).
        for name, m in (
            ("eval_accuracy", eval_accuracy),
            ("eval_precision", eval_precision),
            ("eval_recall", eval_recall),
        ):
            if not 0.0 <= m <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {m!r}")
        if len(features) == 0:
            # Q6: an agent with no features is a construction bug. How many features an
            # agent SHOULD get is W2-03's assignment policy, not validated here.
            raise ValueError("an agent must have at least one feature")

        self._features: tuple[str, ...] = tuple(features)
        self._eval_accuracy = eval_accuracy
        self._eval_precision = eval_precision
        self._eval_recall = eval_recall

        # ---- §2 init formulas (pinned in tests; do not "simplify") ----
        self.certainty: float = (eval_accuracy + eval_precision) / 2
        self.trust_score: float = eval_precision
        self._confidence: float = (
            confidence_weights.w_acc * eval_accuracy
            + confidence_weights.w_prec * eval_precision
            + confidence_weights.w_rec * eval_recall
        )
        self.prior_performance: float = 1.0  # neutral cold start (spec §6.7)
        self.prior_accuracy: float = eval_accuracy  # eval-seeded until ≥5 scored (§6.7)

        # No classifier in this ticket: prediction is unset until Phase-2 inference
        # sets it (Q3). Never None during an arena round.
        self.current_prediction: Literal[0, 1] | None = None

        # Training-time certainty, retained for the §6.6 per-sample reset. Certainty
        # drift is evidence about ONE sample; it never carries over.
        self._certainty_train: float = self.certainty

    # ---- fixed-after-training state (spec §2), read-only ----

    @property
    def confidence(self) -> float:
        """§5.4 blend. Fixed after training; never updated at inference."""
        return self._confidence

    @property
    def eval_accuracy(self) -> float:
        return self._eval_accuracy

    @property
    def eval_precision(self) -> float:
        return self._eval_precision

    @property
    def eval_recall(self) -> float:
        return self._eval_recall

    @property
    def features(self) -> tuple[str, ...]:
        """Assigned at creation (W2-03's policy), fixed thereafter."""
        return self._features

    # ---- the §6.5 boundary ----

    def public_profile(self) -> Mapping[str, object]:
        """Read-only snapshot of exactly the six §6.5 fields.

        Snapshot-per-call: a partner reads it once during an interaction. Private
        internals (classifier, data, history, eval metrics, prior_accuracy) are NEVER
        exposed — this locality is the meta-swarm privacy argument (W8-03). Matches the
        W0-02 `ScoringPolicy.update_prediction(partner_profile: Mapping[str, object])`
        seam. Widening this mapping is a contract change.
        """
        return MappingProxyType(
            {
                "current_prediction": self.current_prediction,
                "certainty": self.certainty,
                "confidence": self._confidence,
                "trust_score": self.trust_score,
                "prior_performance": self.prior_performance,
                "features": self._features,
            }
        )

    # ---- §6.6 reset hook (caller: W4-01's per-sample loop — Q4) ----

    def reset_certainty(self) -> None:
        """Reset certainty to its training-time value (spec §6.6, MUST).

        trust_score, prior_performance, prior_accuracy and history persist — they are
        the crowd's long-term social memory. Skipping this reset is fine for 50 samples,
        then the crowd ossifies (forbidden-shortcut register).
        """
        self.certainty = self._certainty_train
