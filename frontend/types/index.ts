export type Suit = 'h' | 'd' | 'c' | 's'
export type Rank = '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | 'T' | 'J' | 'Q' | 'K' | 'A'

export interface Card {
  rank: Rank
  suit: Suit
  str: string // e.g., "Ah"
}

export type Street = 'preflop' | 'flop' | 'turn' | 'river'
export type ActionType = 'fold' | 'call' | 'check' | 'bet_small' | 'bet_medium' | 'bet_large' | 'all_in'

export interface PlayerAction {
  player: string
  action: string
  amount: number
}

// Training
export interface TrainingScenario {
  scenario_id: string
  hole_cards: string[]
  board: string[]
  pot_size_bb: number
  hero_stack_bb: number
  villain_stack_bb: number
  hero_position: string
  street: string
  action_history: PlayerAction[]
  legal_actions: string[]
  prompt: string
}

export interface GradeResult {
  score: number
  grade: string
  predicted_equity: number
  recommended_action: string
  action_evs: Record<string, number>
  chosen_ev: number
  optimal_ev: number
  ev_loss: number
  bluff_probability: number | null
  explanation: string
}

// Analysis
export interface AnalysisResult {
  hand_strength: string
  hand_strength_probs: Record<string, number>
  equity: number
  recommended_action: string
  action_evs: Record<string, number>
  bluff_probability: number | null
  explanation: string
}

// Simulation
export type AgentType = 'TAG' | 'LAG' | 'CallingStation' | 'Random' | 'MLAgent' | 'Custom'

export interface AgentStats {
  agent_name: string
  total_hands: number
  total_profit_bb: number
  bb_per_100: number
  win_rate: number
  showdown_rate: number
  showdown_win_rate: number
  aggression_factor: number
  fold_frequency: number
  bet_frequency: number
  call_frequency: number
  hands_won: number
}

export interface BankrollDataPoint {
  hand: number
  agent_1_bankroll: number
  agent_2_bankroll: number
}

export interface HandAction {
  agent: string
  action: string
  amount_bb: number
  street: string
}

export interface HandSummary {
  hand_number: number
  agent_1_cards: string[]
  agent_2_cards: string[]
  board: string[]
  agent_1_profit_bb: number
  agent_2_profit_bb: number
  went_to_showdown: boolean
  winner: string | null
  final_street: string
  actions: HandAction[]
}

export interface SimulationResult {
  num_hands: number
  agent_1_stats: AgentStats
  agent_2_stats: AgentStats
  bankroll_history: BankrollDataPoint[]
  hand_summaries: HandSummary[]
}

// Strategy
export interface StrategyConfig {
  name: string
  description: string
  tightness: number
  aggression: number
  preflop: {
    open_raise_range: number
    three_bet_range: number
    call_raise_range: number
    open_size: string
    limp_frequency: number
  }
  flop: StreetStrategyConfig
  turn: StreetStrategyConfig
  river: StreetStrategyConfig
  continuation_bet_frequency: number
  fold_to_aggression: number
  positional_awareness: number
}

export interface StreetStrategyConfig {
  value_bet_threshold: number
  call_threshold: number
  bet_sizing: string
  bluff_sizing: string
  bluff_frequency: number
  draw_aggression: number
}

export interface ParseResult {
  strategy: StrategyConfig
  matched_keywords: string[]
  confidence: number
  warnings: string[]
}
