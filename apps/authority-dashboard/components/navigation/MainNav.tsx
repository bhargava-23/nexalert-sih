'use client'

// Main Navigation Component

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const navItems = [
  { href: '/', label: 'Overview' },
  { href: '/monitoring', label: 'Live Monitoring' },
  { href: '/hazards', label: 'Hazards' },
  { href: '/nodes', label: 'Nodes' },
  { href: '/map', label: 'Map' },
]

export function MainNav() {
  const pathname = usePathname()

  return (
    <nav className="border-b border-white/10 bg-zinc-900/50 backdrop-blur-md sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3">
            <div className="text-2xl">🔥</div>
            <div>
              <div className="font-bold text-zinc-100">NexAlert</div>
              <div className="text-xs text-zinc-500">Command Center</div>
            </div>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-white/10 text-zinc-100'
                      : 'text-zinc-400 hover:text-zinc-100 hover:bg-white/5'
                  )}
                >
                  {item.label}
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}
