/**
 * NexAlert Service Worker
 * Handles push notifications and offline capabilities
 */

const CACHE_VERSION = 'nexalert-v1';
const CACHE_NAME = `nexalert-cache-${CACHE_VERSION}`;

// Install event - cache critical assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  self.skipWaiting(); // Activate immediately
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name.startsWith('nexalert-cache-') && name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push received:', event);

  let notificationData = {
    title: 'NexAlert',
    body: 'New alert from NexAlert',
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    tag: 'nexalert-notification',
    requireInteraction: true,
    data: {
      url: '/'
    }
  };

  if (event.data) {
    try {
      const payload = event.data.json();
      console.log('[Service Worker] Push payload:', payload);

      notificationData = {
        title: payload.title || 'NexAlert Emergency',
        body: payload.body || payload.message || 'New hazard alert',
        icon: payload.icon || '/favicon.svg',
        badge: '/favicon.svg',
        tag: payload.tag || `nexalert-${payload.alert_id || Date.now()}`,
        requireInteraction: payload.severity === 'CRITICAL',
        vibrate: payload.severity === 'CRITICAL' ? [200, 100, 200] : [100],
        data: {
          alert_id: payload.alert_id,
          hazard_type: payload.hazard_type,
          severity: payload.severity,
          url: payload.url || '/',
          timestamp: Date.now()
        }
      };
    } catch (e) {
      console.error('[Service Worker] Failed to parse push payload:', e);
    }
  }

  event.waitUntil(
    self.registration.showNotification(notificationData.title, notificationData)
  );
});

// Notification click event - open the app
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked:', event);
  event.notification.close();

  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if there's already a window open
        for (const client of clientList) {
          if (client.url.includes(self.registration.scope) && 'focus' in client) {
            return client.focus().then(client => {
              // Navigate to the alert URL
              if (client.navigate) {
                return client.navigate(urlToOpen);
              }
              return client;
            });
          }
        }
        // No window open, open a new one
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Fetch event - serve from cache when offline (optional)
self.addEventListener('fetch', (event) => {
  // Let all requests go through to the network
  // In the future, we could add offline support here
  event.respondWith(fetch(event.request));
});
