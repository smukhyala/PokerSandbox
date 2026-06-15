import { SUIT_SYMBOLS } from '@/lib/constants'
import clsx from 'clsx'

interface PokerCardProps {
  card?: string  // e.g., "Ah", "Td"
  size?: 'sm' | 'md' | 'lg'
  faceDown?: boolean
  onClick?: () => void
  selected?: boolean
}

const SIZES = {
  sm: 'w-10 h-14 text-xs',
  md: 'w-14 h-20 text-sm',
  lg: 'w-20 h-28 text-lg',
}

// Inline hex colors — immune to Tailwind purging
const SUIT_HEX: Record<string, string> = {
  h: '#dc2626', // red
  d: '#2563eb', // blue
  c: '#15803d', // green
  s: '#111827', // near-black
}

export default function PokerCard({ card, size = 'md', faceDown, onClick, selected }: PokerCardProps) {
  if (!card || faceDown) {
    return (
      <div className={clsx(
        SIZES[size],
        'rounded-lg border-2 border-[#cfcfcf] bg-[#f7f7f7] flex items-center justify-center cursor-default',
        onClick && 'cursor-pointer hover:border-[#111111]',
      )} onClick={onClick}>
        <span className="text-[#8a8a8a] text-xl">?</span>
      </div>
    )
  }

  const rank = card[0]
  const suit = card[1] as 'h' | 'd' | 'c' | 's'
  const suitSymbol = SUIT_SYMBOLS[suit] || suit
  const color = SUIT_HEX[suit] || '#111827'

  return (
    <div
      className={clsx(
        SIZES[size],
        'rounded-lg border-2 bg-white flex flex-col items-center justify-center font-bold cursor-default select-none',
        selected ? 'border-[#111111] ring-2 ring-[#111111]/20' : 'border-[#cfcfcf]',
        onClick && 'cursor-pointer hover:border-[#111111] hover:scale-105 transition-transform',
      )}
      onClick={onClick}
    >
      <span className="leading-none" style={{ color }}>
        {rank === 'T' ? '10' : rank}
      </span>
      <span className="leading-none" style={{ color }}>
        {suitSymbol}
      </span>
    </div>
  )
}
