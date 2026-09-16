import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'NexAlert Citizen Emergency',
  description: 'Citizen emergency alert system for NexAlert environmental monitoring',
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
