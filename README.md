# PokerLab

ML-driven poker training and simulation platform. PokerLab is an end-to-end AI decision-support product for strategic decision-making under uncertainty: it simulates hands, generates training data, trains predictive models, parses natural-language strategies, and serves model-backed recommendations through an interactive web app.

## Features

- **Train** — Practice poker scenarios with ML-powered feedback on hand strength, action quality, and bluff detection
- **Analyze** — Input any hand and get equity estimates, action recommendations, and opponent modeling
- **Simulate** — Run 1000+ hand simulations between different agent types and view bankroll charts
- **Strategy Lab** — Describe strategies in plain English, parse them into executable configs, and benchmark profitability against baseline agents
- **Diagnose + Optimize** — Stress-test natural-language strategies across baselines, detect leaks, and recommend parameter-level policy patches
- **Evaluate** — Generate model metrics, feature importances, and seeded agent backtests for reproducible ML evaluation

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI / scikit-learn (Random Forests) / treys
- **Frontend:** Next.js / React / TypeScript / Tailwind CSS / Recharts
- **ML Models:** Hand strength predictor, opponent model, bluff detector, EV estimator

## Quick Start

```bash
# 1. Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# 2. Generate training data and train models
python3 backend/scripts/generate_data.py
python3 backend/scripts/generate_ev_data.py
python3 backend/scripts/train_models.py
python3 backend/scripts/evaluate_models.py

# 3. Start backend (terminal 1)
python3 -m uvicorn backend.main:app --reload --port 8000

# 4. Start frontend (terminal 2)
cd frontend && npm run dev
```

Then open http://localhost:3000

## Project Structure

```
backend/
  poker_engine/     # Card handling, game state, betting rules, showdown
  feature_engineering/  # 40-feature extraction from game states
  data_generation/  # Monte Carlo equity, simulation, training data pipelines
  models/           # Random Forest models (hand strength, opponent, bluff, EV)
  agents/           # Random, TAG, LAG, CallingStation, ML, ConfigPolicy agents
  strategy_language/ # NL parser, strategy schema, defaults
  evaluation/       # Profitability metrics, model evaluation
  api/              # FastAPI routes and schemas
frontend/
  pages/            # Train, Analyze, Simulate, Strategy Lab
  components/       # PokerCard, CardSelector, layout, charts
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check + model status |
| `/api/analyze-hand` | POST | Analyze a hand scenario |
| `/api/training-scenario` | GET | Get a random training scenario |
| `/api/grade-scenario` | POST | Grade user's answer |
| `/api/simulate` | POST | Run agent vs agent simulation |
| `/api/parse-strategy` | POST | Parse natural language strategy |
| `/api/strategy-experiment` | POST | Parse and benchmark a natural-language strategy |
| `/api/strategy-diagnose` | POST | Compile, stress-test, diagnose leaks, and optimize strategy parameters |

## Agents

| Agent | Style | Description |
|-------|-------|-------------|
| Random | — | Uniformly random legal action |
| TAG | Tight-Aggressive | Premium hands only, bets strong |
| LAG | Loose-Aggressive | Wide range, frequent bluffs |
| CallingStation | Passive | Calls almost everything |
| MLAgent | ML-driven | Uses trained EV model for decisions |
| Custom | Configurable | Driven by parsed strategy config |

## Evaluation

After training models, run:

```bash
python3 backend/scripts/evaluate_models.py
```

This writes `backend/artifacts/evaluation_report.json` with held-out model metrics, confusion matrices, feature importances, and seeded agent-vs-agent backtests.

For a stronger EV model, run `python3 backend/scripts/generate_ev_data.py` before training. This creates counterfactual state-action labels by estimating the EV of every legal action from sampled decision states instead of only learning from the one action that was actually taken.

## Portfolio Framing

PokerLab is best described as an AI decision-support platform, not just a poker app. It demonstrates:

- simulation-based data generation
- supervised ML pipelines
- model evaluation and baselines
- natural-language strategy configuration
- simulation-based leak detection
- simulation-driven policy optimization
- FastAPI inference and experimentation APIs
- Next.js product interface for analysis, training, and simulation

See `docs/architecture.md`, `docs/modeling.md`, and `docs/product.md` for implementation details and project positioning.
