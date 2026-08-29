# From Dissertation to Codebase: A WoC-Bots Onboarding Guide

*How Dr. Grimes's dissertation ("WoC-Bots: Swarms of Biologically Inspired Prediction Agents,"
Drexel University, 2023) maps onto the `antevorta-capstone` ("WoC-Bots Reimagined") codebase —
written for someone joining the project with no prior context.*

---

## 1. What this document is (and isn't)

This guide answers one question: **"When the dissertation talks about X, where does X live in
the code, and how far along is it?"**

It is *not* a replacement for the two documents you actually need to read before writing any
code:

1. `docs/WoC-Bots_Implementation_Spec.md` — the team's own translation of the dissertation into
   exact build rules (initialization values, formulas, edge cases). This is the project's
   **source of truth**, not the dissertation itself.
2. `tickets/01_MANDATORY_PREAMBLE.md` — the binding rules for how work gets done (session
   protocol, review requirements, testing discipline).

Think of this guide as the map that sits *between* the dissertation and the spec/code — it tells
you which chapter explains which mechanism, which module implements it, and whether that piece
has actually been built yet.

---

## 2. The one-paragraph idea

The dissertation's core proposal, and the thing the whole codebase exists to reproduce and then
extend, is this:

> Instead of training one big classifier on all the data (a "monolithic model"), train **many
> small, simple classifiers** ("agents"), each seeing only a handful of features. Give the agents
> opinions, drop them into a simulated 2D space where they wander around and bump into each
> other, and let them **argue**: when two agents meet, they compare predictions and each one's
> confidence in its own answer shifts based on how trustworthy and confident the other one seems.
> After a while, collect everyone's final opinion into a single prediction — first by a weighted
> vote, later by a more elaborate "honeybee swarm" consensus process that also reports *how
> confident* the crowd is, not just what it predicted.

This is a **Wisdom of Crowds (WoC)** approach: a diverse group of mediocre-but-independent
opinions, properly combined, can beat one expert. The dissertation calls the individual agents
"WoC-Bots."

---

## 3. Dissertation chapters ↔ project structure, at a glance

| Dissertation chapter | What it covers | Codebase area | Project wave(s) |
|---|---|---|---|
| Ch. 1 — Introduction | Motivation, scientific merit | `README.md`, `docs/WoC-Bots_Implementation_Spec.md` §1 | — |
| Ch. 2 — Chemotaxis-based self-organization | Earlier, separate line of work (not WoC-Bots) | *not part of this capstone* | — |
| **Ch. 3 — Wisdom of Crowd Bots: Hollywood Movie Classification** | Agents, the interaction arena, trust-weighted voting, Hollywood results | `src/wocbots/data/`, `agents/`, `arena/`, `interaction/`, `aggregation/voting.py` | **W1–W5 (Q1)** |
| **Ch. 4 — Swarm-based Opinion Aggregation** | The honeybee swarm mechanism, confidence labels | `src/wocbots/aggregation/` (swarm), applied to a breast-cancer dataset in the dissertation, to Hollywood/Airline here | **W6 (Q2)** |
| Ch. 5 — Incremental Feature Addition | Adding new agents for new features without retraining | future `experiments/` injection API | **W8-01/02 (Q3+)** |
| Ch. 6 — Distributability | Distributed processing, "meta-swarm" (external models as agents) | future work | **W8-03/04 (Q3+)** |
| Ch. 7 — Classification Method Comparison & Application | Second dataset, baselines (XGBoost/RF/logreg), applying the method broadly | `data/` (airline ETL), `evaluation/` baselines | **W7 (Q2)** |
| Ch. 8 — Summary & Future Directions | Wrap-up, publications | — | — |

**Key thing to internalize:** the dissertation's Chapter 3 (Hollywood) and Chapter 4 (swarm,
demonstrated on a breast-cancer dataset) describe the *same underlying method* — training,
arena, interaction — with two different final aggregation steps bolted on. The capstone project
builds the method once, generically, and applies **both** aggregation mechanisms to **both**
datasets (Hollywood now, Airline in Q2), which is more thorough than either dissertation chapter
individually.

---

## 4. Walking through the method: dissertation section → code

### 4.1 The data (dissertation §3.2)

**Dissertation:** Two Kaggle datasets — TMDb 5000 Movies and MovieLens 20M — are joined on movie
identity. After dropping rows with impossible values (budget/revenue ≤ 0), the dissertation
reports **4,722 matched movies, 1,023 dropped, leaving a usable set** for an 80/20 train/test
split. The prediction task: will a movie make more than **2× its production budget** in revenue?
That threshold splits the data roughly 47.5% success / 52.5% failure.

