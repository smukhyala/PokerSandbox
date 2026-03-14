"""Natural language strategy parser: converts text descriptions to StrategyConfig.

Handles a wide range of poker strategy descriptions by matching semantic
concepts (not just exact phrases) using regex patterns and keyword groups.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from backend.strategy_language.schema import BetSizing, StrategyConfig, StreetStrategy, PreflopStrategy


@dataclass
class ParseResult:
    """Result of parsing a natural language strategy description."""
    config: StrategyConfig
    matched_keywords: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence: float = 0.5


def parse_strategy(text: str) -> ParseResult:
    """Parse a natural language strategy description into a StrategyConfig."""
    t = text.lower().strip()
    config = StrategyConfig(name="Custom Strategy")
    matched: list[str] = []
    warnings: list[str] = []

    # ===================== HAND SELECTION / TIGHTNESS =====================

    # Specific hand types
    if _rx(t, r"only\s+(play\s+)?(suited\s+connector|sc\b)"):
        config.tightness = 0.85
        config.preflop.open_raise_range = 5  # group 5 includes suited connectors
        config.preflop.call_raise_range = 5
        matched.append("suited connectors only")
        # Narrow further based on context
        if _rx(t, r"no\s+face\s+card|no\s+broadway|no\s+high\s+card|avoid\s+face"):
            config.preflop.open_raise_range = 6  # wider groups but skip premiums
            config.preflop.three_bet_range = 0
            matched.append("no face cards / broadways")
        if _rx(t, r"(2|two)\s*(away|gap)|gapper"):
            config.preflop.open_raise_range = 6  # includes gappers
            matched.append("include gappers")

    elif _rx(t, r"only\s+(play\s+)?(pocket\s+pair|pair)"):
        config.tightness = 0.9
        config.preflop.open_raise_range = 5  # all pairs are groups 0-5
        config.preflop.call_raise_range = 5
        matched.append("pocket pairs only")

    elif _rx(t, r"only\s+(play\s+)?(premium|best\s+hand|top\s+hand|aces|kings|queens)"):
        config.tightness = 0.95
        config.preflop.open_raise_range = 1
        config.preflop.three_bet_range = 0
        config.preflop.call_raise_range = 1
        matched.append("only premium hands")

    elif _rx(t, r"play\s+(every|all|any)\s*(hand|two\s+card|card)"):
        config.tightness = 0.05
        config.preflop.open_raise_range = 7
        config.preflop.call_raise_range = 7
        matched.append("play every hand")

    elif _rx(t, r"(wide|broad|lots?\s+of)\s+(range|hand|opening)"):
        config.tightness = 0.25
        config.preflop.open_raise_range = 6
        config.preflop.call_raise_range = 6
        matched.append("wide range")

    elif _rx(t, r"(narrow|small|few|selective|select)\s+(range|hand|opening)"):
        config.tightness = 0.8
        config.preflop.open_raise_range = 2
        config.preflop.call_raise_range = 3
        matched.append("narrow/selective range")

    # General tightness keywords
    if _match(t, ["very tight", "ultra tight", "nit", "nitty", "super tight", "extremely tight"]):
        config.tightness = 0.9
        config.preflop.open_raise_range = min(config.preflop.open_raise_range, 1)
        config.preflop.call_raise_range = min(config.preflop.call_raise_range, 2)
        matched.append("very tight")
    elif _match(t, ["tight"]) and "very tight" not in " ".join(matched):
        config.tightness = max(config.tightness, 0.7)
        config.preflop.open_raise_range = min(config.preflop.open_raise_range, 3)
        config.preflop.call_raise_range = min(config.preflop.call_raise_range, 3)
        matched.append("tight")
    elif _match(t, ["very loose", "ultra loose", "maniac"]):
        config.tightness = 0.1
        config.preflop.open_raise_range = 7
        config.preflop.call_raise_range = 7
        matched.append("very loose")
    elif _match(t, ["loose"]) and "very loose" not in " ".join(matched):
        config.tightness = min(config.tightness, 0.3)
        config.preflop.open_raise_range = max(config.preflop.open_raise_range, 5)
        config.preflop.call_raise_range = max(config.preflop.call_raise_range, 6)
        matched.append("loose")

    # ===================== AGGRESSION =====================

    if _match(t, ["very aggressive", "hyper aggressive", "ultra aggressive",
                   "super aggressive", "extremely aggressive", "max aggression"]):
        config.aggression = 0.9
        _set_all_streets(config, bluff_frequency=0.35, bet_sizing=BetSizing.LARGE)
        matched.append("very aggressive")
    elif _match(t, ["aggressive", "aggro"]):
        config.aggression = 0.7
        _set_all_streets(config, bluff_frequency=0.20, bet_sizing=BetSizing.LARGE)
        matched.append("aggressive")
    elif _match(t, ["very passive", "ultra passive", "extremely passive"]):
        config.aggression = 0.1
        _set_all_streets(config, bluff_frequency=0.02, bet_sizing=BetSizing.SMALL)
        matched.append("very passive")
    elif _match(t, ["passive"]):
        config.aggression = 0.3
        _set_all_streets(config, bluff_frequency=0.05, bet_sizing=BetSizing.SMALL)
        matched.append("passive")

    # Aggression via action descriptions
    if _rx(t, r"(raise|bet|jam)\s+(a\s+lot|often|frequent|every|always|most)"):
        config.aggression = max(config.aggression, 0.8)
        _set_all_streets(config, bet_sizing=BetSizing.LARGE)
        matched.append("bet/raise frequently")
    elif _rx(t, r"(mostly|prefer|like\s+to)\s+(call|check|flat)"):
        config.aggression = min(config.aggression, 0.3)
        matched.append("prefer calling/checking")

    # ===================== C-BET =====================

    if _match(t, ["always c-bet", "cbet everything", "always continuation bet",
                   "always cbet", "cbet 100", "c-bet every"]):
        config.continuation_bet_frequency = 0.95
        matched.append("always c-bet")
    elif _rx(t, r"(c-?bet|continuation\s+bet)\s*(frequent|often|a\s+lot|most|high)") or \
         _rx(t, r"(frequent|often|high)\s*(c-?bet|continuation)") or \
         _rx(t, r"c-?bet\s*(dry|flop)"):
        config.continuation_bet_frequency = 0.75
        matched.append("frequent c-bet")
    elif _rx(t, r"(rare|seldom|never|no|don.t|avoid)\s*(c-?bet|continuation)"):
        config.continuation_bet_frequency = 0.15
        matched.append("rarely c-bet")

    # ===================== BLUFFING =====================

    if _match(t, ["never bluff", "no bluff", "don't bluff", "no bluffs",
                   "zero bluff", "0 bluff", "avoid bluff"]):
        _set_all_streets(config, bluff_frequency=0.0)
        matched.append("never bluff")
    elif _match(t, ["rarely bluff", "seldom bluff", "minimal bluff"]):
        _set_all_streets(config, bluff_frequency=0.05)
        matched.append("rarely bluff")
    elif _rx(t, r"bluff\s*(a\s+lot|often|frequent|heavy|more|tons|big)") or \
         _rx(t, r"(lots?\s+of|heavy|frequent)\s*bluff"):
        _set_all_streets(config, bluff_frequency=0.35)
        matched.append("heavy bluffing")

    # Numeric bluff %
    bluff_pct = re.search(r'bluff\s*(\d+)\s*%', t)
    if bluff_pct:
        freq = int(bluff_pct.group(1)) / 100
        config.flop.bluff_frequency = freq
        config.turn.bluff_frequency = freq * 0.8
        config.river.bluff_frequency = freq * 0.6
        matched.append(f"bluff {bluff_pct.group(1)}%")

    # ===================== BET SIZING =====================

    if _rx(t, r"(big|large|pot.?size|overbet|max)\s*(bet|raise|sizing)") or \
       _match(t, ["bet big", "bet large", "pot sized"]):
        _set_all_streets(config, bet_sizing=BetSizing.LARGE)
        matched.append("large bet sizing")
    elif _rx(t, r"(small|min|tiny|micro)\s*(bet|raise|sizing)") or \
         _match(t, ["bet small", "min bet", "minimum bet"]):
        _set_all_streets(config, bet_sizing=BetSizing.SMALL)
        matched.append("small bet sizing")

    # ===================== FOLDING =====================

    if _match(t, ["never fold", "don't fold", "call everything", "call every bet",
                   "can't fold", "never lay down", "call down"]):
        config.fold_to_aggression = 0.05
        for s in [config.flop, config.turn, config.river]:
            s.call_threshold = 0.05
        matched.append("never fold")
    elif _rx(t, r"(fold|give\s+up)\s*(easy|quick|often|a\s+lot|to\s+pressure|to\s+aggression|to\s+raise|to\s+large|to\s+big)"):
        config.fold_to_aggression = 0.8
        matched.append("fold to aggression")
    elif _rx(t, r"(sticky|stubborn|don.t\s+fold\s+easy|hero\s+call|call\s+light)"):
        config.fold_to_aggression = 0.2
        for s in [config.flop, config.turn, config.river]:
            s.call_threshold = 0.2
        matched.append("sticky / hero calling")

    # ===================== PREFLOP SPECIFICS =====================

    if _rx(t, r"(3.?bet|three.?bet)\s*(wide|a\s+lot|often|frequent|more|light)"):
        config.preflop.three_bet_range = 4
        matched.append("wide 3-bet range")
    elif _rx(t, r"(never|no|don.t|avoid)\s*(3.?bet|three.?bet)"):
        config.preflop.three_bet_range = 0
        matched.append("no 3-betting")

    if _match(t, ["limp a lot", "limp often", "open limp", "just limp", "like to limp"]):
        config.preflop.limp_frequency = 0.5
        matched.append("limp frequently")
    elif _match(t, ["never limp", "no limping", "don't limp", "always raise"]):
        config.preflop.limp_frequency = 0.0
        matched.append("never limp")

    # ===================== POSITION =====================

    if _rx(t, r"(play|use|leverage|exploit)\s*(position|in\s+position)") or \
       _match(t, ["positional", "position matters", "position aware"]):
        config.positional_awareness = 0.8
        matched.append("positional awareness")
    elif _match(t, ["ignore position", "position doesn't matter"]):
        config.positional_awareness = 0.1
        matched.append("ignore position")

    # ===================== STREET-SPECIFIC =====================

    # River
    if _rx(t, r"(avoid|no|don.t|never)\s*(river\s+bluff|bluff.{0,10}river)"):
        config.river.bluff_frequency = 0.0
        matched.append("no river bluffs")
    elif _rx(t, r"(bluff|bet).{0,15}river"):
        config.river.bluff_frequency = 0.25
        matched.append("river bluffs")

    # Turn
    if _rx(t, r"(barrel|bet|continue|fire).{0,15}turn"):
        config.turn.value_bet_threshold = 0.55
        config.turn.bluff_frequency = max(config.turn.bluff_frequency, 0.20)
        matched.append("barrel the turn")

    # Flop
    if _rx(t, r"(bet|lead|donk).{0,15}flop"):
        config.flop.value_bet_threshold = 0.55
        matched.append("bet the flop")
    if _rx(t, r"(dry|static)\s*(board|flop|texture)"):
        config.flop.bluff_frequency = max(config.flop.bluff_frequency, 0.20)
        config.continuation_bet_frequency = max(config.continuation_bet_frequency, 0.70)
        matched.append("target dry boards")
    if _rx(t, r"(wet|draw.heavy|coordinated)\s*(board|flop|texture)"):
        config.flop.value_bet_threshold = 0.6
        config.flop.bluff_frequency = min(config.flop.bluff_frequency, 0.10)
        matched.append("cautious on wet boards")

    # ===================== STYLE ARCHETYPES =====================

    if _match(t, ["tag style", "tight aggressive", "tight-aggressive", "play like a tag"]):
        config.tightness = 0.75
        config.aggression = 0.7
        config.preflop.open_raise_range = 3
        config.continuation_bet_frequency = 0.70
        matched.append("TAG archetype")
    elif _match(t, ["lag style", "loose aggressive", "loose-aggressive", "play like a lag"]):
        config.tightness = 0.3
        config.aggression = 0.8
        config.preflop.open_raise_range = 5
        config.continuation_bet_frequency = 0.80
        _set_all_streets(config, bluff_frequency=0.25)
        matched.append("LAG archetype")
    elif _match(t, ["calling station", "station", "just call everything"]):
        config.tightness = 0.2
        config.aggression = 0.1
        config.fold_to_aggression = 0.05
        for s in [config.flop, config.turn, config.river]:
            s.call_threshold = 0.1
        matched.append("calling station style")

    # ===================== TRAPPING / SLOW PLAY =====================

    if _rx(t, r"(trap|slow.?play|check.?raise|deceptive|tricky)"):
        config.flop.value_bet_threshold = 0.8  # check strong hands
        config.flop.bluff_frequency = 0.0
        config.turn.value_bet_threshold = 0.6  # then bet turn
        matched.append("trapping / slow-play")

    # ===================== DRAW PLAY =====================

    if _rx(t, r"(chase|play|semi.?bluff).{0,15}draw"):
        for s in [config.flop, config.turn]:
            s.draw_aggression = 0.8
        matched.append("aggressive with draws")
    elif _rx(t, r"(fold|give\s+up|don.t\s+chase).{0,15}draw"):
        for s in [config.flop, config.turn]:
            s.draw_aggression = 0.1
        matched.append("fold draws")

    # ===================== VALUE / THIN VALUE =====================

    if _rx(t, r"(thin\s+value|value\s+bet\s+thin|extract\s+value|max\s+value)"):
        for s in [config.flop, config.turn, config.river]:
            s.value_bet_threshold = max(0.4, s.value_bet_threshold - 0.15)
        matched.append("thin value betting")
    elif _rx(t, r"(only\s+bet|bet\s+only).{0,15}(strong|nuts|monster|premium)"):
        for s in [config.flop, config.turn, config.river]:
            s.value_bet_threshold = 0.85
        matched.append("only bet strong hands")

    # ===================== NUMERIC EXTRACTIONS =====================

    # "open X% of hands"
    open_pct = re.search(r'(?:open|play|raise)\s+(\d+)\s*%', t)
    if open_pct:
        pct = int(open_pct.group(1))
        # Map % to hand group: 10%->1, 20%->2, 30%->3, 50%->5, 70%->6, 100%->7
        group = min(7, max(0, pct // 14))
        config.preflop.open_raise_range = group
        config.tightness = 1.0 - (pct / 100)
        matched.append(f"open {pct}% of hands")

    # "call X% of the time"
    call_pct = re.search(r'call\s+(\d+)\s*%', t)
    if call_pct:
        pct = int(call_pct.group(1))
        threshold = 1.0 - (pct / 100)
        for s in [config.flop, config.turn, config.river]:
            s.call_threshold = max(0.0, threshold)
        config.fold_to_aggression = threshold
        matched.append(f"call {pct}% of bets")

    # ===================== CONFIDENCE & LLM FALLBACK =====================

    confidence = min(1.0, len(matched) * 0.12 + 0.25) if matched else 0.1

    # If regex parser didn't understand much, try LLM
    if confidence < 0.3:
        from backend.strategy_language.llm_parser import llm_parse_strategy
        llm_config, interpretation, llm_warnings = llm_parse_strategy(text)

        if llm_config is not None:
            config = llm_config
            matched = [f"LLM: {interpretation}"] if interpretation else ["LLM-parsed"]
            warnings = llm_warnings
            confidence = 0.75
            config.description = f"AI interpretation: {interpretation}" if interpretation else "Parsed by AI"
        else:
            # LLM also failed
            warnings.extend(llm_warnings)
            if not any("Try phrases" in w for w in warnings):
                warnings.append(
                    "Could not parse strategy. Try phrases like: "
                    "'play tight', 'aggressive', 'only suited connectors', "
                    "'bluff often', 'fold to raises', 'open 25% of hands'."
                )
    else:
        if matched:
            config.description = f"Parsed from: {', '.join(matched)}"

    return ParseResult(
        config=config,
        matched_keywords=matched,
        warnings=warnings,
        confidence=confidence,
    )


def _match(text: str, patterns: list[str]) -> bool:
    """Check if any pattern appears as a substring in the text."""
    return any(p in text for p in patterns)


def _rx(text: str, pattern: str) -> bool:
    """Check if a regex pattern matches anywhere in the text."""
    return bool(re.search(pattern, text))


def _set_all_streets(
    config: StrategyConfig,
    bluff_frequency: float | None = None,
    bet_sizing: BetSizing | None = None,
) -> None:
    """Set a parameter across all post-flop streets."""
    for street in [config.flop, config.turn, config.river]:
        if bluff_frequency is not None:
            street.bluff_frequency = bluff_frequency
        if bet_sizing is not None:
            street.bet_sizing = bet_sizing
