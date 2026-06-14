# Product Framing

PokerLab is a productized AI coaching and simulation tool for strategic decision-making under uncertainty.

## User Workflows

### Train

The app generates a poker scenario, asks the user to choose an action and estimate hand strength, then grades the response against model-backed EV estimates and Monte Carlo equity.

### Analyze

The user inputs a hand state. The backend estimates equity, extracts features, predicts action EVs, and returns a recommended action with explanation text.

### Simulate

The user selects two agents and runs a seeded head-to-head simulation. The app returns profitability, behavior metrics, hand summaries, and bankroll curves.

### Strategy Lab

The user describes a strategy in natural language. The app parses it into an executable policy config, allows parameter editing, and benchmarks it against baseline agents.

### Diagnose

The user asks PokerLab to compile and diagnose a strategy. The backend runs the compiled strategy against several baselines, identifies the weakest matchup, assigns an aggregate score, and returns structured leak reports with evidence and suggested parameter changes.

### Optimize

The diagnosis engine generates candidate strategy patches from detected leaks, backtests those candidates, and recommends the best-performing policy variant. The UI shows original score, improved score, parameter changes, and candidate rankings.

## Why This Matters

The project demonstrates a complete product loop:

- user intent in natural language
- structured strategy representation
- simulation-based experimentation
- strategy leak detection
- simulation-driven policy optimization
- model-backed recommendations
- metrics and visual feedback

This maps to AI product work beyond poker: sales strategy testing, negotiation simulators, trading sandboxes, operational decision support, and policy optimization tools.

## Resume Positioning

Primary framing:

> Built an end-to-end AI decision-support platform for strategic decision-making under uncertainty.

Supporting claims:

- custom simulation engine
- generated supervised training data from simulated agents
- engineered a shared 40-feature model input pipeline
- trained and evaluated multiple ML models
- exposed inference and experiments through FastAPI
- built an interactive Next.js dashboard
- translated natural-language user intent into executable strategies

## Demo Script

1. Open Strategy Lab.
2. Enter: `Play tight preflop, c-bet dry boards often, avoid big river bluffs`.
3. Run a natural-language strategy experiment against TAG.
4. Run Compile and Diagnose.
5. Show parsed config, matchup table, aggregate score, leaks, recommended parameter changes, and optimized strategy patch.
6. Apply the recommended patch.
7. Open Simulate and compare TAG vs LAG.
8. Open Analyze and show action EV recommendations.