**Code:** `src/wocbots/data/hollywood.py` (the join + cleaning + combined-feature logic),
`src/wocbots/data/labels.py` (the 2×-budget label), `src/wocbots/data/splits.py` (80/20 split +
normalization). The spec restates all of this as normative rules in
`docs/WoC-Bots_Implementation_Spec.md` §4.

**Status:** Built (tickets W1-01 through W1-05), but flagged as a live problem — see §6 below.
The team's current real-data join produces **4,227 movies at a 43.93/56.07 class balance**,
short of the dissertation's 4,722 / 47.5-52.5 numbers, and this has been escalated to the
stakeholder rather than silently "fixed."

### 4.2 The agents (dissertation §3.3)

**Dissertation:** Each agent wraps a small MLP: 2–10 input features, 1–4 hidden layers
(`round(0.3 × input_size)`), softmax output. Every agent shares a small set of highly-correlated
"anchor" features (determined via PCA) with every other agent; the rest of its features are
assigned randomly. Agents scoring below 50% accuracy on held-out data are pruned. Each agent also
gets a `confidence` score — a weighted blend of its accuracy, precision, and recall (Eq. 3.2).

**Code:** `src/wocbots/agents/agent.py` (the state fields — a direct, literal transcription of
the dissertation's Table 3.2), `agents/classifier.py` (the MLP wrapper and the
`round(0.3 × input_size)` hidden-layer-count rule), `agents/training.py` (train/eval/prune),
`agents/crowd.py` (feature assignment across a crowd).

**Status:** Built (tickets W2-01 through W2-03), but its results reproduction (W2-04) is
currently **out of band** — see §6.

**Worth knowing:** the dissertation's own confidence formula in Ch. 3 (Eq. 3.2) is
`accuracy×0.25 + precision×0.25 + recall×0.50` ("to avoid false-negative predictions"). The
implementation spec instead directs the Hollywood configuration to weight **precision** highest
— `(w_acc, w_prec, w_rec) = (0.3, 0.5, 0.2)` — and that is what's actually coded
(`HOLLYWOOD_WEIGHTS` in `agents/agent.py`, and `configs/crowd_hollywood_26agent.yaml`). The
0.25/0.25/0.50 recall-biased version the dissertation shows for Hollywood is closer to what the
spec suggests for a *medical* dataset. This is a small but real discrepancy between the literal
dissertation text and what's built — good one to ask the stakeholder about if it comes up.

### 4.3 The interaction arena (dissertation §3.4)

**Dissertation:** For each sample being classified, participating agents are placed at random
empty cells of a 2D grid (sized so the arena holds roughly twice as many cells as agents). Over a
number of rounds, each agent takes one random cardinal step; landing on an occupied cell triggers
a pairwise interaction. Two agents can't interact twice in a row, or more than twice in any
5-round window ("anti-clique" rules); agents that can't legally move are teleported. This is how
information disperses through the crowd using only *local* interactions — no agent ever sees the
whole crowd's opinion at once.

**Code:** `src/wocbots/arena/arena.py` (grid geometry, 2-per-cell capacity),
`arena/init_policy.py` (random placement), `arena/movement_policy.py` (the cardinal-step +
anti-clique + teleport rules), `arena/round_engine.py` (the synchronous move-then-interact round
loop).

**Status:** Grid geometry and random init are built and reviewed (W3-01, ✅). Movement is built,
pending independent review (W3-02, ◐). **Not yet started:** the interaction math itself — see
next section.

### 4.4 Certainty, trust, and the flip rule (dissertation §3.4.2, Eqs. 3.3–3.10)

**Dissertation:** This is the heart of the method and the part most worth reading closely
(dissertation pages 40–43; spec §6.5, which includes a fully worked numeric example). When agent
*a* meets agent *b*:

- *a*'s **acceptance** (open-mindedness) is `1 − a.certainty` — the less sure *a* already is, the
  more it listens.
- *b*'s **influence** on *a* depends on *b*'s confidence, *a*'s acceptance, and how much *a*
  should trust *b* (*b*'s trust score × *b*'s own certainty), further scaled by *b*'s long-run
  track record (`prior_performance`).
- If *a* and *b* disagree, that influence works *against* a's belief instead of for it.
- *a*'s certainty is updated by that (possibly negative) amount. If it drops below 0.5, *a*
  **flips its predicted class** and its certainty becomes `1 − certainty` — it now believes the
  new answer exactly as strongly as it doubted the old one.
- Separately, *b*'s trust score can move by up to ±5% based on whether *a*'s past experience with
  *b* has been accurate and whether they currently agree (Eq. 3.10).

One confident, trustworthy dissenter can flip a lukewarm agent's mind. That's the mechanism by
which information spreads through the crowd.

