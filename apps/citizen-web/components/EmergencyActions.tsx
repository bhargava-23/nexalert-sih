'use client'

// Emergency actions - persistent SOS and emergency communication

import { GlassCard } from '@/components/ui/GlassCard'

interface EmergencyActionsProps {
  normalMode?: boolean
}

export function EmergencyActions({ normalMode = false }: EmergencyActionsProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {/* Emergency Call - Real device phone action */}
      <a href="tel:112">
        <GlassCard
          className={`text-center py-6 hover:bg-white/5 transition-colors ${
            !normalMode ? 'bg-red-500/10 border-red-500/30' : ''
          }`}
        >
          <div className="text-3xl mb-2">📞</div>
          <p className="font-medium text-zinc-100 text-sm">Emergency</p>
          <p className={`text-xs mt-1 ${!normalMode ? 'text-red-400' : 'text-zinc-500'}`}>
            Call 112
          </p>
        </GlassCard>
      </a>

      {/* Map placeholder - backend capability not yet implemented */}
      <button
        onClick={() =>
          alert(
            'Map view: Real mapping integration with hazard geometry from backend requires additional implementation.'
          )
        }
      >
        <GlassCard className="text-center py-6 hover:bg-white/5 transition-colors">
          <div className="text-3xl mb-2">🗺️</div>
          <p className="font-medium text-zinc-100 text-sm">View Map</p>
          <p className="text-xs text-zinc-500 mt-1">
            {normalMode ? 'Monitoring nodes' : 'Affected area'}
          </p>
        </GlassCard>
      </button>

      {normalMode && (
        <>
          {/* Safety information placeholder */}
          <button
            onClick={() =>
              alert('Safety guidance: Preparedness information not yet implemented.')
            }
          >
            <GlassCard className="text-center py-6 hover:bg-white/5 transition-colors">
              <div className="text-3xl mb-2">🛡️</div>
              <p className="font-medium text-zinc-100 text-sm">Safety Tips</p>
              <p className="text-xs text-zinc-500 mt-1">Be prepared</p>
            </GlassCard>
          </button>

          {/* About/info placeholder */}
          <button
            onClick={() =>
              alert('NexAlert system information: Real-time environmental monitoring operational.')
            }
          >
            <GlassCard className="text-center py-6 hover:bg-white/5 transition-colors">
              <div className="text-3xl mb-2">ℹ️</div>
              <p className="font-medium text-zinc-100 text-sm">About</p>
              <p className="text-xs text-zinc-500 mt-1">NexAlert info</p>
            </GlassCard>
          </button>
        </>
      )}
    </div>
  )
}
