import { useState } from 'react'
import CardGroup from '@/components/cards/CardGroup'
import CardSelector from '@/components/cards/CardSelector'
import { analyzeHand } from '@/lib/api'
import { ACTION_LABELS } from '@/lib/constants'
import type { AnalysisResult } from '@/types'
import clsx from 'clsx'

export default function AnalyzePage() {
  const [holeCards, setHoleCards] = useState<string[]>([])
  const [board, setBoard] = useState<string[]>([])
  const [potSize, setPotSize] = useState(6)
  const [heroStack, setHeroStack] = useState(97)
  const [villainStack, setVillainStack] = useState(97)
  const [heroPosition, setHeroPosition] = useState('BTN')
  const [selectingFor, setSelectingFor] = useState<'hole' | 'board' | null>(null)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)

  const allUsed = [...holeCards, ...board]

  const handleCardSelect = (card: string) => {
    if (selectingFor === 'hole' && holeCards.length < 2) {
      setHoleCards([...holeCards, card])
      if (holeCards.length === 1) setSelectingFor(null)
    } else if (selectingFor === 'board' && board.length < 5) {
      setBoard([...board, card])
      if (board.length === 4) setSelectingFor(null)
    }
  }

  const runAnalysis = async () => {
    if (holeCards.length !== 2) return
    setLoading(true)
    try {
      const res = await analyzeHand({
        hole_cards: holeCards,
        board,
        pot_size_bb: potSize,
        hero_stack_bb: heroStack,
        villain_stack_bb: villainStack,
        hero_position: heroPosition,
      })
      setResult(res)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  const reset = () => {
    setHoleCards([])
    setBoard([])
    setResult(null)
    setSelectingFor(null)
  }

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Analyze</h2>
        <p className="text-gray-400 text-sm mt-1">Break down any poker hand</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Inputs */}
        <div className="space-y-4">
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-gray-500">Hole Cards</p>
                <button onClick={() => setSelectingFor('hole')} className="text-xs text-amber-400 hover:text-amber-300">
                  {holeCards.length < 2 ? 'Select' : 'Change'}
                </button>
              </div>
              <CardGroup cards={holeCards} size="lg" emptySlots={2} onSlotClick={() => setSelectingFor('hole')} />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-gray-500">Board (0-5 cards)</p>
                <button onClick={() => setSelectingFor('board')} className="text-xs text-amber-400 hover:text-amber-300">
                  Add Card
                </button>
              </div>
              <CardGroup cards={board} size="lg" emptySlots={Math.max(board.length, 3)} onSlotClick={() => setSelectingFor('board')} />
            </div>

            {selectingFor && (
              <CardSelector
                onSelect={handleCardSelect}
                usedCards={allUsed}
                onCancel={() => setSelectingFor(null)}
              />
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Pot (BB)</label>
                <input type="number" value={potSize} onChange={e => setPotSize(Number(e.target.value))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Position</label>
                <select value={heroPosition} onChange={e => setHeroPosition(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
                  <option value="BTN">Button (BTN) — Dealer, acts last post-flop</option>
                  <option value="BB">Big Blind (BB) — Acts first post-flop</option>
                  <option value="SB">Small Blind (SB) — Posts half blind</option>
                  <option value="CO">Cutoff (CO) — One before button</option>
                  <option value="MP">Middle Position (MP)</option>
                  <option value="UTG">Under the Gun (UTG) — First to act</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Hero Stack (BB)</label>
                <input type="number" value={heroStack} onChange={e => setHeroStack(Number(e.target.value))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Villain Stack (BB)</label>
                <input type="number" value={villainStack} onChange={e => setVillainStack(Number(e.target.value))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>

            <div className="flex gap-3">
              <button onClick={runAnalysis} disabled={holeCards.length !== 2 || loading}
                className="flex-1 bg-amber-500 hover:bg-amber-600 disabled:bg-gray-700 disabled:text-gray-500 text-gray-900 font-semibold px-4 py-2.5 rounded-lg transition-colors">
                {loading ? 'Analyzing...' : 'Analyze Hand'}
              </button>
              <button onClick={reset}
                className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2.5 rounded-lg transition-colors">
                Reset
              </button>
            </div>
          </div>
        </div>

        {/* Right: Results */}
        <div>
          {result ? (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-4">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide">Analysis Results</h3>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-800 rounded-lg p-4 text-center">
                  <p className="text-xs text-gray-500">Equity</p>
                  <p className="text-3xl font-bold text-amber-400">{(result.equity * 100).toFixed(0)}%</p>
                </div>
                <div className="bg-gray-800 rounded-lg p-4 text-center">
                  <p className="text-xs text-gray-500">Hand Strength</p>
                  <p className="text-2xl font-bold text-white capitalize">{result.hand_strength}</p>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-1">Recommended Action</p>
                <p className="text-lg font-bold text-green-400">{ACTION_LABELS[result.recommended_action] || result.recommended_action}</p>
              </div>

              <div>
                <h4 className="text-xs text-gray-500 mb-2">Action EVs</h4>
                <div className="space-y-2">
                  {Object.entries(result.action_evs).sort(([,a], [,b]) => b - a).map(([action, ev]) => {
                    const maxEv = Math.max(...Object.values(result.action_evs))
                    const minEv = Math.min(...Object.values(result.action_evs))
                    const range = maxEv - minEv || 1
                    const pct = ((ev - minEv) / range) * 100
                    return (
                      <div key={action}>
                        <div className="flex justify-between text-sm mb-0.5">
                          <span className={action === result.recommended_action ? 'text-green-400' : 'text-gray-400'}>
                            {ACTION_LABELS[action] || action}
                          </span>
                          <span className="font-mono">{ev.toFixed(1)} BB</span>
                        </div>
                        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div className={clsx('h-full rounded-full', action === result.recommended_action ? 'bg-green-500' : 'bg-gray-500')}
                            style={{ width: `${Math.max(5, pct)}%` }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {result.bluff_probability != null && (
                <div className="bg-gray-800 rounded-lg p-4">
                  <p className="text-xs text-gray-500">Bluff Probability</p>
                  <p className="text-xl font-bold">{(result.bluff_probability * 100).toFixed(0)}%</p>
                </div>
              )}

              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-1">Reasoning</p>
                <p className="text-sm text-gray-300">{result.explanation}</p>
              </div>
            </div>
          ) : (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 flex items-center justify-center h-64">
              <p className="text-gray-500">Select cards and analyze to see results</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
