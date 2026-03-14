export const AGENT_TYPES = ['TAG', 'LAG', 'CallingStation', 'Random', 'MLAgent', 'Custom'] as const

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
