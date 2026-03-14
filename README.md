# PokerLab

ML-driven poker training and simulation platform. Train your poker intuition, analyze hands, simulate agent matchups, and test natural-language strategies.

## Features

- **Train** — Practice poker scenarios with ML-powered feedback on hand strength, action quality, and bluff detection
- **Analyze** — Input any hand and get equity estimates, action recommendations, and opponent modeling
- **Simulate** — Run 1000+ hand simulations between different agent types and view bankroll charts
- **Strategy Lab** — Describe strategies in plain English, parse them into structured configs, and test profitability

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
python3 backend/scripts/train_models.py

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

## Agents

| Agent | Style | Description |
|-------|-------|-------------|
| Random | — | Uniformly random legal action |
| TAG | Tight-Aggressive | Premium hands only, bets strong |
| LAG | Loose-Aggressive | Wide range, frequent bluffs |
| CallingStation | Passive | Calls almost everything |
| MLAgent | ML-driven | Uses trained EV model for decisions |
| Custom | Configurable | Driven by parsed strategy config |
