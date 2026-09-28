/**
 * Web Push notification utilities
 * Handles browser push subscription and notification management
 */

const BACKEND_URL = import.meta.env.VITE_API_BASE_URL || 'http://192.168.29.178:8000';

export interface PushSubscriptionData {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

/**
 * Check if push notifications are supported
 */
export function isPushSupported(): boolean {
  return (
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  );
}

/**
 * Get current notification permission state
 */
export function getNotificationPermission(): NotificationPermission {
  if (!('Notification' in window)) {
    return 'denied';
  }
  return Notification.permission;
}

/**
 * Request notification permission from the user
 */
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    throw new Error('Notifications not supported in this browser');
  }

  const permission = await Notification.requestPermission();
  console.log('[WebPush] Notification permission:', permission);
  return permission;
}

/**
 * Register service worker
 */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration> {
  if (!('serviceWorker' in navigator)) {
    throw new Error('Service workers not supported in this browser');
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
      updateViaCache: 'none'
    });

    console.log('[WebPush] Service worker registered:', registration);

    // Wait for service worker to be ready
    await navigator.serviceWorker.ready;
    console.log('[WebPush] Service worker ready');

    return registration;
  } catch (error) {
    console.error('[WebPush] Service worker registration failed:', error);
    throw error;
  }
}

/**
 * Get VAPID public key from backend
 */
export async function getVapidPublicKey(): Promise<string> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/alerts/vapid-public-key`);
    if (!response.ok) {
      throw new Error(`Failed to get VAPID key: ${response.status}`);
    }
    const data = await response.json();
    console.log('[WebPush] VAPID public key retrieved');
    return data.public_key;
  } catch (error) {
    console.error('[WebPush] Failed to get VAPID public key:', error);
    throw error;
  }
}

/**
 * Convert base64 URL-safe string to Uint8Array
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

/**
 * Subscribe to push notifications
 */
export async function subscribeToPush(
  registration: ServiceWorkerRegistration
): Promise<PushSubscriptionData> {
  try {
    // Get VAPID public key from backend
    const vapidPublicKey = await getVapidPublicKey();
    const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);

    // Subscribe to push
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey
    });

    console.log('[WebPush] Push subscription created:', subscription);

    // Convert subscription to data format
    const subscriptionData: PushSubscriptionData = {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: arrayBufferToBase64(subscription.getKey('p256dh')!),
        auth: arrayBufferToBase64(subscription.getKey('auth')!)
      }
    };

    return subscriptionData;
  } catch (error) {
    console.error('[WebPush] Push subscription failed:', error);
    throw error;
  }
}

/**
 * Convert ArrayBuffer to base64 string
 */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

/**
 * Send subscription to backend
 */
export async function sendSubscriptionToBackend(
  subscription: PushSubscriptionData,
  location?: { lat: number; lon: number }
): Promise<{ subscription_id: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/alerts/subscribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        endpoint: subscription.endpoint,
        p256dh_key: subscription.keys.p256dh,
        auth_secret: subscription.keys.auth,
        location_lat: location?.lat,
        location_lon: location?.lon
      })
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Backend subscription failed: ${response.status} ${error}`);
    }

    const data = await response.json();
    console.log('[WebPush] Subscription sent to backend:', data);
    return data;
  } catch (error) {
    console.error('[WebPush] Failed to send subscription to backend:', error);
    throw error;
  }
}

/**
 * Complete push notification setup flow
 */
export async function setupPushNotifications(
  location?: { lat: number; lon: number }
): Promise<{ subscription_id: string; subscription: PushSubscriptionData }> {
  // Check support
  if (!isPushSupported()) {
    throw new Error('Push notifications not supported in this browser');
  }

  // Request permission
  const permission = await requestNotificationPermission();
  if (permission !== 'granted') {
    throw new Error(`Notification permission ${permission}`);
  }

  // Register service worker
  const registration = await registerServiceWorker();

  // Subscribe to push
  const subscription = await subscribeToPush(registration);

  // Send to backend
  const result = await sendSubscriptionToBackend(subscription, location);

  return {
    subscription_id: result.subscription_id,
    subscription
  };
}

/**
 * Get existing push subscription
 */
export async function getExistingSubscription(): Promise<PushSubscriptionData | null> {
  if (!('serviceWorker' in navigator)) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) {
      return null;
    }

    const subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
      return null;
    }

    return {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: arrayBufferToBase64(subscription.getKey('p256dh')!),
        auth: arrayBufferToBase64(subscription.getKey('auth')!)
      }
    };
  } catch (error) {
    console.error('[WebPush] Failed to get existing subscription:', error);
    return null;
  }
}

/**
 * Check if existing subscription uses current VAPID key
 * Returns true if subscription is compatible with current backend VAPID key
 */
export async function isSubscriptionCompatible(): Promise<boolean> {
  if (!('serviceWorker' in navigator)) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) {
      return false;
    }

    const subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
      return false;
    }

    // Get current VAPID public key from backend
    const currentVapidKey = await getVapidPublicKey();
    const currentKeyBytes = urlBase64ToUint8Array(currentVapidKey);

    // Get the applicationServerKey the subscription was created with
    // Note: subscription.options.applicationServerKey can be ArrayBuffer or null
    const subscriptionKeyBytes = subscription.options?.applicationServerKey;

    if (!subscriptionKeyBytes || !(subscriptionKeyBytes instanceof ArrayBuffer)) {
      // No applicationServerKey available - assume incompatible
      console.warn('[WebPush] Subscription has no applicationServerKey - assuming incompatible');
      return false;
    }

    // Compare the keys byte by byte
    const subKeyArray = new Uint8Array(subscriptionKeyBytes);
    if (subKeyArray.length !== currentKeyBytes.length) {
      console.log('[WebPush] Key length mismatch - VAPID key has changed');
      return false;
    }

    for (let i = 0; i < subKeyArray.length; i++) {
      if (subKeyArray[i] !== currentKeyBytes[i]) {
        console.log('[WebPush] Key bytes mismatch - VAPID key has changed');
        return false;
      }
    }

    console.log('[WebPush] Subscription uses current VAPID key');
    return true;

  } catch (error) {
    console.error('[WebPush] Failed to check subscription compatibility:', error);
    return false;
  }
}

/**
 * Unsubscribe from push notifications
 */
export async function unsubscribeFromPush(): Promise<boolean> {
  if (!('serviceWorker' in navigator)) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) {
      return false;
    }

    const subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
      return false;
    }

    const success = await subscription.unsubscribe();
    if (success) {
      console.log('[WebPush] Unsubscribed from push notifications');
    }
    return success;

  } catch (error) {
    console.error('[WebPush] Failed to unsubscribe:', error);
    return false;
  }
}
