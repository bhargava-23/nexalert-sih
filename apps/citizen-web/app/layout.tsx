import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'NexAlert - Public Safety',
  description: 'Real-time environmental hazard alerts and safety information for citizens',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
        {children}
      </body>
    </html>
  )
}
