"""Global constants for PokerLab."""

# Stack and blind structure
# All values in chips. BB = 2 chips, so 100BB = 200 chips.
# This avoids the SB=BB=1 ambiguity where BTN has already matched the bet.
STARTING_STACK: int = 200  # 100 big blinds worth of chips
SMALL_BLIND: int = 1       # 0.5 BB
BIG_BLIND: int = 2         # 1 BB
BB_SIZE: int = 2            # for converting chips to BB units

# Bet sizing fractions (as fraction of pot after calling)
BET_SMALL_FRACTION: float = 0.33
BET_MEDIUM_FRACTION: float = 0.66
BET_LARGE_FRACTION: float = 1.0

# Monte Carlo defaults
DEFAULT_EQUITY_SIMULATIONS: int = 1000
DEFAULT_EV_ROLLOUTS: int = 200

# Data generation defaults
DEFAULT_SIMULATION_HANDS: int = 10000

# Model artifact paths
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
DATA_DIR = os.path.join(BASE_DIR, "data")
