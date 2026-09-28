'use client'

// SOS Emergency Management Page
// Display and manage citizen emergency SOS requests

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { LoadingSpinner } from '@/components/ui/Loading'
import { ErrorState } from '@/components/ui/ErrorState'
import { formatTimestamp } from '@/lib/utils'

interface SOSRequest {
  sos_id: string
  status: string
  location_lat?: number
  location_lon?: number
  message?: string
  device_info?: string
  created_at: string
  updated_at: string
  acknowledged_at?: string
  resolved_at?: string
}

const STATUS_COLORS = {
  QUEUED: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  SENT: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  ACKNOWLEDGED: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  UNREACHABLE: 'bg-red-500/10 text-red-400 border-red-500/20',
  RESOLVED: 'bg-green-500/10 text-green-400 border-green-500/20',
}

const STATUS_LABELS = {
  QUEUED: 'Queued',
  SENT: 'Sent',
  ACKNOWLEDGED: 'Acknowledged',
  UNREACHABLE: 'Unreachable',
  RESOLVED: 'Resolved',
}

export default function SOSPage() {
  const [requests, setRequests] = useState<SOSRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('ALL')
  const [updatingId, setUpdatingId] = useState<string | null>(null)

  const fetchSOSRequests = async () => {
    try {
      setError(null)
      const data = await api.getSOSRequests()
      setRequests(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load SOS requests')
      console.error('SOS fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSOSRequests()
    const interval = setInterval(fetchSOSRequests, 5000) // Poll every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const handleStatusUpdate = async (sosId: string, newStatus: string) => {
    setUpdatingId(sosId)
    try {
      await api.updateSOSStatus(sosId, newStatus)
      await fetchSOSRequests()
    } catch (err) {
      console.error('Failed to update SOS status:', err)
      alert(`Failed to update SOS status: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setUpdatingId(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p className="text-zinc-400">Loading SOS Requests...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <ErrorState
            title="SOS System Error"
            message={error}
            onRetry={fetchSOSRequests}
          />
        </div>
      </div>
    )
  }

  const filteredRequests = filter === 'ALL'
    ? requests
    : requests.filter(r => r.status === filter)

  const activeRequests = requests.filter(r =>
    !['RESOLVED', 'UNREACHABLE'].includes(r.status)
  ).length

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">SOS Emergency Requests</h1>
          <p className="text-zinc-400">Monitor and respond to citizen emergency requests</p>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
            <div className="text-zinc-400 text-sm mb-1">Total Requests</div>
            <div className="text-2xl font-bold text-white">{requests.length}</div>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
            <div className="text-zinc-400 text-sm mb-1">Active</div>
            <div className="text-2xl font-bold text-orange-400">{activeRequests}</div>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
            <div className="text-zinc-400 text-sm mb-1">Acknowledged</div>
            <div className="text-2xl font-bold text-blue-400">
              {requests.filter(r => r.status === 'ACKNOWLEDGED').length}
            </div>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
            <div className="text-zinc-400 text-sm mb-1">Resolved</div>
            <div className="text-2xl font-bold text-green-400">
              {requests.filter(r => r.status === 'RESOLVED').length}
            </div>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700 mb-6">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setFilter('ALL')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                filter === 'ALL'
                  ? 'bg-blue-500 text-white'
                  : 'bg-zinc-700 text-zinc-300 hover:bg-zinc-600'
              }`}
            >
              All ({requests.length})
            </button>
            {Object.keys(STATUS_LABELS).map(status => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                  filter === status
                    ? 'bg-blue-500 text-white'
                    : 'bg-zinc-700 text-zinc-300 hover:bg-zinc-600'
                }`}
              >
                {STATUS_LABELS[status as keyof typeof STATUS_LABELS]} (
                {requests.filter(r => r.status === status).length})
              </button>
            ))}
          </div>
        </div>

        {/* SOS Request List */}
        {filteredRequests.length === 0 ? (
          <div className="bg-zinc-800/50 rounded-lg p-8 border border-zinc-700 text-center">
            <p className="text-zinc-400">No SOS requests found</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredRequests.map(request => (
              <div
                key={request.sos_id}
                className="bg-zinc-800/50 rounded-lg p-6 border border-zinc-700 hover:border-zinc-600 transition"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white font-mono">
                        {request.sos_id.substring(0, 8)}
                      </h3>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium border ${
                          STATUS_COLORS[request.status as keyof typeof STATUS_COLORS]
                        }`}
                      >
                        {STATUS_LABELS[request.status as keyof typeof STATUS_LABELS]}
                      </span>
                    </div>
                    <div className="text-sm text-zinc-400 space-y-1">
                      <div>
                        <span className="text-zinc-500">Created:</span>{' '}
                        {formatTimestamp(request.created_at)}
                      </div>
                      {request.location_lat && request.location_lon && (
                        <div>
                          <span className="text-zinc-500">Location:</span>{' '}
                          {request.location_lat.toFixed(6)}, {request.location_lon.toFixed(6)}
                        </div>
                      )}
                      {request.message && (
                        <div>
                          <span className="text-zinc-500">Message:</span> {request.message}
                        </div>
                      )}
                      {request.acknowledged_at && (
                        <div>
                          <span className="text-zinc-500">Acknowledged:</span>{' '}
                          {formatTimestamp(request.acknowledged_at)}
                        </div>
                      )}
                      {request.resolved_at && (
                        <div>
                          <span className="text-zinc-500">Resolved:</span>{' '}
                          {formatTimestamp(request.resolved_at)}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    {request.status === 'QUEUED' || request.status === 'SENT' ? (
                      <button
                        onClick={() => handleStatusUpdate(request.sos_id, 'ACKNOWLEDGED')}
                        disabled={updatingId === request.sos_id}
                        className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
                      >
                        {updatingId === request.sos_id ? 'Updating...' : 'Acknowledge'}
                      </button>
                    ) : null}
                    {request.status === 'ACKNOWLEDGED' ? (
                      <button
                        onClick={() => handleStatusUpdate(request.sos_id, 'RESOLVED')}
                        disabled={updatingId === request.sos_id}
                        className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
                      >
                        {updatingId === request.sos_id ? 'Updating...' : 'Resolve'}
                      </button>
                    ) : null}
                    {(request.status === 'QUEUED' || request.status === 'SENT') && (
                      <button
                        onClick={() => handleStatusUpdate(request.sos_id, 'UNREACHABLE')}
                        disabled={updatingId === request.sos_id}
                        className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
                      >
                        {updatingId === request.sos_id ? 'Updating...' : 'Mark Unreachable'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
