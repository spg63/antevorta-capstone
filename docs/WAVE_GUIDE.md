# The Waves, in Plain English

This is a companion to `tickets/00_INDEX.md`. It explains what each wave is *for* and what you're
actually building in it, without the governance vocabulary. The index is still the authority for
ticket IDs, blockers, and status — when this document and the index disagree, the index wins.

**The one idea to hold onto:** the project builds a "wisdom of crowds" prediction system. Instead of
one big machine-learning model, we train many small classifier agents, each seeing only a few
features of the data. The agents then "socialize" in a simulated arena — meeting, comparing
opinions, and adjusting how sure they are — before the crowd votes on a final yes/no prediction with
a confidence label. Every wave below builds one layer of that system.

**What a "wave" is:** a wave is a *when*, not a *who*. Tickets in the same wave can be worked in
parallel by different students; a ticket only has to wait for the specific tickets in its
"Blocked by" column. Waves W1, W2, and W3 largely run at the same time — the numbering is
dependency order, not calendar order.

---

## Wave W0 — Scaffold: the empty workshop

**Question it answers: "Where does code go, and how do we know it works?"**

Before anyone writes a line of the actual method, W0 sets up the repository so five people can work
in it without stepping on each other: packaging, the check suite (ruff, mypy, pytest), CI, and PR
rules (W0-01); the shared type definitions and the five "policy seams" — the agreed interfaces that
let each stream build against the others' code before that code exists (W0-02); the experiment
configuration and results-manifest models, so every experiment is recorded as config + seed + git
SHA (W0-03); and the harness runner with seed discipline and the RNG guard, which enforces the
"one seeded random generator, no wall-clock" rule mechanically (W0-04).

W0 blocks everything else, which is why it comes first and why it has the most formal plans.

## Wave W1 — Hollywood data: the first dataset

**Question it answers: "What are we predicting, and is the data trustworthy?"**

W1 turns raw movie data into a clean, labeled, split dataset the rest of the project can trust.
It runs the full pipeline: acquire the raw data with provenance records (W1-01), build ground truth
from `antevorta-db` (W1-02), join and clean the features (W1-03), attach labels and pass the
validation *gate* — the checkpoint where label disputes escalate to the stakeholder instead of
being decided locally (W1-04), cut train/eval/test splits with leakage guards (W1-05), and finally
analyze the "anchor" features that agents will be built around (W1-06).

W1-01 has no blockers at all — the DATA stream starts on day one, in parallel with W0.

## Wave W2 — Agent layer: the individual voters

**Question it answers: "What is one agent, and how does it learn?"**

W2 builds the small classifiers that make up the crowd. That means the agent's internal state and
public profile exactly as the spec §2 defines them (W2-01); training, evaluating, and pruning the
classifiers, plus the special sanity-check agent used only to validate the pipeline (W2-02);
assigning features to agents and assembling a whole crowd (W2-03); and reproducing the spec's
agent table as the wave's closing experiment — proof the agents behave the way the published
method says they should (W2-04).

## Wave W3 — Interaction arena: where agents meet

**Question it answers: "How do agents socialize?"**

W3 is pure logic — no dataset needed — so it runs in parallel with W1 and W2. It builds the
simulated space where agents interact: the grid geometry and random placement (W3-01); movement
rules, the anti-clique mechanism that stops the same agents from always talking to each other, and
the lockstep round structure (W3-02); the interaction kernel itself — when two agents meet, how
their certainty updates and when one flips its opinion (W3-03); and the history store and trust
updates, so agents remember who they've met and learn whom to believe (W3-04).

## Wave W4 — Lifecycle and voting: the crowd decides

**Question it answers: "How does one prediction actually happen, start to finish?"**

W4 wires agents and arena together into the per-sample loop. For each sample: select which agents
participate (agents missing a feature sit out — the method never imputes), size the arena from the
participant count, and reset certainty (W4-01); after the answer is revealed, feed ground truth
back into each agent's prior-performance multiplier, including the degenerate rule for tiny crowds
(W4-02); implement the three voting aggregators — unweighted majority, weighted vote, and
trust-weighted (W4-03); and run the tier comparison experiment showing that each added layer of
the mechanism (tier 3 > tier 2 > tier 1) actually improves results (W4-04).

