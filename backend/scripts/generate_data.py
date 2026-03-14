"""Generate training data by simulating hands between various agent matchups."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pandas as pd
import numpy as np

from backend.agents.random_agent import RandomAgent
from backend.agents.tag_agent import TAGAgent
from backend.agents.lag_agent import LAGAgent
from backend.agents.calling_station import CallingStationAgent
from backend.data_generation.simulator import Simulator
from backend.data_generation.monte_carlo import estimate_equity
from backend.feature_engineering.features import FEATURE_NAMES
from backend.models.hand_strength import equity_to_bucket
from backend.config import DATA_DIR, BB_SIZE


def generate_simulation_data(num_hands_per_matchup: int = 10000) -> pd.DataFrame:
    """Generate decision records from multiple agent matchups."""
    matchups = [
        ("TAG", TAGAgent(), "Random", RandomAgent()),
        ("LAG", LAGAgent(), "Random", RandomAgent()),
        ("TAG", TAGAgent(), "LAG", LAGAgent()),
        ("TAG", TAGAgent(), "CallingStation", CallingStationAgent()),
        ("LAG", LAGAgent(), "CallingStation", CallingStationAgent()),
        ("Random", RandomAgent(), "Random", RandomAgent()),
    ]

    all_records = []
    for name1, agent1, name2, agent2, in matchups:
        print(f"  Simulating {name1} vs {name2} ({num_hands_per_matchup} hands)...")
        sim = Simulator(agent1, agent2, num_hands=num_hands_per_matchup, seed=42)
        result = sim.run()
        all_records.extend(result.decision_records)
        print(f"    -> {len(result.decision_records)} decision records")

    # Convert to DataFrame
    rows = []
    for r in all_records:
        row = dict(r.features)
        row["action_taken"] = r.action_taken
        row["hand_profit_bb"] = r.hand_profit_bb
        row["went_to_showdown"] = int(r.went_to_showdown)
        row["agent_name"] = r.agent_name
        row["street"] = r.street
        row["position"] = r.position
        rows.append(row)

    df = pd.DataFrame(rows)
    return df


def enrich_with_equity(df: pd.DataFrame, sample_size: int = 20000) -> pd.DataFrame:
    """Add Monte Carlo equity estimates to a sample of rows.

    This is expensive so we only do it for a subset.
    """
    # For the hand strength model we need equity labels.
    # Since we can't easily reconstruct hole_cards from features alone,
    # we'll use hand_rank_normalized as a proxy for equity when board is present,
    # and the preflop_hand_group for preflop.
    # This is a simplification but works for the MVP.

    # Create equity bucket from hand_rank_normalized
    df["equity_bucket"] = df["hand_rank_normalized"].apply(equity_to_bucket)
    return df


def generate_bluff_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Add bluff/value labels for betting actions.

    A bet is labeled as a 'bluff' if the hand strength (hand_rank_normalized)
    is below 0.4 at the time of the bet. This is a simplified heuristic.
    """
    bet_actions = {"bet_small", "bet_medium", "bet_large", "all_in"}
    df["is_bet"] = df["action_taken"].isin(bet_actions).astype(int)
    df["is_bluff"] = ((df["is_bet"] == 1) & (df["hand_rank_normalized"] < 0.4)).astype(int)
    return df


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("=== Generating Training Data ===")
    start = time.time()

    print("\n1. Simulating agent matchups...")
    df = generate_simulation_data(num_hands_per_matchup=10000)
    print(f"   Total records: {len(df)}")

    print("\n2. Computing equity buckets...")
    df = enrich_with_equity(df)

    print("\n3. Generating bluff labels...")
    df = generate_bluff_labels(df)

    # Save
    path = os.path.join(DATA_DIR, "training_data.csv")
    df.to_csv(path, index=False)
    print(f"\n4. Saved to {path}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Shape: {df.shape}")

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
