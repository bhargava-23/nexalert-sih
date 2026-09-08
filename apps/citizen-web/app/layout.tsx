import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'NexAlert Citizen Web',
  description: 'Citizen PWA for NexAlert environmental monitoring system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
