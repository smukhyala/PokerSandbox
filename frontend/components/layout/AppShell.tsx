import Link from 'next/link'
import { useRouter } from 'next/router'
import { GraduationCap, Search, Play, FlaskConical } from 'lucide-react'
import clsx from 'clsx'

const NAV_ITEMS = [
  { href: '/train', label: 'Train', icon: GraduationCap },
  { href: '/analyze', label: 'Analyze', icon: Search },
  { href: '/simulate', label: 'Simulate', icon: Play },
  { href: '/strategy', label: 'Strategy Lab', icon: FlaskConical },
]

export default function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter()

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      {/* Sidebar */}
      <nav className="w-56 border-r border-gray-800 flex flex-col py-6 px-3 shrink-0">
        <div className="px-3 mb-8">
          <h1 className="text-xl font-bold text-amber-400">PokerLab</h1>
          <p className="text-xs text-gray-500 mt-1">ML Poker Training</p>
        </div>
        <div className="space-y-1">
          {NAV_ITEMS.map(item => {
            const isActive = router.pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-amber-400/10 text-amber-400 border-l-2 border-amber-400'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50',
                )}
              >
                <item.icon size={18} />
                {item.label}
              </Link>
            )
          })}
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-8">
        {children}
      </main>
    </div>
  )
}
