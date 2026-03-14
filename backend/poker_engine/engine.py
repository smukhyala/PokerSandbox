"""Game engine: runs a heads-up NLHE hand from deal to showdown."""

from __future__ import annotations

from typing import Optional

from backend.config import (
    BET_LARGE_FRACTION,
    BET_MEDIUM_FRACTION,
    BET_SMALL_FRACTION,
    BIG_BLIND,
    SMALL_BLIND,
    STARTING_STACK,
)
from backend.poker_engine.deck import Deck
from backend.poker_engine.hand_evaluator import (
    evaluate,
    get_rank_class_name,
)
from backend.poker_engine.types import (
    Action,
    ActionType,
    GameState,
    HandResult,
    PlayerState,
    Position,
    Street,
)


class GameEngine:
    """Runs a single heads-up NLHE hand."""

    def deal_hand(self, seed: int | None = None) -> GameState:
        """Deal a new hand: shuffle, deal hole cards, post blinds."""
        deck = Deck(seed=seed)

        btn_cards = deck.draw(2)
        bb_cards = deck.draw(2)

        btn = PlayerState(
            position=Position.BUTTON,
            hole_cards=btn_cards,
            stack=STARTING_STACK - SMALL_BLIND,
            bet_this_street=SMALL_BLIND,
            total_invested=SMALL_BLIND,
        )
        bb = PlayerState(
            position=Position.BIG_BLIND,
            hole_cards=bb_cards,
            stack=STARTING_STACK - BIG_BLIND,
            bet_this_street=BIG_BLIND,
            total_invested=BIG_BLIND,
        )

        state = GameState(
            players={Position.BUTTON: btn, Position.BIG_BLIND: bb},
            deck_remaining=deck.remaining,
            current_street=Street.PREFLOP,
            pot=SMALL_BLIND + BIG_BLIND,
            current_bet=BIG_BLIND,
            actor=Position.BUTTON,  # BTN acts first preflop in heads-up
            effective_stack=STARTING_STACK,
        )
        return state

    def get_legal_actions(self, state: GameState) -> list[ActionType]:
        """Return the list of legal actions for the current actor."""
        if state.is_hand_over:
            return []

        player = state.players[state.actor]
        if player.is_folded or player.is_all_in:
            return []

        actions: list[ActionType] = []
        call_amount = state.current_bet - player.bet_this_street

        if call_amount > 0:
            # Facing a bet
            actions.append(ActionType.FOLD)
            actions.append(ActionType.CALL)
        else:
            # No bet to face
            actions.append(ActionType.CHECK)

        # Bet/raise options (only if player has chips beyond calling)
        chips_after_call = player.stack - call_amount
        if chips_after_call > 0:
            pot_after_call = state.pot + call_amount
            for action_type, fraction in [
                (ActionType.BET_SMALL, BET_SMALL_FRACTION),
                (ActionType.BET_MEDIUM, BET_MEDIUM_FRACTION),
                (ActionType.BET_LARGE, BET_LARGE_FRACTION),
            ]:
                bet_amount = int(pot_after_call * fraction)
                if 0 < bet_amount < chips_after_call:
                    actions.append(action_type)

            # All-in is always legal if the player has chips
            actions.append(ActionType.ALL_IN)

        return actions

    def apply_action(self, state: GameState, action_type: ActionType) -> GameState:
        """Apply an action and return the new game state."""
        state = state.copy()
        player = state.players[state.actor]
        opponent = state.players[state.actor.opponent]

        call_amount = max(0, state.current_bet - player.bet_this_street)
        amount = self._compute_bet_amount(
            action_type, state.pot, state.current_bet,
            player.bet_this_street, player.stack,
        )

        # Record the action
        action = Action(
            player=state.actor,
            action_type=action_type,
            amount=amount,
            street=state.current_street,
            sequence_index=len(state.action_history),
        )
        state.action_history.append(action)
        state.num_actions_this_street += 1

        if action_type == ActionType.FOLD:
            player.is_folded = True
            state.is_hand_over = True
            state.winner = state.actor.opponent
            return state

        if action_type == ActionType.CHECK:
            # Check if street is complete
            if self._is_street_complete(state):
                state = self._advance_street(state)
            else:
                state.actor = state.actor.opponent
            return state

        # Call, bet, or raise — transfer chips
        player.stack -= amount
        player.bet_this_street += amount
        player.total_invested += amount
        state.pot += amount

        if player.stack == 0:
            player.is_all_in = True

        # Update current bet if this is a raise
        if player.bet_this_street > state.current_bet:
            state.current_bet = player.bet_this_street

        # If both players are now all-in or one folded, run out board
        both_committed = all(
            p.is_all_in or p.is_folded for p in state.players.values()
        )
        if both_committed:
            active = [p for p in state.players.values() if not p.is_folded]
            if len(active) == 2:
                state = self._run_out_board(state)
                state = self._showdown(state)
            return state

        # Opponent can't act (all-in) — just advance the street
        if opponent.is_all_in:
            if self._is_street_complete(state):
                state = self._advance_street(state)
            # else: action continues with current player (can bet again)
            # Actually no — if opponent is all-in and called, street is done
            # The _is_street_complete check handles this
            return state

        # Check if street is complete
        if self._is_street_complete(state):
            state = self._advance_street(state)
        else:
            state.actor = state.actor.opponent

        return state

    def _compute_bet_amount(
        self, action_type: ActionType, pot: int, current_bet: int,
        player_bet_this_street: int, player_stack: int,
    ) -> int:
        """Compute how many chips the player puts in for this action."""
        call_amount = max(0, current_bet - player_bet_this_street)

        if action_type in (ActionType.FOLD, ActionType.CHECK):
            return 0
        elif action_type == ActionType.CALL:
            return min(call_amount, player_stack)
        elif action_type == ActionType.ALL_IN:
            return player_stack
        else:
            # Sized bet: fraction of (pot + call_amount)
            pot_after_call = pot + call_amount
            fraction = {
                ActionType.BET_SMALL: BET_SMALL_FRACTION,
                ActionType.BET_MEDIUM: BET_MEDIUM_FRACTION,
                ActionType.BET_LARGE: BET_LARGE_FRACTION,
            }[action_type]
            bet_over_call = max(1, int(pot_after_call * fraction))
            total = call_amount + bet_over_call
            return min(total, player_stack)

    def _is_street_complete(self, state: GameState) -> bool:
        """Check if the current street's betting round is complete."""
        btn = state.players[Position.BUTTON]
        bb = state.players[Position.BIG_BLIND]

        # Both all-in: always complete
        if btn.is_all_in and bb.is_all_in:
            return True

        # One player all-in: street is complete once the other player has acted
        # at least once on this street (call/fold/check). We check that the
        # non-all-in player had a turn by requiring num_actions >= 1 on a
        # street where one is already all-in AND bets are matched or
        # the action this street was by the non-all-in player.
        one_all_in = btn.is_all_in or bb.is_all_in
        if one_all_in and state.num_actions_this_street >= 1:
            # The street is complete if the non-all-in player has acted
            # (i.e., bets are matched — the non-all-in player called or the
            #  all-in player's bet was 0 and non-all-in checked)
            return btn.bet_this_street == bb.bet_this_street

        # Normal case: both players must have acted, bets must match
        if state.num_actions_this_street < 2:
            return False

        return btn.bet_this_street == bb.bet_this_street

    def _advance_street(self, state: GameState) -> GameState:
        """Move to the next street: deal community cards, reset betting."""
        # If we're on the river, betting is done — go to showdown
        if state.current_street == Street.RIVER:
            state = self._showdown(state)
            return state

        # Reset street-level betting state
        for p in state.players.values():
            p.bet_this_street = 0
        state.current_bet = 0
        state.num_actions_this_street = 0

        next_street = Street(state.current_street + 1)

        if next_street == Street.FLOP:
            state.board.extend(state.deck_remaining[:3])
            state.deck_remaining = state.deck_remaining[3:]
        elif next_street in (Street.TURN, Street.RIVER):
            state.board.append(state.deck_remaining[0])
            state.deck_remaining = state.deck_remaining[1:]

        state.current_street = next_street

        # Post-flop: BB acts first in heads-up
        # (BTN is in position = acts last)
        state.actor = Position.BIG_BLIND

        # Skip actors who can't act
        actor_state = state.players[state.actor]
        if actor_state.is_all_in or actor_state.is_folded:
            opp = state.players[state.actor.opponent]
            if opp.is_all_in or opp.is_folded:
                # Both can't act — run out board and showdown
                state = self._run_out_board(state)
                state = self._showdown(state)
                return state
            state.actor = state.actor.opponent

        # Check if both players are all-in (no more action possible)
        active_can_act = [
            p for p in state.players.values()
            if not p.is_folded and not p.is_all_in
        ]
        if len(active_can_act) == 0:
            state = self._run_out_board(state)
            state = self._showdown(state)

        return state

    def _run_out_board(self, state: GameState) -> GameState:
        """Deal remaining community cards when all players are all-in."""
        while len(state.board) < 5 and state.deck_remaining:
            cards_needed = {0: 3, 3: 1, 4: 1}.get(len(state.board), 0)
            if cards_needed == 0:
                break
            state.board.extend(state.deck_remaining[:cards_needed])
            state.deck_remaining = state.deck_remaining[cards_needed:]
        return state

    def _showdown(self, state: GameState) -> GameState:
        """Evaluate hands and determine winner."""
        state.is_hand_over = True

        btn = state.players[Position.BUTTON]
        bb = state.players[Position.BIG_BLIND]

        # If someone folded, they already lost
        if btn.is_folded:
            state.winner = Position.BIG_BLIND
            return state
        if bb.is_folded:
            state.winner = Position.BUTTON
            return state

        # Evaluate both hands
        btn_rank = evaluate(btn.hole_cards, state.board)
        bb_rank = evaluate(bb.hole_cards, state.board)

        if btn_rank < bb_rank:  # lower rank = better in treys
            state.winner = Position.BUTTON
        elif bb_rank < btn_rank:
            state.winner = Position.BIG_BLIND
        else:
            state.winner = None  # split pot

        return state

    def get_hand_result(self, state: GameState) -> HandResult:
        """Extract a HandResult from a completed game state."""
        if not state.is_hand_over:
            raise ValueError("Hand is not over yet")

        btn = state.players[Position.BUTTON]
        bb = state.players[Position.BIG_BLIND]

        went_to_showdown = not btn.is_folded and not bb.is_folded

        # Compute hand ranks (only meaningful if we have a board)
        player_hand_ranks: dict[Position, int] = {}
        player_hand_classes: dict[Position, str] = {}

        if went_to_showdown and len(state.board) >= 3:
            for pos, ps in state.players.items():
                rank = evaluate(ps.hole_cards, state.board)
                player_hand_ranks[pos] = rank
                player_hand_classes[pos] = get_rank_class_name(rank)
        else:
            for pos in state.players:
                player_hand_ranks[pos] = 0
                player_hand_classes[pos] = "N/A"

        # Compute profit
        profit: dict[Position, int] = {}
        if state.winner is None:
            # Split pot
            half_pot = state.pot // 2
            for pos in state.players:
                profit[pos] = half_pot - state.players[pos].total_invested
        else:
            for pos in state.players:
                if pos == state.winner:
                    profit[pos] = state.pot - state.players[pos].total_invested
                else:
                    profit[pos] = -state.players[pos].total_invested

        return HandResult(
            hand_id=state.hand_id,
            winner=state.winner,
            pot_won=state.pot,
            went_to_showdown=went_to_showdown,
            final_board=list(state.board),
            player_hands={pos: list(ps.hole_cards) for pos, ps in state.players.items()},
            player_hand_ranks=player_hand_ranks,
            player_hand_classes=player_hand_classes,
            action_history=list(state.action_history),
            profit=profit,
            final_street=state.current_street,
        )

    def play_hand(
        self,
        agent_btn,
        agent_bb,
        seed: int | None = None,
    ) -> tuple[GameState, HandResult]:
        """Play a complete hand between two agents.

        Args:
            agent_btn: Agent playing the BTN/SB position.
            agent_bb: Agent playing the BB position.
            seed: Random seed for deck shuffle.

        Returns:
            Tuple of (final_state, hand_result).
        """
        agents = {Position.BUTTON: agent_btn, Position.BIG_BLIND: agent_bb}
        state = self.deal_hand(seed=seed)

        max_actions = 100  # safety limit
        action_count = 0

        while not state.is_hand_over and action_count < max_actions:
            legal = self.get_legal_actions(state)
            if not legal:
                break

            agent = agents[state.actor]
            action = agent.select_action(state, legal)

            # Validate action
            if action not in legal:
                # Fallback: fold if facing bet, check otherwise
                action = ActionType.FOLD if ActionType.FOLD in legal else ActionType.CHECK

            state = self.apply_action(state, action)
            action_count += 1

        result = self.get_hand_result(state)
        return state, result