**Code:** this lives in `src/wocbots/interaction/`, which is where `InteractionPolicy` and
`ScoringPolicy` (the certainty/trust math) are meant to go per the spec's toolkit shape (§11).

**Status: not yet built.** As of this writing, `interaction/` is an empty package
(`__init__.py` only). This is the next major piece of work (tickets W3-03 "the interaction
kernel" and W3-04 "history + trust updates"), and a lot else is blocked behind it — including the
full arena integration (W4-01) and, further downstream, the honeybee swarm (W6, which reuses this
same interaction math inside its swarm rounds).

### 4.5 Aggregation, mechanism 1 — voting (dissertation §3.5)

**Dissertation:** Three vote-based ways to turn the crowd's post-interaction opinions into one
prediction, presented in increasing sophistication:

1. **UWM (Unweighted Mean Model):** every agent gets 100 votes for its class. Simple majority.
2. **WVM (Weighted Voter Model):** an agent's votes scale with its prior accuracy (an 80%-accurate
   agent gets 80 votes); 50 votes as a neutral default before an accuracy can be established.
3. **Trust-weighted voting (the dissertation's own contribution):** votes scale with the average
   of prior accuracy *and* the trust score other agents have assigned it during interaction —
   `votes = round(((prior_accuracy + trust) / 2) × 100)`.

On the Hollywood data, mechanism 3 is expected to beat mechanisms 1 and 2.

**Code:** `src/wocbots/aggregation/voting.py` (all three mechanisms),
`aggregation/tiers.py` (a cheap vote-margin-based confidence bucket — a simpler cousin of the
swarm's confidence ladder in §4.6 below).

**Status:** Built (W4-03 implemented, pending merge/review); the tie-breaking rule (ties go to
class 1), vote-margin tiers, and the three-mechanism comparison experiment (W4-04) are also in
place. This piece currently sits downstream of the missing interaction math (§4.4) for full
end-to-end runs, since voting consumes the `trust_score`/`prior_accuracy` values that interaction
updates.

### 4.6 Aggregation, mechanism 2 — the honeybee swarm (dissertation Ch. 4)

**Dissertation:** Chapter 4 replaces the vote-counting aggregation with a process modeled on
honeybee foraging, and — notably — demonstrates it on a *different* dataset: breast-cancer
lymph-node metastasis prediction, not Hollywood movies. Roughly 20% of participating agents are
selected as "presenters"; the rest ("watchers") are assigned to a presenter via
fitness-proportionate (roulette-wheel) selection, with a limited ability for a strongly-opinionated
watcher to re-roll if it disagrees with its presenter. Each presenter's opinion carries a vote
weight equal to 1 plus its assigned watchers. This repeats across a bounded number of rounds, and
the *round* at which the crowd reaches consensus becomes a **confidence label**:

- Unanimous agreement on the very first round → **Very High** confidence.
- ≥90% agreement within the next chunk of rounds → **High**.
- ≥75% agreement in a further chunk → **Medium**.
- Otherwise, fall back to a certainty-weighted vote of everyone → **Low**.

On the dissertation's breast-cancer data, this produced a clean, monotonic result: Very High
predictions were 100% accurate, High 93.1%, Medium 82.3%, Low 64.7% — and dropping the Low band
raised overall accuracy from ~80% to 86.8% while keeping ~79% of the samples. Confidence isn't
just a label here; it's a genuinely useful filter.

**Code:** intended for `src/wocbots/aggregation/` alongside `voting.py` and `tiers.py`, per the
project's toolkit shape.

**Status: not yet built** (tickets W6-01 through W6-03). This is a Quarter 2 deliverable and
depends on the interaction math (§4.4) being finished first, since swarm rounds run the same
certainty/trust interaction logic among watchers.

### 4.7 A second dataset, baselines, and the fuller comparison (dissertation Ch. 7)

**Dissertation:** Chapter 7 broadens the evaluation — additional datasets and a comparison
against standard baselines (a monolithic MLP, and in the capstone's plan, also XGBoost, random
forest, and logistic regression).

**Code / plan:** the capstone's Quarter 2 introduces the Kaggle **Airline Passenger
Satisfaction** dataset (~120,000 samples, 22 features) specifically because its 1–5
satisfaction ratings use `0` to mean "not applicable" — a real-world instance of the missing-data
story the method already handles for free (an agent missing its required feature just sits out a
sample). Planned modules: `data/` (airline ETL), `evaluation/` (XGBoost/RF/logreg baseline
wrappers).

**Status: not started** — Quarter 2 work (tickets W7-01 through W7-06), blocked behind the
Quarter 1 exit.

### 4.8 The distinctive capabilities (dissertation Ch. 5 & 6)

**Dissertation:** Two properties the architecture buys that a monolithic model can't easily
match:

- **Incremental feature addition (Ch. 5):** when a new feature becomes available, train a new
  agent for it and drop it into the crowd — no retraining of existing agents required.
- **Distributability (Ch. 6):** because agents only share a small public profile (prediction,
  certainty, confidence, trust, prior performance — never raw data or the classifier itself), the
  crowd can be spread across machines, and an agent's "classifier" can even be another
  institution's external model prediction standing in — a **meta-swarm** that aggregates across
  institutions without anyone sharing data.

**Code / plan:** future `experiments/` injection API (adding agents without retraining) and an
external-prediction agent type + a "federated" experiment.

**Status: not started** — this is Quarter 3+ work (tickets W8-01 through W8-05), the part of the
project explicitly reserved for producing a new, publishable contribution beyond replication.

---

## 5. How the team's process works (so the tickets make sense)

The repo is organized as **42 tickets across 9 "waves" (W0–W8)**, each wave being a dependency
stage, with **5 students each owning a "stream"** (a subsystem) across all waves:

| Stream | Owns | Roughly corresponds to |
|---|---|---|
| **DATA** | `data/` | §4.1 above |
| **AGENTS** | `agents/` | §4.2 above |
| **ARENA** | `arena/`, `interaction/` | §4.3–4.4 above |
| **CORE** | `experiments/`, `aggregation/`, `protocols.py` | §4.5–4.6 above |
| **EVAL** | `evaluation/`, baselines, the report | §4.7 above |

Precedence when documents disagree: **the implementation spec > a ticket's plan > the ticket
itself** — and if the spec seems to contradict the dissertation, that's treated as something to
raise with the stakeholder (Dr. Grimes), never something to quietly reconcile. There's also a
strict **clean-room rule**: the only prior code the team may consult is the `antevorta-db` data
module; nobody looks for "how the original research code did it" beyond the spec and the
publications.

Every ticket needs a written mini-plan, a green check suite, a committed **results manifest**
(config + seed + git commit hash, so any reported number can be regenerated), and sign-off from
someone who did *not* implement it before it's marked done (✅).

---

## 6. Current status snapshot (as of the last handoff, mid-August 2026)

For a newcomer, the most useful thing to know is: **Quarter 1 (replicating dissertation Chapter
3 on the Hollywood dataset) is roughly two-thirds built, and its central reproduction check is
currently failing in a documented, escalated way — not silently.**

- **Solid ground:** data ETL, splits, and the agent layer (train/eval/prune) are implemented;
  grid geometry, random initialization, and movement are implemented; all three voting
  mechanisms and the vote-margin confidence tiers are implemented.
- **Not yet built:** the interaction/certainty/trust math (§4.4) — everything downstream of it
  (full arena integration, the honeybee swarm) is blocked waiting on it; the baseline MLP and the
  Quarter-1 exit report; anything from Quarter 2 or 3 (swarm, second dataset, baselines beyond
  the monolithic MLP, incremental features, distribution).
- **A flagged, unresolved discrepancy:** reproducing the dissertation's §9.2 reference numbers
  (the reference spec's restatement of Table 3.3 / the crowd-level results) currently **misses
  its target bands**. The real MovieLens/TMDb join yields 4,227 movies at a 43.93/56.07 class
  balance, versus the dissertation's 4,722 movies at 47.5/52.5 — and a re-run anchor-feature
  analysis currently ranks `budget` as the *least* correlated feature, rather than the anchor
  feature every agent is supposed to share. This has been escalated to the stakeholder for a
  ruling rather than adjusted to fit; if you're picking up data-pipeline work, `tickets/
  W1-06_anchor-analysis.md` and `results/W2-04_agent_table_comparison.md` are where that
  conversation lives.
- **Process note:** several completed-looking pieces of work are marked "implemented, pending
  independent review" rather than ✅ — the team's rule is that no one can review their own work,
  so a chunk of what looks done is functionally still awaiting a second set of eyes.

If you want the single most current account of "what's true right now," read `AGENT_HANDOFF.md`
at the repo root — it's the team's living state journal and is kept more current than any
document like this one.

---

## 7. Reading order for a new team member

1. This document, for orientation.
2. `README.md` — setup, branch structure, the reproducibility contract.
3. `docs/WoC-Bots_Implementation_Spec.md` — the actual build rules (§1–§3 for the big picture,
   then whichever of §4–§9 covers your stream).
4. Dissertation Chapter 3 (Hollywood) in full, then Chapter 4 (swarm) — now that you have the
   vocabulary, the equations and figures will make sense quickly.
5. `tickets/01_MANDATORY_PREAMBLE.md`, then `tickets/00_INDEX.md` to find your stream's next open
   ticket.
6. `AGENT_HANDOFF.md` for exactly where things stand today.
