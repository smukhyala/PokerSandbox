"""Generate counterfactual action-EV training data.

This script samples decision states from simulated hands and estimates the EV of
each legal action by rolling out the rest of the hand. The resulting dataset is
more useful for the EV model than assigning every decision the final result from
the one action that happened to be taken.
"""

from __future__ import annotations

import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pandas as pd

from backend.agents.calling_station import CallingStationAgent
from backend.agents.lag_agent import LAGAgent
from backend.agents.random_agent import RandomAgent
from backend.agents.tag_agent import TAGAgent
from backend.config import DATA_DIR
from backend.data_generation.action_ev import estimate_action_ev
from backend.feature_engineering.features import extract_features
from backend.models.ev_model import FULL_FEATURE_NAMES
from backend.poker_engine.engine import GameEngine
from backend.poker_engine.types import ActionType, Position


def _agent_matchups():
    return [
        (TAGAgent(), RandomAgent()),
        (LAGAgent(), RandomAgent()),
        (TAGAgent(), LAGAgent()),
        (TAGAgent(), CallingStationAgent()),
        (LAGAgent(), CallingStationAgent()),
        (RandomAgent(), RandomAgent()),
    ]


def generate_counterfactual_ev_data(
    num_hands_per_matchup: int = 250,
    sample_rate: float = 0.35,
    rollouts_per_action: int = 25,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate state-action EV labels from sampled simulated decisions."""
    rng = random.Random(seed)
    engine = GameEngine()
    rows = []

    for matchup_index, (agent_btn_base, agent_bb_base) in enumerate(_agent_matchups()):
        for hand_num in range(num_hands_per_matchup):
            # Fresh instances avoid cross-hand state if agents later gain memory.
            agent_btn = type(agent_btn_base)()
            agent_bb = type(agent_bb_base)()
            agent_btn.position = Position.BUTTON
            agent_bb.position = Position.BIG_BLIND
            agents = {Position.BUTTON: agent_btn, Position.BIG_BLIND: agent_bb}

            state = engine.deal_hand(seed=seed * 100000 + matchup_index * 10000 + hand_num)
            action_count = 0

            while not state.is_hand_over and action_count < 100:
                legal = engine.get_legal_actions(state)
                if not legal:
                    break

                actor = state.actor
                features = extract_features(state, actor)

                if rng.random() < sample_rate:
                    for action in legal:
                        row = dict(features)
                        for action_type in ActionType:
                            row[f"action_{action_type.value}"] = (
                                1.0 if action_type == action else 0.0
                            )
                        row["action_taken"] = action.value
                        row["action_ev_bb"] = estimate_action_ev(
                            state,
                            action,
                            actor,
                            num_rollouts=rollouts_per_action,
                            seed=seed + len(rows),
                        )
                        rows.append(row)

                chosen = agents[actor].select_action(state, legal)
                if chosen not in legal:
                    chosen = ActionType.FOLD if ActionType.FOLD in legal else ActionType.CHECK
                state = engine.apply_action(state, chosen)
                action_count += 1

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[FULL_FEATURE_NAMES + ["action_taken", "action_ev_bb"]]
    return df


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    start = time.time()
    print("=== Generating Counterfactual EV Data ===")
    df = generate_counterfactual_ev_data()
    path = os.path.join(DATA_DIR, "ev_training_data.csv")
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {path}")
    print(f"Done in {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
