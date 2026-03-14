import PokerCard from './PokerCard'

interface CardGroupProps {
  cards: string[]
  size?: 'sm' | 'md' | 'lg'
  emptySlots?: number
  onSlotClick?: (index: number) => void
}

export default function CardGroup({ cards, size = 'md', emptySlots = 0, onSlotClick }: CardGroupProps) {
  const totalSlots = Math.max(cards.length, emptySlots)

  return (
    <div className="flex gap-1.5">
      {Array.from({ length: totalSlots }).map((_, i) => (
        <PokerCard
          key={i}
          card={cards[i]}
          size={size}
          onClick={onSlotClick ? () => onSlotClick(i) : undefined}
        />
      ))}
    </div>
  )
}
