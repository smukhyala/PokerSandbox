import Link from 'next/link'
import { useRouter } from 'next/router'
import { GraduationCap, Search, Play, FlaskConical, Workflow } from 'lucide-react'
import { motion } from 'motion/react'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { href: '/train', label: 'Train', icon: GraduationCap },
  { href: '/analyze', label: 'Analyze', icon: Search },
  { href: '/simulate', label: 'Simulate', icon: Play },
  { href: '/strategy', label: 'Strategy Lab', icon: FlaskConical },
  { href: '/guide', label: 'How It Works', icon: Workflow },
]

export default function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter()

  return (
    <div className="flex min-h-screen bg-black text-white">
      <nav className="w-56 border-r border-white/10 flex flex-col py-6 px-3 shrink-0 bg-black">
        <div className="px-3 mb-8">
          <h1 className="text-xl font-semibold tracking-tight text-white">PokerLab</h1>
          <p className="text-xs text-zinc-500 mt-1">Strategy Compiler</p>
        </div>
        <div className="space-y-1">
          {NAV_ITEMS.map(item => {
            const isActive = router.pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-white text-black'
                    : 'text-zinc-400 hover:text-white hover:bg-white/10',
                )}
              >
                <item.icon size={18} />
                {item.label}
              </Link>
            )
          })}
        </div>
      </nav>

      <motion.main
        key={router.pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.22, ease: 'easeOut' }}
        className="flex-1 overflow-y-auto p-8"
      >
        {children}
      </motion.main>
    </div>
  )
}