W4-01 is the first hard cross-stream integration point — CORE consumes AGENTS' and ARENA's work
here — and one of the two named schedule risks.

## Wave W5 — Baseline and Q1 reproduction: does it beat one big model?

**Question it answers: "Is the crowd actually better than the obvious alternative?"**

W5 is the payoff of the first quarter. Build the monolithic MLP baseline — one conventional neural
net trained on everything (W5-01) — then run the matched head-to-head comparison against the crowd
(W5-02), the feature-removal robustness contrasts (W5-03), and the 26-agent scaling run (W5-04).
W5-05 assembles the Q1 report and exit audit: **this ticket is the Q1 exit** — everything from
W0 through W5 converges here, and every reported number is a 10-run mean ± std backed by a
committed manifest.

## Wave W6 — Honeybee swarm: earning a confidence label

**Question it answers: "How sure is the crowd, and can it say so honestly?"**

Q2 begins here. W6 adds the second aggregation mechanism, modeled on honeybee decision-making:
the swarm round primitive, where "presenter" agents pitch their view and others reassign themselves
via a fitness wheel (W6-01); the confidence ladder and group interactions that convert swarm
behavior into an earned High/Medium/Low confidence label rather than a made-up one (W6-02); and
the variance study comparing swarm output against the weighted vote and calibrating the confidence
bands (W6-03).

## Wave W7 — Second dataset: proving it generalizes

**Question it answers: "Does this work on data it wasn't designed around?"**

W7 repeats the story on airline data, which brings *structured missingness* — real gaps the
method's sit-out rule must handle gracefully. It covers the airline ETL and label rule (W7-01),
airline-specific anchors and crowd configurations at larger scale (W7-02), conventional baselines
to compare against — XGBoost, random forest, logistic regression (W7-03), the full comparison grid
across datasets, mechanisms, and baselines (W7-04), a deletion-mask protocol for deliberately
removing data (W7-05), and the missing-data tolerance curves that show how the crowd degrades as
data disappears (W7-06). A key rule enforced throughout: nothing Hollywood-specific may live in
the toolkit core.

## Wave W8 — Distinctive capabilities: the publication

**Question it answers: "What can this method do that a monolithic model can't?"**

Q3 is the research payoff — the capabilities that justify a paper. Incremental feature injection:
add a new feature to a live crowd by adding agents, no retraining of everyone (W8-01), with a
study measuring the lift and cost of holding features back (W8-02). An external-prediction agent
that lets another organization's model join the crowd without sharing its data, plus the privacy
audit (W8-03), and a federated meta-swarm study built on it (W8-04). Auto-tuned confidence
thresholds (W8-05). And the final report assembly, which has been accreting since the Q1 report
(W8-06).

---

## Quick reference

| Wave | One-line summary | Quarter |
|---|---|---|
| W0 | Repo, types, config, harness — the workshop everything is built in | Q1 |
| W1 | Hollywood data: acquire → clean → label → split | Q1 |
| W2 | The agents: small classifiers with state, training, and pruning | Q1 |
| W3 | The arena: grid, movement, interactions, trust | Q1 |
| W4 | The loop: pick participants, interact, vote, learn from the answer | Q1 |
| W5 | Beat the single big model — **Q1 exit at W5-05** | Q1 |
| W6 | Honeybee swarm: an earned confidence label | Q2 |
| W7 | Airline data: generalization and missing-data tolerance | Q2 |
| W8 | Feature injection, federation, auto-tuning — the paper | Q3+ |

**Waves vs streams, one more time:** waves say *when* a ticket may start (its blockers must be ✅);
streams say *who* owns it (CORE, DATA, AGENTS, ARENA, EVAL — one writer per directory). A wave is
not a sprint the whole team does together: in week one, DATA is in W1 while CORE and EVAL are in
W0 and AGENTS/ARENA are reading spec sections for W2/W3.
