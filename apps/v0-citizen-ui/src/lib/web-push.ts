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
 * Handles both URL-safe and standard base64 formats
 * Critical for VAPID key in PushManager.subscribe()
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  try {
    // Remove any whitespace
    base64String = base64String.trim();

    // Add padding if needed
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);

    // Convert URL-safe base64 to standard base64
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    // Decode base64 to binary string
    const rawData = window.atob(base64);

    // Convert binary string to Uint8Array
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; i++) {
      outputArray[i] = rawData.charCodeAt(i);
    }

    console.log('[WebPush] Converted VAPID key:', outputArray.length, 'bytes');
    return outputArray;
  } catch (error) {
    console.error('[WebPush] VAPID key conversion failed:', error);
    throw new Error('Invalid VAPID public key format');
  }
}

/**
 * Subscribe to push notifications
 * Enhanced error handling for mobile browsers
 */
export async function subscribeToPush(
  registration: ServiceWorkerRegistration
): Promise<PushSubscriptionData> {
  try {
    // Get VAPID public key from backend
    console.log('[WebPush] Fetching VAPID public key from backend...');
    const vapidPublicKey = await getVapidPublicKey();
    console.log('[WebPush] VAPID key received, length:', vapidPublicKey.length);

    // Convert to Uint8Array for PushManager.subscribe()
    const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);

    // Subscribe to push with VAPID key
    console.log('[WebPush] Calling PushManager.subscribe()...');
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey
    });

    console.log('[WebPush] ✅ Push subscription created successfully');
    console.log('[WebPush] Endpoint:', subscription.endpoint);

    // Verify subscription has required keys
    const p256dhKey = subscription.getKey('p256dh');
    const authKey = subscription.getKey('auth');

    if (!p256dhKey || !authKey) {
      throw new Error('Subscription missing required keys (p256dh or auth)');
    }

    // Convert subscription to data format
    const subscriptionData: PushSubscriptionData = {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: arrayBufferToBase64(p256dhKey),
        auth: arrayBufferToBase64(authKey)
      }
    };

    console.log('[WebPush] Subscription data prepared for backend');
    return subscriptionData;
  } catch (error: any) {
    console.error('[WebPush] Push subscription failed:', error);

    // Provide helpful error messages for common issues
    if (error.name === 'NotAllowedError') {
      throw new Error('Push subscription denied by browser or user');
    } else if (error.name === 'NotSupportedError') {
      throw new Error('Push messaging not supported on this device/browser');
    } else if (error.name === 'InvalidStateError') {
      throw new Error('Service worker is not in active state');
    } else if (error.message?.includes('VAPID')) {
      throw new Error(`VAPID key error: ${error.message}`);
    } else {
      throw error;
    }
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
 * Improved error handling with specific failure stages
 */
export async function setupPushNotifications(
  location?: { lat: number; lon: number }
): Promise<{ subscription_id: string; subscription: PushSubscriptionData }> {
  try {
    // STAGE 1: Check support
    if (!isPushSupported()) {
      throw new Error('STAGE: Browser Support - Push notifications not supported in this browser');
    }

    // STAGE 2: Request permission
    let permission: NotificationPermission;
    try {
      permission = await requestNotificationPermission();
    } catch (error: any) {
      throw new Error(`STAGE: Permission Request - ${error.message || 'Permission request failed'}`);
    }

    if (permission !== 'granted') {
      throw new Error(`STAGE: Permission Denied - User ${permission === 'denied' ? 'denied' : 'dismissed'} notification permission`);
    }

    // STAGE 3: Register service worker
    let registration: ServiceWorkerRegistration;
    try {
      registration = await registerServiceWorker();
    } catch (error: any) {
      throw new Error(`STAGE: Service Worker Registration - ${error.message || 'Failed to register service worker'}`);
    }

    // STAGE 4: Check for and handle existing subscription
    try {
      const existingSub = await registration.pushManager.getSubscription();
      if (existingSub) {
        console.log('[WebPush] Found existing subscription, checking compatibility...');

        // Try to determine if subscription is compatible
        // If we can't verify, unsubscribe to be safe
        try {
          const isCompatible = await isSubscriptionCompatible();
          if (!isCompatible) {
            console.log('[WebPush] Existing subscription incompatible (VAPID changed), unsubscribing...');
            await existingSub.unsubscribe();
          }
        } catch (compatError) {
          // If we can't check compatibility, unsubscribe old one to be safe
          console.log('[WebPush] Cannot verify compatibility, unsubscribing old subscription...');
          await existingSub.unsubscribe();
        }
      }
    } catch (error) {
      console.warn('[WebPush] Failed to check existing subscription, continuing...', error);
    }

    // STAGE 5: Subscribe to push with VAPID key
    let subscription: PushSubscriptionData;
    try {
      subscription = await subscribeToPush(registration);
    } catch (error: any) {
      // Provide specific error for PushManager.subscribe failures
      if (error.name === 'NotAllowedError') {
        throw new Error('STAGE: Push Subscribe - Permission denied by browser');
      } else if (error.name === 'NotSupportedError') {
        throw new Error('STAGE: Push Subscribe - Push messaging not supported');
      } else if (error.name === 'InvalidStateError') {
        throw new Error('STAGE: Push Subscribe - Service worker not active');
      } else {
        throw new Error(`STAGE: Push Subscribe - ${error.message || 'PushManager.subscribe() failed'}`);
      }
    }

    // STAGE 6: Send to backend
    let result: { subscription_id: string };
    try {
      result = await sendSubscriptionToBackend(subscription, location);
    } catch (error: any) {
      throw new Error(`STAGE: Backend Registration - ${error.message || 'Failed to register with backend'}`);
    }

    console.log('[WebPush] ✅ Push notifications enabled successfully');
    return {
      subscription_id: result.subscription_id,
      subscription
    };
  } catch (error: any) {
    // Re-throw with original error message if already formatted
    throw error;
  }
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
