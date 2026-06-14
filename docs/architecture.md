# PokerLab Architecture

PokerLab is an end-to-end AI decision-support platform for heads-up no-limit hold'em. It combines a custom simulator, feature engineering, learned models, strategy parsing, FastAPI inference routes, and a Next.js product surface.

## System Components

### Poker Engine

`backend/poker_engine/` owns hand state and game mechanics:

- deals deterministic seeded hands
- posts blinds
- tracks pot, stack, board, street, actor, and action history
- computes legal actions
- applies fold/check/call/bet/all-in actions
- advances streets and runs all-in boards
- resolves showdown with `treys`

The engine is intentionally heads-up and uses bucketed bet sizes: small, medium, large, and all-in.

### Feature Pipeline

`backend/feature_engineering/` converts a `GameState` into a fixed 40-feature vector.

Feature groups:

- card strength and preflop hand group
- board texture
- position and street context
- pot, stack, SPR, and pot odds
- betting history and aggression patterns

This feature vector is shared by model training, API recommendations, training scenarios, and ML-driven agents.

### Data Generation

`backend/data_generation/simulator.py` runs large batches of hands between agents. When feature recording is enabled, every decision point becomes a supervised learning row:

- state features before action
- action taken
- final hand profit
- showdown flag
- agent identity

`backend/scripts/generate_data.py` simulates several rule-based matchups to create `backend/data/training_data.csv`.

### Model Training

`backend/scripts/train_models.py` trains four scikit-learn Random Forest models:

- hand strength bucket classifier
- opponent action classifier
- bluff detector
- action EV regressor

Artifacts are saved in `backend/artifacts/`.

### Evaluation

`backend/scripts/evaluate_models.py` evaluates trained artifacts on a held-out split and runs seeded agent backtests. It writes `backend/artifacts/evaluation_report.json`.

The report includes:

- classification and regression metrics
- confusion matrices
- top feature importances
- seeded agent-vs-agent backtests
- explicit modeling limitations

### API Layer

FastAPI routes in `backend/api/routes/` expose product workflows:

- hand analysis
- training scenario generation and grading
- agent simulation
- natural-language strategy parsing
- natural-language strategy experiment benchmarking
- natural-language strategy diagnosis and leak detection
- simulation-driven policy optimization

### Frontend

The Next.js frontend in `frontend/` provides:

- training scenario UI
- hand analyzer
- simulation dashboard
- strategy lab with natural-language parsing and experiment results

Next rewrites `/api/*` to the FastAPI backend at `localhost:8000`.

## Data Flow

1. Engine creates a game state.
2. Feature extractor converts the state into numeric model inputs.
3. Agents or user workflows select an action.
4. Simulator records the decision and final outcome.
5. Training scripts fit models from generated data.
6. API routes load model artifacts and serve predictions.
7. Frontend renders recommendations, metrics, and bankroll curves.

## Key Tradeoffs

- The project optimizes for an explainable AI product workflow, not solver-grade poker accuracy.
- EV labels use final simulated hand profit, not counterfactual game-theoretic EV.
- Strategy parsing is schema-driven and testable, with optional LLM fallback for low-confidence descriptions.
- Coarse bet sizing keeps simulations tractable and product results easier to explain.
