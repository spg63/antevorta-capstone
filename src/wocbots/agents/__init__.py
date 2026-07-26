"""Agent layer (AGENTS stream). W2-01 lands Agent state + the §6.5 profile boundary.

The W0-02 constructor-only stub is replaced; the seam import path
`from wocbots.agents import Agent` is unchanged (tighten-never-loosen).
"""

from wocbots.agents.agent import HOLLYWOOD_WEIGHTS, Agent, ConfidenceWeights

__all__ = ["HOLLYWOOD_WEIGHTS", "Agent", "ConfidenceWeights"]
