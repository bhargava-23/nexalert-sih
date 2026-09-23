'use client'

// Location and page header component

import type { GeolocationState } from '@/types'

interface LocationHeaderProps {
  location: GeolocationState
  onRequestLocation: () => void
  emergencyMode: boolean
}

export function LocationHeader({
  location,
  onRequestLocation,
  emergencyMode,
}: LocationHeaderProps) {
  return (
    <header
      className={`sticky top-0 z-40 backdrop-blur-md border-b ${
        emergencyMode
          ? 'bg-red-950/80 border-red-500/30'
          : 'bg-zinc-900/80 border-white/10'
      }`}
    >
      <div className="max-w-screen-sm mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
              <span className="text-2xl">🔥</span>
              NexAlert
            </h1>
            {location.latitude && location.longitude ? (
              <p className="text-xs text-zinc-500 mt-1">
                📍 {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
              </p>
            ) : location.error ? (
              <p className="text-xs text-red-400 mt-1">Location unavailable</p>
            ) : (
              <button
                onClick={onRequestLocation}
                disabled={location.loading}
                className="text-xs text-blue-400 hover:text-blue-300 mt-1 underline disabled:opacity-50"
              >
                {location.loading ? 'Getting location...' : '📍 Enable location'}
              </button>
            )}
          </div>
          {emergencyMode && (
            <div className="px-3 py-1 rounded-lg bg-red-500/20 border border-red-500/50">
              <span className="text-xs font-bold text-red-300 uppercase">Emergency</span>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
