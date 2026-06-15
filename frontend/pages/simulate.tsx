import { useState, useCallback, useEffect } from 'react'
import { simulate } from '@/lib/api'
import { AGENT_DESCRIPTIONS, AGENT_LABELS, AGENT_TYPES, ACTION_LABELS, BB_EXPLANATION } from '@/lib/constants'
import type { AgentStats, HandSummary, SimulationResult, StrategyConfig } from '@/types'
import CardGroup from '@/components/cards/CardGroup'
import clsx from 'clsx'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'

const CUSTOM_STRATEGY_STORAGE_KEY = 'pokerlab.customStrategy'
const MAX_SIMULATION_HANDS = 1000

interface SavedCustomStrategy {
  config: StrategyConfig
  sourceText: string
  summary: string
  savedAt: string
}

export default function SimulatePage() {
  const [agent1, setAgent1] = useState('TAG')
  const [agent2, setAgent2] = useState('Random')
  const [numHands, setNumHands] = useState(1000)
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedHand, setSelectedHand] = useState<HandSummary | null>(null)
  const [customStrategy, setCustomStrategy] = useState<SavedCustomStrategy | null>(null)

  useEffect(() => {
    const raw = window.localStorage.getItem(CUSTOM_STRATEGY_STORAGE_KEY)
    if (!raw) return
    try {
      setCustomStrategy(JSON.parse(raw) as SavedCustomStrategy)
    } catch {
      window.localStorage.removeItem(CUSTOM_STRATEGY_STORAGE_KEY)
    }
  }, [])

  const runSimulation = async () => {
    if ((agent1 === 'Custom' || agent2 === 'Custom') && !customStrategy) {
      alert('Add a custom strategy in Strategy Lab first, then return here to simulate it.')
      return
    }
    setLoading(true)
    setResult(null)
    setSelectedHand(null)
    try {
      const res = await simulate({
        agent_1: agent1,
        agent_2: agent2,
        num_hands: clampHands(numHands),
        strategy_config_1: agent1 === 'Custom' ? customStrategy?.config as unknown as Record<string, unknown> : undefined,
        strategy_config_2: agent2 === 'Custom' ? customStrategy?.config as unknown as Record<string, unknown> : undefined,
      })
      setResult(res)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const [handInput, setHandInput] = useState('')

  const inspectHand = (num: number) => {
    if (!result?.hand_summaries?.length || num < 1 || num > result.hand_summaries.length) return
    setSelectedHand(result.hand_summaries[num - 1])
    setHandInput(String(num))
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleChartClick = useCallback((data: any) => {
    if (!result?.hand_summaries?.length || !data?.activePayload?.[0]) return
    const handNum = data.activePayload[0].payload.hand as number
    if (handNum >= 1 && handNum <= result.hand_summaries.length) {
      setSelectedHand(result.hand_summaries[handNum - 1])
      setHandInput(String(handNum))
    }
  }, [result])

  // Downsample bankroll data for cleaner chart (max 200 points)
  const chartData = result ? downsample(result.bankroll_history, 200) : []

  return (
    <div className="max-w-6xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Simulate</h2>
        <p className="text-[#4a4a4a] text-sm mt-1">Pit preset strategies against each other over thousands of hands. {BB_EXPLANATION}</p>
      </div>

      {/* Agent Key */}
      <div className="bg-[#fbfbfb] rounded-xl border border-[#ececec] p-4 mb-4">
        <h3 className="text-xs font-medium text-[#4a4a4a] uppercase tracking-wide mb-3">Agent Styles</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-2 text-sm">
          {AGENT_TYPES.map(agent => (
            <div key={agent} className="min-w-0">
              <span className="text-[#111111] font-medium">{AGENT_LABELS[agent]}</span>
              <span className="text-[#8a8a8a]"> - {getAgentDescription(agent, customStrategy)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Config */}
      <div className="bg-[#fbfbfb] rounded-xl border border-[#ececec] p-6 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
          <div>
            <label className="text-xs text-[#8a8a8a] block mb-1">Agent 1</label>
            <select value={agent1} onChange={e => setAgent1(e.target.value)}
              className="w-full bg-white border border-[#ececec] rounded-lg px-3 py-2.5 text-sm">
              {AGENT_TYPES.map(a => <option key={a} value={a}>{AGENT_LABELS[a]}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-[#8a8a8a] block mb-1">Agent 2</label>
            <select value={agent2} onChange={e => setAgent2(e.target.value)}
              className="w-full bg-white border border-[#ececec] rounded-lg px-3 py-2.5 text-sm">
              {AGENT_TYPES.map(a => <option key={a} value={a}>{AGENT_LABELS[a]}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-[#8a8a8a] block mb-1">Hands: {numHands.toLocaleString()} (maximum 1,000)</label>
            <input type="range" min="100" max={MAX_SIMULATION_HANDS} step="100" value={numHands}
              onChange={e => setNumHands(clampHands(Number(e.target.value)))}
              className="w-full accent-[#8a8a8a]" />
          </div>
        </div>
        {(agent1 === 'Custom' || agent2 === 'Custom') && (
          <div className="mt-4 rounded-lg border border-[#ececec] bg-[#fbfbfb] p-3 text-sm">
            {customStrategy ? (
              <>
                <p className="font-medium text-[#111111]">Custom Strategy Loaded</p>
                <p className="text-[#8a8a8a] mt-1">{formatCustomSummary(customStrategy.summary)}</p>
              </>
            ) : (
              <>
                <p className="font-medium text-[#111111]">Custom Strategy Needed</p>
                <p className="text-[#8a8a8a] mt-1">Open Strategy Lab, compile or diagnose a strategy, then return here to simulate it.</p>
              </>
            )}
          </div>
        )}
        <button onClick={runSimulation} disabled={loading}
          className="mt-4 bg-[#f7f7f7] border border-[#cfcfcf] hover:bg-white disabled:bg-[#f7f7f7] disabled:text-[#8a8a8a] text-[#111111] font-semibold px-6 py-2.5 rounded-lg transition-colors">
          {loading ? 'Simulating...' : 'Run Simulation'}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Bankroll Chart */}
          <div className="bg-[#fbfbfb] rounded-xl border border-[#ececec] p-6">
            <h3 className="text-sm font-medium text-[#4a4a4a] uppercase tracking-wide mb-4">Bankroll Over Time</h3>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={chartData} onClick={handleChartClick} style={{ cursor: 'crosshair' }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ececec" />
                <XAxis
                  dataKey="hand"
                  stroke="#6b7280"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v)}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v: number) => `${v >= 0 ? '+' : ''}${v}`}
                  label={{ value: 'Profit in big blinds', angle: -90, position: 'insideLeft', fill: '#6b7280', fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #cfcfcf', borderRadius: '8px', fontSize: 13, color: '#111111' }}
                  labelFormatter={(v) => `Hand #${v}`}
                  formatter={(value, name) => [`${Number(value) >= 0 ? '+' : ''}${Number(value).toFixed(1)} big blinds`, name]}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <ReferenceLine y={0} stroke="#cfcfcf" />
                <Line type="monotone" dataKey="agent_1_bankroll" stroke="#111111" name={displayAgentName(agent1, customStrategy)} dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="agent_2_bankroll" stroke="#8a8a8a" name={displayAgentName(agent2, customStrategy)} dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Hand Navigator */}
          {result.hand_summaries?.length > 0 && <div className="bg-[#fbfbfb] rounded-xl border border-[#ececec] p-4">
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-sm text-[#4a4a4a] shrink-0">Inspect hand:</p>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => inspectHand((selectedHand?.hand_number ?? 2) - 1)}
                  disabled={!selectedHand || selectedHand.hand_number <= 1}
                  className="px-3 py-1.5 bg-white hover:bg-[#f7f7f7] disabled:opacity-30 rounded text-sm"
                >&larr; Prev</button>
                <input
                  type="number"
                  min="1"
                  max={result.num_hands}
                  value={handInput}
                  onChange={e => setHandInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && inspectHand(Number(handInput))}
                  placeholder="Hand #"
                  className="w-24 bg-white border border-[#ececec] rounded px-3 py-1.5 text-sm text-center font-mono"
                />
                <button
                  onClick={() => inspectHand((selectedHand?.hand_number ?? 0) + 1)}
                  disabled={!selectedHand || selectedHand.hand_number >= result.num_hands}
                  className="px-3 py-1.5 bg-white hover:bg-[#f7f7f7] disabled:opacity-30 rounded text-sm"
                >Next &rarr;</button>
              </div>
              <button
                onClick={() => inspectHand(1)}
                className="px-3 py-1.5 bg-white hover:bg-[#f7f7f7] rounded text-xs text-[#8a8a8a]"
              >First</button>
              <button
                onClick={() => inspectHand(result.num_hands)}
                className="px-3 py-1.5 bg-white hover:bg-[#f7f7f7] rounded text-xs text-[#8a8a8a]"
              >Last</button>
              <p className="text-xs text-[#8a8a8a] sm:ml-auto">of {result.num_hands.toLocaleString()} hands</p>
            </div>
          </div>}

          {/* Hand Inspector */}
          {selectedHand && (
            <div className="bg-[#fbfbfb] rounded-xl border border-[#ececec] p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-[#111111] uppercase tracking-wide">
                  Hand #{selectedHand.hand_number}
                </h3>
                <button onClick={() => setSelectedHand(null)} className="text-xs text-[#8a8a8a] hover:text-[#4a4a4a]">Close</button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Cards */}
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-[#8a8a8a] mb-1">
                      {displayHandAgentLabel(agent1, customStrategy)}
                      <span className={clsx('ml-2 font-mono text-sm',
                        selectedHand.agent_1_profit_bb > 0 ? 'text-[#111111]' :
                        selectedHand.agent_1_profit_bb < 0 ? 'text-[#111111]' : 'text-[#4a4a4a]'
                      )}>
                        {selectedHand.agent_1_profit_bb > 0 ? '+' : ''}{selectedHand.agent_1_profit_bb} big blinds
                      </span>
                    </p>
                    <CardGroup cards={selectedHand.agent_1_cards} size="md" />
                  </div>
                  <div>
                    <p className="text-xs text-[#8a8a8a] mb-1">
                      {displayHandAgentLabel(agent2, customStrategy)}
                      <span className={clsx('ml-2 font-mono text-sm',
                        selectedHand.agent_2_profit_bb > 0 ? 'text-[#111111]' :
                        selectedHand.agent_2_profit_bb < 0 ? 'text-[#111111]' : 'text-[#4a4a4a]'
                      )}>
                        {selectedHand.agent_2_profit_bb > 0 ? '+' : ''}{selectedHand.agent_2_profit_bb} big blinds
                      </span>
                    </p>
                    <CardGroup cards={selectedHand.agent_2_cards} size="md" />
                  </div>
                  {selectedHand.board.length > 0 && (
                    <div>
                      <p className="text-xs text-[#8a8a8a] mb-1">Board</p>
                      <CardGroup cards={selectedHand.board} size="md" />
                    </div>
                  )}
                </div>

                {/* Action timeline */}
                <div>
                  <p className="text-xs text-[#8a8a8a] mb-2">Action Sequence</p>
                  <div className="space-y-1">
                    {selectedHand.actions.map((a, i) => {
                      const prevStreet = i > 0 ? selectedHand.actions[i - 1].street : null
                      const showStreetHeader = a.street !== prevStreet
                      return (
                        <div key={i}>
                          {showStreetHeader && (
                            <p className="text-xs text-[#8a8a8a] uppercase tracking-wide mt-2 mb-1 border-b border-[#ececec] pb-1">
                              {a.street}
                            </p>
                          )}
                          <div className="grid grid-cols-[minmax(0,1fr)_minmax(5rem,auto)_max-content] items-baseline gap-x-3 gap-y-1 text-sm py-1">
                            <span className={clsx(
                              'min-w-0 truncate font-medium',
                              a.agent === agent1 ? 'text-emerald-400' : 'text-[#111111]'
                            )} title={displayHandAgentLabel(a.agent, customStrategy)}>
                              {displayHandAgentLabel(a.agent, customStrategy)}
                            </span>
                            <span className="text-[#4a4a4a] whitespace-nowrap">
                              {ACTION_LABELS[a.action] || a.action}
                            </span>
                            {a.amount_bb > 0 && (
                              <span className="text-[#8a8a8a] font-mono text-xs whitespace-nowrap">{a.amount_bb} big blinds</span>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                  <div className="mt-3 pt-3 border-t border-[#ececec] text-sm">
                    <span className="text-[#8a8a8a]">Result: </span>
                    <span className={clsx(
                      'font-medium',
                      selectedHand.winner === agent1 ? 'text-emerald-400' :
                      selectedHand.winner === agent2 ? 'text-[#111111]' : 'text-[#4a4a4a]'
                    )}>
                      {selectedHand.winner === 'split' ? 'Split pot' : `${selectedHand.winner} wins`}
                    </span>
                    {selectedHand.went_to_showdown && <span className="text-[#8a8a8a] ml-2">(showdown)</span>}
                    {!selectedHand.went_to_showdown && <span className="text-[#8a8a8a] ml-2">(fold)</span>}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Stats Tables */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <StatsTable title={displayAgentName(agent1, customStrategy)} stats={result.agent_1_stats} color="text-emerald-400" />
            <StatsTable title={displayAgentName(agent2, customStrategy)} stats={result.agent_2_stats} color="text-[#111111]" />
          </div>
        </div>
      )}
    </div>
  )
}

function StatsTable({ title, stats, color }: { title: string; stats: AgentStats; color: string }) {
  const rows: [string, string][] = [
    ['Big blinds per 100 hands', `${stats.bb_per_100?.toFixed(1)} big blinds`],
    ['Win Rate', `${(stats.win_rate * 100)?.toFixed(1)}%`],
    ['Showdown Rate', `${(stats.showdown_rate * 100)?.toFixed(1)}%`],
    ['Showdown Win', `${(stats.showdown_win_rate * 100)?.toFixed(1)}%`],
    ['Aggression', stats.aggression_factor?.toFixed(2)],
    ['Fold %', `${(stats.fold_frequency * 100)?.toFixed(1)}%`],
    ['Bet %', `${(stats.bet_frequency * 100)?.toFixed(1)}%`],
    ['Total Profit', `${stats.total_profit_bb?.toFixed(1)} big blinds`],
  ]

  return (
    <div className="bg-[#fbfbfb] rounded-xl border border-[#ececec] p-6">
      <h3 className={`text-lg font-bold ${color} mb-4`}>{title}</h3>
      <table className="w-full text-sm">
        <tbody>
          {rows.map(([label, val]) => (
            <tr key={label} className="border-b border-[#ececec] last:border-0">
              <td className="py-2 text-[#4a4a4a]">{label}</td>
              <td className="py-2 font-mono text-right">{val}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function displayAgentName(agent: string, customStrategy: SavedCustomStrategy | null) {
  if (agent !== 'Custom') return AGENT_LABELS[agent] ?? agent
  if (!customStrategy) return 'Custom Strategy - add one in Strategy Lab'
  return `Custom Strategy - ${formatCustomSummary(customStrategy.summary)}`
}

function displayHandAgentLabel(agent: string, customStrategy: SavedCustomStrategy | null) {
  if (agent === 'Custom') return customStrategy ? 'Custom Strategy' : 'Custom'
  return AGENT_LABELS[agent] ?? agent
}

function getAgentDescription(agent: string, customStrategy: SavedCustomStrategy | null) {
  if (agent !== 'Custom') return AGENT_DESCRIPTIONS[agent]
  if (!customStrategy) return 'Add one in Strategy Lab to simulate it here.'
  return formatCustomSummary(customStrategy.summary)
}

function formatCustomSummary(summary: string) {
  if (summary.startsWith('Strategy:')) return summary
  const strategyText = summary.includes(':') ? summary.slice(summary.indexOf(':') + 1).trim() : summary.trim()
  return strategyText ? `Strategy: ${strategyText}` : 'Strategy: compiled in Strategy Lab'
}

function clampHands(value: number) {
  if (Number.isNaN(value)) return 10
  return Math.max(10, Math.min(MAX_SIMULATION_HANDS, value))
}

/** Downsample an array to at most `maxPoints` evenly spaced entries. */
function downsample<T>(data: T[], maxPoints: number): T[] {
  if (data.length <= maxPoints) return data
  const step = data.length / maxPoints
  const result: T[] = []
  for (let i = 0; i < maxPoints; i++) {
    result.push(data[Math.floor(i * step)])
  }
  // Always include the last point
  if (result[result.length - 1] !== data[data.length - 1]) {
    result.push(data[data.length - 1])
  }
  return result
}
