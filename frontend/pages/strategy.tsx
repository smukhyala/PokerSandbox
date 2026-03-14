import { useState } from 'react'
import { parseStrategy, simulate } from '@/lib/api'
import type { ParseResult, SimulationResult, StrategyConfig } from '@/types'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'

export default function StrategyPage() {
  const [text, setText] = useState('')
  const [parseResult, setParseResult] = useState<ParseResult | null>(null)
  const [config, setConfig] = useState<StrategyConfig | null>(null)
  const [simResult, setSimResult] = useState<SimulationResult | null>(null)
  const [baseline, setBaseline] = useState('TAG')
  const [loading, setLoading] = useState(false)
  const [simLoading, setSimLoading] = useState(false)

  const handleParse = async () => {
    if (!text.trim()) return
    setLoading(true)
    try {
      const res = await parseStrategy(text)
      setParseResult(res)
      setConfig(res.strategy)
      setSimResult(null)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const handleSimulate = async () => {
    if (!config) return
    setSimLoading(true)
    try {
      // Strip description field before sending — backend StrategyConfig expects it but
      // we want to ensure no extra/invalid fields cause validation errors
      const configPayload = { ...config }
      const res = await simulate({
        agent_1: 'Custom',
        agent_2: baseline,
        num_hands: 1000,
        strategy_config_1: configPayload as unknown as Record<string, unknown>,
      })
      setSimResult(res)
    } catch (e: unknown) {
      const err = e as { response?: { data?: unknown }; message?: string }
      console.error('Simulate error:', err.response?.data || err.message || e)
      alert(`Simulation failed: ${JSON.stringify(err.response?.data || err.message || 'unknown error')}`)
    }
    setSimLoading(false)
  }

  const updateConfig = (field: string, value: number) => {
    if (!config) return
    setConfig({ ...config, [field]: value })
  }

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Strategy Lab</h2>
        <p className="text-gray-400 text-sm mt-1">Define strategies in natural language and test them</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Strategy input */}
        <div className="space-y-4">
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-4">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide">Describe Your Strategy</h3>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="e.g., Play tight preflop, bet aggressively on dry boards, avoid big river bluffs..."
              className="w-full h-32 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm resize-none placeholder-gray-500 focus:border-amber-500 focus:ring-1 focus:ring-amber-500/50"
            />
            <button onClick={handleParse} disabled={!text.trim() || loading}
              className="bg-amber-500 hover:bg-amber-600 disabled:bg-gray-700 disabled:text-gray-500 text-gray-900 font-semibold px-6 py-2.5 rounded-lg transition-colors">
              {loading ? 'Parsing...' : 'Parse Strategy'}
            </button>

            {parseResult && (
              <div className="text-sm space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-gray-500">Confidence:</span>
                  <span className={parseResult.confidence > 0.5 ? 'text-green-400' : 'text-amber-400'}>
                    {(parseResult.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                {parseResult.matched_keywords.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {parseResult.matched_keywords.map(kw => (
                      <span key={kw} className="bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded text-xs">{kw}</span>
                    ))}
                  </div>
                )}
                {parseResult.warnings.map((w, i) => (
                  <p key={i} className="text-orange-400 text-xs">{w}</p>
                ))}
              </div>
            )}
          </div>

          {/* Config editor */}
          {config && (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-3">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide">Strategy Config</h3>
              <ConfigSlider label="Tightness" value={config.tightness} onChange={v => updateConfig('tightness', v)} />
              <ConfigSlider label="Aggression" value={config.aggression} onChange={v => updateConfig('aggression', v)} />
              <ConfigSlider label="C-Bet Freq" value={config.continuation_bet_frequency} onChange={v => updateConfig('continuation_bet_frequency', v)} />
              <ConfigSlider label="Fold to Aggression" value={config.fold_to_aggression} onChange={v => updateConfig('fold_to_aggression', v)} />
              <ConfigSlider label="Flop Bluff Freq" value={config.flop.bluff_frequency} onChange={v => setConfig({...config, flop: {...config.flop, bluff_frequency: v}})} />
              <ConfigSlider label="Turn Bluff Freq" value={config.turn.bluff_frequency} onChange={v => setConfig({...config, turn: {...config.turn, bluff_frequency: v}})} />
              <ConfigSlider label="River Bluff Freq" value={config.river.bluff_frequency} onChange={v => setConfig({...config, river: {...config.river, bluff_frequency: v}})} />

              <div className="flex gap-3 items-end pt-2">
                <div className="flex-1">
                  <label className="text-xs text-gray-500 block mb-1">Baseline</label>
                  <select value={baseline} onChange={e => setBaseline(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
                    {['TAG', 'LAG', 'CallingStation', 'Random'].map(a => <option key={a} value={a}>{a}</option>)}
                  </select>
                </div>
                <button onClick={handleSimulate} disabled={simLoading}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors">
                  {simLoading ? 'Running...' : 'Simulate vs Baseline'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right: Results */}
        <div>
          {simResult ? (
            <div className="space-y-6">
              <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
                <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-4">Results: Custom vs {baseline}</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={simResult.bankroll_history}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="hand" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }} />
                    <Legend />
                    <ReferenceLine y={0} stroke="#6B7280" strokeDasharray="3 3" />
                    <Line type="monotone" dataKey="agent_1_bankroll" stroke="#10B981" name="Your Strategy" dot={false} strokeWidth={2} />
                    <Line type="monotone" dataKey="agent_2_bankroll" stroke="#F59E0B" name={baseline} dot={false} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
                <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-4">Comparison</h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-2 text-gray-500">Metric</th>
                      <th className="text-right py-2 text-green-400">Your Strategy</th>
                      <th className="text-right py-2 text-amber-400">{baseline}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ['BB/100', simResult.agent_1_stats.bb_per_100, simResult.agent_2_stats.bb_per_100, true],
                      ['Win Rate', (simResult.agent_1_stats.win_rate as number) * 100, (simResult.agent_2_stats.win_rate as number) * 100, false],
                      ['Aggression', simResult.agent_1_stats.aggression_factor, simResult.agent_2_stats.aggression_factor, false],
                      ['Showdown %', (simResult.agent_1_stats.showdown_rate as number) * 100, (simResult.agent_2_stats.showdown_rate as number) * 100, false],
                      ['Fold %', (simResult.agent_1_stats.fold_frequency as number) * 100, (simResult.agent_2_stats.fold_frequency as number) * 100, false],
                    ].map(([label, v1, v2, isBB]) => (
                      <tr key={label as string} className="border-b border-gray-800">
                        <td className="py-2 text-gray-400">{label as string}</td>
                        <td className="py-2 font-mono text-right">{(v1 as number).toFixed(1)}{isBB ? ' BB' : '%'}</td>
                        <td className="py-2 font-mono text-right">{(v2 as number).toFixed(1)}{isBB ? ' BB' : '%'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 flex items-center justify-center h-64">
              <p className="text-gray-500">Parse a strategy and simulate to see results</p>
            </div>
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
        <span className="text-gray-500">{label}</span>
        <span className="text-gray-300 font-mono">{(value * 100).toFixed(0)}%</span>
      </div>
      <input type="range" min="0" max="100" value={value * 100}
        onChange={e => onChange(Number(e.target.value) / 100)}
        className="w-full accent-amber-500" />
    </div>
  )
}
