/**
 * NexAlert Citizen Service Worker
 *
 * Handles:
 * - Web Push notifications
 * - Notification click handling
 * - Deep linking to emergency UI
 * - Offline cache (future)
 */

const CACHE_VERSION = 'nexalert-v1'
const API_BASE = self.location.origin.includes('localhost')
  ? 'http://localhost:8000'
  : 'https://api.nexalert.local' // Production API URL

// Install service worker
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...')
  self.skipWaiting()
})

// Activate service worker
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...')
  event.waitUntil(self.clients.claim())
})

// Handle push notifications
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received')

  if (!event.data) {
    console.warn('[SW] Push event has no data')
    return
  }

  try {
    const payload = event.data.json()
    console.log('[SW] Push payload:', payload)

    const {
      title,
      body,
      icon,
      badge,
      tag,
      data,
      requireInteraction,
      vibrate
    } = payload

    const options = {
      body: body || 'NexAlert notification',
      icon: icon || '/icon-192x192.png',
      badge: badge || '/badge-96x96.png',
      tag: tag || 'nexalert-notification',
      data: data || {},
      requireInteraction: requireInteraction || false,
      vibrate: vibrate || [200, 100, 200],
      actions: [
        {
          action: 'view',
          title: 'View Details',
          icon: '/icons/view.png'
        },
        {
          action: 'dismiss',
          title: 'Dismiss',
          icon: '/icons/dismiss.png'
        }
      ]
    }

    event.waitUntil(
      self.registration.showNotification(title || 'NexAlert', options)
    )
  } catch (error) {
    console.error('[SW] Failed to show notification:', error)
  }
})

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.action, event.notification.tag)

  event.notification.close()

  // Get alert data from notification
  const data = event.notification.data || {}
  const alertId = data.alert_id
  const incidentId = data.incident_id

  // Construct URL (emergency mode activates automatically based on active incidents)
  const url = data.url || '/'

  // Track notification opened
  if (alertId) {
    fetch(`${API_BASE}/api/v1/alerts/${alertId}/opened`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        opened_at: new Date().toISOString()
      })
    }).catch(err => console.error('[SW] Failed to track notification open:', err))
  }

  // Open or focus citizen UI
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if citizen UI is already open
        for (const client of clientList) {
          if (client.url.includes(url) && 'focus' in client) {
            return client.focus()
          }
        }

        // Open new window if not found
        if (self.clients.openWindow) {
          return self.clients.openWindow(url)
        }
      })
  )
})

// Handle notification close
self.addEventListener('notificationclose', (event) => {
  console.log('[SW] Notification dismissed:', event.notification.tag)

  // Optional: Track dismissals for analytics
  const data = event.notification.data || {}
  const alertId = data.alert_id

  if (alertId) {
    fetch(`${API_BASE}/api/v1/alerts/${alertId}/dismissed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dismissed_at: new Date().toISOString()
      })
    }).catch(err => console.error('[SW] Failed to track dismissal:', err))
  }
})

// Handle messages from client
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data)

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
})

console.log('[SW] Service worker loaded')
