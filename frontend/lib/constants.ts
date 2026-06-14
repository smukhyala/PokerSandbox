export const AGENT_TYPES = ['TAG', 'LAG', 'CallingStation', 'Random', 'MLAgent', 'Custom'] as const

export const AGENT_DESCRIPTIONS: Record<string, string> = {
  TAG: 'Tight-Aggressive: plays fewer starting hands and applies pressure with strong ranges.',
  LAG: 'Loose-Aggressive: plays wider ranges and bluffs more often.',
  CallingStation: 'Calling Station: calls frequently, folds rarely, and seldom raises.',
  Random: 'Random: chooses randomly from legal actions; useful as a noise baseline.',
  MLAgent: 'Machine Learning Agent: uses the Random Forest EV model to choose the highest predicted-value action.',
  Custom: 'Custom: uses the natural-language strategy compiled in Strategy Lab.',
}

export const AGENT_LABELS: Record<string, string> = {
  TAG: 'TAG - Tight-Aggressive',
  LAG: 'LAG - Loose-Aggressive',
  CallingStation: 'Calling Station',
  Random: 'Random Baseline',
  MLAgent: 'Machine Learning Agent',
  Custom: 'Custom Strategy',
}

export const POSITION_LABELS: Record<string, string> = {
  BTN: 'Button',
  BB: 'Big Blind',
  SB: 'Small Blind',
  CO: 'Cutoff',
  MP: 'Middle Position',
  UTG: 'Under the Gun',
}

export const POSITION_DESCRIPTIONS: Record<string, string> = {
  BTN: 'Button: dealer seat; acts last after the flop.',
  BB: 'Big Blind: posts the full blind; acts first after the flop.',
  SB: 'Small Blind: posts half a blind.',
  CO: 'Cutoff: seat immediately before the Button.',
  MP: 'Middle Position: middle table seat.',
  UTG: 'Under the Gun: first seat to act preflop.',
}

export const BB_EXPLANATION = 'BB means big blind, the standard poker unit used for stack, pot, and profit size.'

export const SUIT_SYMBOLS: Record<string, string> = {
  h: '\u2665',
  d: '\u2666',
  c: '\u2663',
  s: '\u2660',
}

export const SUIT_COLORS: Record<string, string> = {
  h: 'text-red-600',
  d: 'text-blue-600',
  c: 'text-green-700',
  s: 'text-gray-900',
}

export const SUIT_LABELS: Record<string, string> = {
  s: 'Spades',
  h: 'Hearts',
  d: 'Diamonds',
  c: 'Clubs',
}

export const SUIT_BG_COLORS: Record<string, string> = {
  s: 'bg-gray-700 hover:bg-gray-600 border-gray-500',
  h: 'bg-red-900/60 hover:bg-red-800/60 border-red-700',
  d: 'bg-blue-900/60 hover:bg-blue-800/60 border-blue-700',
  c: 'bg-green-900/60 hover:bg-green-800/60 border-green-700',
}

export const RANK_LABELS: Record<string, string> = {
  '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7',
  '8': '8', '9': '9', 'T': '10', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A',
}

export const RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'] as const
export const SUITS = ['s', 'h', 'd', 'c'] as const

export const ACTION_COLORS: Record<string, string> = {
  fold: 'bg-red-600 hover:bg-red-700',
  call: 'bg-amber-600 hover:bg-amber-700',
  check: 'bg-gray-600 hover:bg-gray-700',
  bet_small: 'bg-green-700 hover:bg-green-800',
  bet_medium: 'bg-green-600 hover:bg-green-700',
  bet_large: 'bg-green-500 hover:bg-green-600',
  all_in: 'bg-purple-600 hover:bg-purple-700',
}

export const ACTION_LABELS: Record<string, string> = {
  fold: 'Fold',
  call: 'Call',
  check: 'Check',
  bet_small: 'Bet Small (33%)',
  bet_medium: 'Bet Medium (66%)',
  bet_large: 'Bet Large (Pot)',
  all_in: 'All In',
}
