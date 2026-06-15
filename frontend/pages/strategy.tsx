import { useState } from 'react'
import { motion } from 'motion/react'
import { diagnoseStrategy, runStrategyExperiment, simulate } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AGENT_DESCRIPTIONS, AGENT_LABELS, BB_EXPLANATION } from '@/lib/constants'
import type {
  ParseResult,
  SimulationResult,
  StrategyConfig,
  StrategyDiagnoseResult,
  StrategyExperimentResult,
} from '@/types'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'

const CUSTOM_STRATEGY_STORAGE_KEY = 'pokerlab.customStrategy'
const MAX_SIMULATION_HANDS = 1000

export default function StrategyPage() {
  const [text, setText] = useState('')
  const [parseResult, setParseResult] = useState<ParseResult | null>(null)
  const [config, setConfig] = useState<StrategyConfig | null>(null)
  const [simResult, setSimResult] = useState<SimulationResult | null>(null)
  const [experimentResult, setExperimentResult] = useState<StrategyExperimentResult | null>(null)
  const [diagnoseResult, setDiagnoseResult] = useState<StrategyDiagnoseResult | null>(null)
  const [baseline, setBaseline] = useState('TAG')
  const [numHands, setNumHands] = useState(1000)
  const [simLoading, setSimLoading] = useState(false)

  const handleSimulate = async () => {
    if (!config) return
    setSimLoading(true)
    try {
      const res = await simulate({
        agent_1: 'Custom',
        agent_2: baseline,
        num_hands: numHands,
        strategy_config_1: { ...config } as unknown as Record<string, unknown>,
      })
      setSimResult(res)
      setExperimentResult(null)
      setDiagnoseResult(null)
    } catch (e: unknown) {
      const err = e as { response?: { data?: unknown }; message?: string }
      alert(`Simulation failed: ${JSON.stringify(err.response?.data || err.message || 'unknown error')}`)
    }
    setSimLoading(false)
  }

  const handleExperiment = async () => {
    if (!text.trim()) return
    setSimLoading(true)
    try {
      const res = await runStrategyExperiment({
        description: text,
        baseline_agent: baseline,
        num_hands: numHands,
      })
      setExperimentResult(res)
      setDiagnoseResult(null)
      setParseResult({
        strategy: res.parsed_strategy,
        matched_keywords: res.matched_keywords,
        confidence: res.confidence,
        warnings: res.warnings,
      })
      setConfig(res.parsed_strategy)
      saveCustomStrategy(res.parsed_strategy, text)
      setSimResult({
        num_hands: res.num_hands,
        agent_1_stats: res.agent_1_stats,
        agent_2_stats: res.agent_2_stats,
        bankroll_history: res.bankroll_history,
        hand_summaries: [],
      })
    } catch (e: unknown) {
      const err = e as { response?: { data?: unknown }; message?: string }
      alert(`Experiment failed: ${JSON.stringify(err.response?.data || err.message || 'unknown error')}`)
    }
    setSimLoading(false)
  }

  const handleDiagnose = async () => {
    if (!text.trim()) return
    setSimLoading(true)
    try {
      const res = await diagnoseStrategy({
        description: text,
        num_hands: numHands,
        optimize: true,
        max_candidates: 6,
      })
      setDiagnoseResult(res)
      setExperimentResult(null)
      setParseResult({
        strategy: res.parsed_strategy,
        matched_keywords: res.matched_keywords,
        confidence: res.confidence,
        warnings: res.warnings,
      })
      setConfig(res.parsed_strategy)
      saveCustomStrategy(res.parsed_strategy, text)
      const first = res.matchup_results[0]
      if (first) {
        setBaseline(first.baseline_agent)
        setSimResult({
          num_hands: res.num_hands_per_matchup,
          agent_1_stats: first.agent_1_stats,
          agent_2_stats: first.agent_2_stats,
          bankroll_history: [],
          hand_summaries: [],
        })
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: unknown }; message?: string }
      alert(`Diagnosis failed: ${JSON.stringify(err.response?.data || err.message || 'unknown error')}`)
    }
    setSimLoading(false)
  }

  const rerunDiagnosisForConfig = async (nextConfig: StrategyConfig) => {
    setSimLoading(true)
    try {
      const res = await diagnoseStrategy({
        strategy_config: nextConfig as unknown as Record<string, unknown>,
        num_hands: numHands,
        optimize: true,
        max_candidates: 6,
      })
      setDiagnoseResult(res)
      setExperimentResult(null)
      setParseResult({
        strategy: res.parsed_strategy,
        matched_keywords: res.matched_keywords,
        confidence: res.confidence,
        warnings: res.warnings,
      })
      setConfig(res.parsed_strategy)
      saveCustomStrategy(res.parsed_strategy, text)
      const first = res.matchup_results[0]
      if (first) {
        setBaseline(first.baseline_agent)
        setSimResult({
          num_hands: res.num_hands_per_matchup,
          agent_1_stats: first.agent_1_stats,
          agent_2_stats: first.agent_2_stats,
          bankroll_history: [],
          hand_summaries: [],
        })
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: unknown }; message?: string }
      alert(`Patch diagnosis failed: ${JSON.stringify(err.response?.data || err.message || 'unknown error')}`)
    }
    setSimLoading(false)
  }

  const updateConfig = (field: string, value: number) => {
    if (!config) return
    setConfig({ ...config, [field]: value })
  }

  return (
    <div className="max-w-6xl">
      <div className="mb-8">
        <Badge variant="outline" className="mb-3">Natural-language strategy compiler</Badge>
        <h2 className="text-3xl font-semibold tracking-tight">Strategy Lab</h2>
        <p className="text-zinc-400 text-sm mt-2 max-w-2xl">
          Compile poker ideas into executable agents, stress-test them, detect leaks, and patch strategy parameters. {BB_EXPLANATION}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Describe Strategy</CardTitle>
              <CardDescription>Write the policy you want PokerLab to compile.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <textarea
                value={text}
                onChange={e => setText(e.target.value)}
                placeholder="Play loose aggressive, bluff rivers often, never fold to pressure..."
                className="w-full h-32 bg-zinc-950 border border-white/10 rounded-md px-4 py-3 text-sm resize-none placeholder-zinc-600 focus:border-white focus:ring-1 focus:ring-white/30 outline-none"
              />
              <Button onClick={handleDiagnose} disabled={simLoading || !text.trim()}>
                {simLoading ? 'Running...' : 'Compile and Diagnose'}
              </Button>

              {parseResult && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-3 border-t border-white/10 pt-4"
                >
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-zinc-500">Confidence</span>
                    <span className="font-mono text-white">{(parseResult.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {parseResult.matched_keywords.map(kw => (
                      <Badge key={kw} variant="muted">{kw}</Badge>
                    ))}
                  </div>
                  {parseResult.warnings.map((w, i) => (
                    <p key={i} className="text-xs text-zinc-400">{w}</p>
                  ))}
                </motion.div>
              )}
            </CardContent>
          </Card>

          {config && (
            <Card>
              <CardHeader>
                <CardTitle>Compiled Policy</CardTitle>
                <CardDescription>Adjust the executable parameters before testing.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ConfigSlider label="Tightness" value={config.tightness} onChange={v => updateConfig('tightness', v)} />
                <ConfigSlider label="Aggression" value={config.aggression} onChange={v => updateConfig('aggression', v)} />
                <ConfigSlider label="C-Bet Frequency" value={config.continuation_bet_frequency} onChange={v => updateConfig('continuation_bet_frequency', v)} />
                <ConfigSlider label="Fold to Aggression" value={config.fold_to_aggression} onChange={v => updateConfig('fold_to_aggression', v)} />
                <ConfigSlider label="Flop Bluff Frequency" value={config.flop.bluff_frequency} onChange={v => setConfig({...config, flop: {...config.flop, bluff_frequency: v}})} />
                <ConfigSlider label="Turn Bluff Frequency" value={config.turn.bluff_frequency} onChange={v => setConfig({...config, turn: {...config.turn, bluff_frequency: v}})} />
                <ConfigSlider label="River Bluff Frequency" value={config.river.bluff_frequency} onChange={v => setConfig({...config, river: {...config.river, bluff_frequency: v}})} />

                <div className="grid grid-cols-2 gap-3 pt-2">
                  <label className="text-xs text-zinc-500">
                    Baseline
                    <select value={baseline} onChange={e => setBaseline(e.target.value)}
                      className="mt-1 w-full bg-zinc-950 border border-white/10 rounded-md px-3 py-2 text-sm text-white">
                      {['TAG', 'LAG', 'CallingStation', 'Random'].map(a => (
                        <option key={a} value={a}>{AGENT_LABELS[a]}</option>
                      ))}
                    </select>
                  </label>
                  <label className="text-xs text-zinc-500">
                    Hands
                    <input
	                      type="number"
	                      min="10"
	                      max={MAX_SIMULATION_HANDS}
	                      step="100"
	                      value={numHands}
	                      onChange={e => setNumHands(clampHands(Number(e.target.value)))}
	                      className="mt-1 w-full bg-zinc-950 border border-white/10 rounded-md px-3 py-2 text-sm text-white"
	                    />
                    <span className="mt-1 block text-[11px] text-zinc-600">Maximum: 1,000 hands for compute.</span>
	                  </label>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button onClick={handleSimulate} disabled={simLoading} variant="outline">
                    {simLoading ? 'Running...' : 'Simulate'}
                  </Button>
                  <Button onClick={handleExperiment} disabled={simLoading || !text.trim()} variant="secondary">
                    {simLoading ? 'Running...' : 'Experiment'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Preset Strategies</CardTitle>
              <CardDescription>The built-in opponents used for experiments and leak detection.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {['TAG', 'LAG', 'CallingStation', 'Random'].map(agent => (
                <div key={agent} className="rounded-md border border-white/10 bg-zinc-950 p-3">
                  <div className="text-sm font-medium text-white">{AGENT_LABELS[agent]}</div>
                  <p className="text-xs text-zinc-500 mt-1">{AGENT_DESCRIPTIONS[agent]}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          {diagnoseResult && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <Card>
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <CardTitle>Diagnosis</CardTitle>
                      <CardDescription className="mt-2">{diagnoseResult.summary}</CardDescription>
                    </div>
                    <div className="text-right">
                      <div className="text-4xl font-semibold">{diagnoseResult.aggregate_score}</div>
                      <div className="text-xs text-zinc-500">score</div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-2">
                    {diagnoseResult.matchup_results.map(result => (
                      <div key={result.baseline_agent} className="rounded-md border border-white/10 bg-zinc-950 p-3">
                        <div className="text-xs text-zinc-500">{AGENT_LABELS[result.baseline_agent] ?? result.baseline_agent}</div>
                        <div className="font-mono text-sm text-white">
                          {(result.summary.delta_bb_per_100 as number).toFixed(1)} big blinds per 100 hands
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="space-y-3">
                    {diagnoseResult.detailed_feedback?.length > 0 && (
                      <div className="rounded-md border border-white/10 bg-zinc-950 p-4">
                        <h4 className="font-medium">Why this is good or bad</h4>
                        <div className="mt-3 space-y-2">
                          {diagnoseResult.detailed_feedback.map(item => (
                            <p key={item} className="text-sm text-zinc-400 leading-relaxed">{item}</p>
                          ))}
                        </div>
                      </div>
                    )}

                    {diagnoseResult.leaks.length > 0 ? diagnoseResult.leaks.map(leak => (
                      <motion.div
                        key={leak.leak_type}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="rounded-md border border-white/10 bg-zinc-950 p-4"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <h4 className="font-medium">{leak.leak_type}</h4>
                          <Badge variant="outline">{leak.severity}</Badge>
                        </div>
                        <ul className="mt-3 space-y-1">
                          {leak.evidence.map(item => (
                            <li key={item} className="text-xs text-zinc-500">{item}</li>
                          ))}
                        </ul>
                        <p className="text-sm text-zinc-300 mt-3">{leak.recommendation}</p>
                        <div className="mt-3 flex flex-wrap gap-1">
                          {Object.entries(leak.suggested_parameter_changes).map(([key, value]) => (
                            <Badge key={key} variant="muted">{key}: {value.toFixed(2)}</Badge>
                          ))}
                        </div>
                      </motion.div>
                    )) : (
                      <p className="text-sm text-zinc-400">No major leaks triggered in this stress test.</p>
                    )}
                  </div>

                  {diagnoseResult.optimization && (
                    <div className="rounded-md border border-white/10 bg-white text-black p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h4 className="font-semibold">Recommended Patch</h4>
                          <p className="text-sm text-zinc-700 mt-1">{diagnoseResult.optimization.reason}</p>
                        </div>
                        {diagnoseResult.optimization.best_score !== null && (
                          <div className="text-right">
                            <div className="text-2xl font-semibold">{diagnoseResult.optimization.best_score}</div>
                            <div className="text-xs text-zinc-600">
                              {diagnoseResult.optimization.improvement !== null && diagnoseResult.optimization.improvement >= 0 ? '+' : ''}
                              {diagnoseResult.optimization.improvement ?? 0} pts
                            </div>
                          </div>
                        )}
                      </div>

                      {diagnoseResult.optimization.changes.length > 0 && (
                        <div className="mt-4 space-y-2">
                          {diagnoseResult.optimization.changes.map(change => (
                            <div key={`${change.parameter}-${change.after}`} className="flex items-center justify-between gap-3 text-sm">
                              <span>{change.parameter}</span>
                              <span className="font-mono text-zinc-700">
                                {Number(change.before).toFixed(2)} {'->'} {Number(change.after).toFixed(2)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

                      <Button
                        onClick={() => {
                          const nextConfig = diagnoseResult.optimization?.best_config ?? config
                          if (nextConfig) {
                            setConfig(nextConfig)
                            saveCustomStrategy(nextConfig, text)
                            void rerunDiagnosisForConfig(nextConfig)
                          }
                        }}
                        disabled={simLoading}
                        className="mt-4"
                        variant="secondary"
                      >
                        {simLoading ? 'Rerunning...' : 'Apply Patch and Rerun'}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {simResult ? (
            <Card>
              <CardHeader>
                <CardTitle>Results</CardTitle>
                <CardDescription>Custom strategy vs {baseline}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {experimentResult && (
                  <div className="space-y-2">
                    {experimentResult.product_insights.map((insight, i) => (
                      <p key={i} className="text-sm text-zinc-300 rounded-md border border-white/10 bg-zinc-950 px-3 py-2">
                        {insight}
                      </p>
                    ))}
                  </div>
                )}
                {simResult.bankroll_history.length > 0 && (
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={simResult.bankroll_history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="hand" stroke="#a1a1aa" />
                      <YAxis stroke="#a1a1aa" />
                      <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid rgba(255,255,255,.14)', borderRadius: '8px' }} />
                      <Legend />
                      <ReferenceLine y={0} stroke="#52525b" strokeDasharray="3 3" />
                      <Line type="monotone" dataKey="agent_1_bankroll" stroke="#fff" name="Your Strategy" dot={false} strokeWidth={2} />
                      <Line type="monotone" dataKey="agent_2_bankroll" stroke="#71717a" name={baseline} dot={false} strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                )}

                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="text-left py-2 text-zinc-500">Metric</th>
                      <th className="text-right py-2 text-white">Strategy</th>
                      <th className="text-right py-2 text-zinc-400">{baseline}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ['Big blinds per 100 hands', simResult.agent_1_stats.bb_per_100, simResult.agent_2_stats.bb_per_100, true],
                      ['Win Rate', (simResult.agent_1_stats.win_rate as number) * 100, (simResult.agent_2_stats.win_rate as number) * 100, false],
                      ['Aggression', simResult.agent_1_stats.aggression_factor, simResult.agent_2_stats.aggression_factor, false],
                      ['Showdown %', (simResult.agent_1_stats.showdown_rate as number) * 100, (simResult.agent_2_stats.showdown_rate as number) * 100, false],
                      ['Fold %', (simResult.agent_1_stats.fold_frequency as number) * 100, (simResult.agent_2_stats.fold_frequency as number) * 100, false],
                    ].map(([label, v1, v2, isBB]) => (
                      <tr key={label as string} className="border-b border-white/10">
                        <td className="py-2 text-zinc-400">{label as string}</td>
                        <td className="py-2 font-mono text-right">{(v1 as number).toFixed(1)}{isBB ? ' big blinds' : '%'}</td>
                        <td className="py-2 font-mono text-right text-zinc-400">{(v2 as number).toFixed(1)}{isBB ? ' big blinds' : '%'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          ) : (
            <Card className="min-h-64 flex items-center justify-center">
              <p className="text-zinc-500 text-sm">Compile a strategy to see diagnostics.</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

function ConfigSlider({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-zinc-500">{label}</span>
        <span className="text-zinc-300 font-mono">{(value * 100).toFixed(0)}%</span>
      </div>
      <input type="range" min="0" max="100" value={value * 100}
        onChange={e => onChange(Number(e.target.value) / 100)}
        className="w-full accent-white" />
    </div>
  )
}

function saveCustomStrategy(config: StrategyConfig, sourceText: string) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(CUSTOM_STRATEGY_STORAGE_KEY, JSON.stringify({
    config,
    sourceText,
    summary: summarizeStrategy(config, sourceText),
    savedAt: new Date().toISOString(),
  }))
}

function summarizeStrategy(config: StrategyConfig, sourceText: string) {
  const range = config.tightness >= 0.65 ? 'tight' : config.tightness <= 0.35 ? 'loose' : 'balanced range'
  const pressure = config.aggression >= 0.65 ? 'aggressive' : config.aggression <= 0.35 ? 'passive' : 'balanced pressure'
  const river = config.river.bluff_frequency >= 0.20 ? 'river bluffing' : 'low river bluffing'
  const source = sourceText.trim()
  return source ? `Strategy: ${source.slice(0, 90)}` : `Strategy: ${range}, ${pressure}, ${river}`
}

function clampHands(value: number) {
  if (Number.isNaN(value)) return 10
  return Math.max(10, Math.min(MAX_SIMULATION_HANDS, value))
}
