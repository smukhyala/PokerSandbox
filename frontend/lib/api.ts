import axios from 'axios'
import type {
  AnalysisResult,
  GradeResult,
  ParseResult,
  StrategyDiagnoseResult,
  SimulationResult,
  StrategyExperimentResult,
  TrainingScenario,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export async function getTrainingScenario(): Promise<TrainingScenario> {
  const { data } = await api.get('/training-scenario')
  return data
}

export async function gradeScenario(
  scenarioId: string,
  chosenAction: string,
  handStrengthEstimate: number,
  bluffGuess: number,
): Promise<GradeResult> {
  const { data } = await api.post('/grade-scenario', {
    scenario_id: scenarioId,
    chosen_action: chosenAction,
    hand_strength_estimate: handStrengthEstimate,
    bluff_guess: bluffGuess,
  })
  return data
}

export async function analyzeHand(params: {
  hole_cards: string[]
  board: string[]
  pot_size_bb: number
  hero_stack_bb: number
  villain_stack_bb: number
  hero_position: string
}): Promise<AnalysisResult> {
  const { data } = await api.post('/analyze-hand', params)
  return data
}

export async function simulate(params: {
  agent_1: string
  agent_2: string
  num_hands: number
  strategy_config_1?: Record<string, unknown>
  strategy_config_2?: Record<string, unknown>
}): Promise<SimulationResult> {
  const { data } = await api.post('/simulate', params)
  return data
}

export async function parseStrategy(description: string): Promise<ParseResult> {
  const { data } = await api.post('/parse-strategy', { description })
  return data
}

export async function runStrategyExperiment(params: {
  description: string
  baseline_agent: string
  num_hands: number
  seed?: number
}): Promise<StrategyExperimentResult> {
  const { data } = await api.post('/strategy-experiment', {
    description: params.description,
    baseline_agent: params.baseline_agent,
    num_hands: params.num_hands,
    seed: params.seed ?? 42,
  })
  return data
}

export async function diagnoseStrategy(params: {
  description?: string
  strategy_config?: Record<string, unknown>
  baselines?: string[]
  num_hands: number
  seed?: number
  optimize?: boolean
  max_candidates?: number
}): Promise<StrategyDiagnoseResult> {
  const { data } = await api.post('/strategy-diagnose', {
    description: params.description ?? '',
    strategy_config: params.strategy_config,
    baselines: params.baselines ?? ['TAG', 'LAG', 'CallingStation', 'Random'],
    num_hands: params.num_hands,
    seed: params.seed ?? 42,
    optimize: params.optimize ?? true,
    max_candidates: params.max_candidates ?? 6,
  })
  return data
}
