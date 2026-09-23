import type { Metadata } from 'next'
import './globals.css'
import { MainNav } from '@/components/navigation/MainNav'

export const metadata: Metadata = {
  title: 'NexAlert Command Center',
  description: 'Real-time hazard monitoring and intelligence dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <MainNav />
        {children}
      </body>
    </html>
  )
}
