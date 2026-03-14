import { useState } from 'react'
import { RANKS, SUITS, SUIT_SYMBOLS, SUIT_LABELS, RANK_LABELS } from '@/lib/constants'
import clsx from 'clsx'

interface CardSelectorProps {
  onSelect: (card: string) => void
  usedCards: string[]
  onCancel?: () => void
}

// Inline colors to avoid Tailwind purge issues
const SUIT_HEX: Record<string, string> = {
  h: '#dc2626',
  d: '#2563eb',
  c: '#15803d',
  s: '#111827',
}

const SUIT_BG_HEX: Record<string, string> = {
  s: '#1f2937',
  h: '#3b1111',
  d: '#0c1a3d',
  c: '#0a2618',
}

const SUIT_BORDER_HEX: Record<string, string> = {
  s: '#6b7280',
  h: '#dc2626',
  d: '#2563eb',
  c: '#15803d',
}

export default function CardSelector({ onSelect, usedCards, onCancel }: CardSelectorProps) {
  const [selectedSuit, setSelectedSuit] = useState<string | null>(null)

  const handleRankSelect = (rank: string) => {
    if (!selectedSuit) return
    const card = `${rank}${selectedSuit}`
    if (!usedCards.includes(card)) {
      onSelect(card)
      setSelectedSuit(null)
    }
  }

  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      {!selectedSuit ? (
        <>
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm text-gray-400">Pick a suit:</p>
            {onCancel && (
              <button onClick={onCancel} className="text-xs text-gray-500 hover:text-gray-300">Cancel</button>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2">
            {SUITS.map(suit => {
              const available = RANKS.filter(r => !usedCards.includes(`${r}${suit}`)).length
              return (
                <button
                  key={suit}
                  onClick={() => setSelectedSuit(suit)}
                  disabled={available === 0}
                  className={clsx(
                    'flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-all',
                    available === 0 ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer hover:brightness-125',
                  )}
                  style={{
                    backgroundColor: available === 0 ? '#1f2937' : SUIT_BG_HEX[suit],
                    borderColor: available === 0 ? '#374151' : SUIT_BORDER_HEX[suit],
                  }}
                >
                  <span className="text-2xl" style={{ color: SUIT_HEX[suit] }}>
                    {SUIT_SYMBOLS[suit]}
                  </span>
                  <div className="text-left">
                    <p className="text-sm font-medium text-white">{SUIT_LABELS[suit]}</p>
                    <p className="text-xs text-gray-400">{available} available</p>
                  </div>
                </button>
              )
            })}
          </div>
        </>
      ) : (
        <>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSelectedSuit(null)}
                className="text-xs text-gray-500 hover:text-gray-300"
              >
                &larr; Back
              </button>
              <span className="text-lg" style={{ color: SUIT_HEX[selectedSuit] }}>
                {SUIT_SYMBOLS[selectedSuit]}
              </span>
              <p className="text-sm text-gray-400">{SUIT_LABELS[selectedSuit]} &mdash; pick rank:</p>
            </div>
            {onCancel && (
              <button onClick={onCancel} className="text-xs text-gray-500 hover:text-gray-300">Cancel</button>
            )}
          </div>
          <div className="grid grid-cols-5 gap-1.5">
            {RANKS.map(rank => {
              const card = `${rank}${selectedSuit}`
              const isUsed = usedCards.includes(card)
              return (
                <button
                  key={rank}
                  onClick={() => handleRankSelect(rank)}
                  disabled={isUsed}
                  className={clsx(
                    'py-2.5 rounded-lg text-sm font-bold border-2 transition-all',
                    isUsed
                      ? 'opacity-20 cursor-not-allowed bg-gray-800 border-gray-700 text-gray-500'
                      : 'bg-white cursor-pointer hover:scale-105 hover:border-amber-400 border-gray-300',
                  )}
                  style={isUsed ? undefined : { color: SUIT_HEX[selectedSuit] }}
                >
                  {RANK_LABELS[rank]}
                </button>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
