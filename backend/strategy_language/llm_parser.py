"""LLM-based strategy parser using GPT-4o-mini as fallback."""

from __future__ import annotations

import json
import os

from backend.strategy_language.schema import StrategyConfig

SYSTEM_PROMPT = """You are a poker strategy interpreter for a heads-up No Limit Hold'em simulator. Given a natural language description, convert it to a JSON config that controls an automated poker agent.

IMPORTANT: Think carefully about what the user actually means. They might reference:
- Specific card ranks: "only play 3, 4, 5" = only enter pots with hands containing 3s, 4s, or 5s (very tight, unconventional, low cards)
- Hand types: "suited connectors", "pocket pairs", "broadways", "Ax suited"
- Play styles: "tight", "aggressive", "passive", "loose"
- Specific actions: "always 3-bet", "never bluff the river", "c-bet dry boards"
- Percentages: "open 20% of hands", "bluff 30%"

Your job: figure out the INTENT and map it to these config parameters.

SCHEMA (all floats 0.0-1.0 unless noted):
{
  "tightness": float,              // 0=play every hand, 1=only the absolute best
  "aggression": float,             // 0=check/call only, 1=bet/raise constantly
  "preflop": {
    "open_raise_range": int 0-7,   // which hand groups to play (see below)
    "three_bet_range": int 0-7,
    "call_raise_range": int 0-7,
    "limp_frequency": float        // 0=always raise, 1=always limp
  },
  "flop": {
    "value_bet_threshold": float,  // min hand strength to value bet (0.7=only strong, 0.3=bet wide)
    "call_threshold": float,       // min hand strength to call (0.4=normal, 0.1=call everything)
    "bluff_frequency": float,      // 0=never bluff, 0.3=bluff often
    "bet_sizing": "small"|"medium"|"large",   // 33% / 66% / 100% pot
    "draw_aggression": float       // 0=fold draws, 1=always semi-bluff draws
  },
  "turn": { same fields as flop },
  "river": { same fields as flop },
  "continuation_bet_frequency": float,  // how often to c-bet as preflop raiser
  "fold_to_aggression": float,          // 0=never fold to bets, 1=fold easily
  "positional_awareness": float         // 0=ignore position, 1=heavily use position
}

HAND GROUPS (open_raise_range, three_bet_range, call_raise_range):
Group 0: AA, KK, QQ, AKs — the nuts preflop
Group 1: JJ, TT, AKo, AQs — very strong
Group 2: 99, 88, AJs, ATs, KQs — strong
Group 3: 77, 66, AJo, KJs, QJs — above average
Group 4: 55, 44, ATo, KJo, QJo, JTs — playable
Group 5: 33, 22, suited connectors 56s-89s, A2s-A9s — speculative
Group 6: suited gappers T8s/97s, offsuit broadways — marginal
Group 7: everything else — trash

The value means "play hands in this group AND all better groups." So open_raise_range=3 means play groups 0,1,2,3.

MAPPING EXAMPLES:
- "play only 3, 4, 5" → User wants hands with rank 3/4/5. Those are low cards: 33, 44, 55, 34s, 45s, 35s. This is very tight and unconventional. Set tightness=0.9, open_raise_range=5 (includes small pairs/connectors), three_bet_range=0, aggression based on other context.
- "suited connectors only" → tightness=0.85, open_raise_range=5 (suited connectors are group 5)
- "play everything" → tightness=0.0, open_raise_range=7
- "TAG" → tightness=0.75, aggression=0.7, open_raise_range=3
- "check-raise a lot" → aggression=0.8, value_bet_threshold low (to check first then raise)

Return ONLY a JSON object matching the schema. Add an "interpretation" field (string) explaining what you understood from the user's description and how you mapped it. Be specific about what hands/actions this config will produce."""


def llm_parse_strategy(text: str) -> tuple[StrategyConfig | None, str, list[str]]:
    """Parse strategy using GPT-4o-mini.

    Returns:
        Tuple of (config or None, interpretation text, warnings list)
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None, "", ["LLM parsing unavailable: OPENAI_API_KEY not set."]

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Convert this poker strategy to config JSON:\n\n\"{text}\""},
            ],
            temperature=0.2,
            max_tokens=800,
        )

        content = response.choices[0].message.content or ""

        # Extract JSON from the response
        json_str = _extract_json(content)
        if not json_str:
            return None, content, ["LLM response did not contain valid JSON."]

        data = json.loads(json_str)

        # Extract interpretation if present
        interpretation = data.pop("interpretation", "")

        # Build the config, handling nested structure
        config = _build_config_from_dict(data)

        return config, interpretation, []

    except Exception as e:
        return None, "", [f"LLM parsing error: {str(e)}"]


def _extract_json(text: str) -> str | None:
    """Extract a JSON object from LLM response text."""
    # Try to find JSON in code blocks first
    import re
    code_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block:
        return code_block.group(1)

    # Try to find raw JSON object
    brace_start = text.find('{')
    if brace_start == -1:
        return None

    # Find matching closing brace
    depth = 0
    for i in range(brace_start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[brace_start:i + 1]
    return None


def _build_config_from_dict(data: dict) -> StrategyConfig:
    """Build a StrategyConfig from a flat or nested dict, handling missing/extra fields."""
    from backend.strategy_language.schema import PreflopStrategy, StreetStrategy, BetSizing

    preflop_data = data.get("preflop", {})
    flop_data = data.get("flop", {})
    turn_data = data.get("turn", {})
    river_data = data.get("river", {})

    def parse_street(d: dict) -> dict:
        """Clean a street dict for StreetStrategy construction."""
        clean = {}
        for key in ["value_bet_threshold", "call_threshold", "bluff_frequency", "draw_aggression"]:
            if key in d:
                clean[key] = float(d[key])
        if "bet_sizing" in d:
            try:
                clean["bet_sizing"] = BetSizing(d["bet_sizing"])
            except ValueError:
                pass
        if "bluff_sizing" in d:
            try:
                clean["bluff_sizing"] = BetSizing(d["bluff_sizing"])
            except ValueError:
                pass
        return clean

    config = StrategyConfig(
        name="Custom Strategy (LLM)",
        tightness=float(data.get("tightness", 0.5)),
        aggression=float(data.get("aggression", 0.5)),
        preflop=PreflopStrategy(
            open_raise_range=int(preflop_data.get("open_raise_range", 3)),
            three_bet_range=int(preflop_data.get("three_bet_range", 1)),
            call_raise_range=int(preflop_data.get("call_raise_range", 4)),
            limp_frequency=float(preflop_data.get("limp_frequency", 0.0)),
        ),
        flop=StreetStrategy(**parse_street(flop_data)),
        turn=StreetStrategy(**parse_street(turn_data)),
        river=StreetStrategy(**parse_street(river_data)),
        continuation_bet_frequency=float(data.get("continuation_bet_frequency", 0.65)),
        fold_to_aggression=float(data.get("fold_to_aggression", 0.5)),
        positional_awareness=float(data.get("positional_awareness", 0.5)),
    )
    return config
