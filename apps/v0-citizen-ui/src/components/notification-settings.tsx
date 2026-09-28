/**
 * Notification Settings Component
 * Manages Web Push notification subscription flow
 */

import { useState, useEffect } from 'react';
import { Bell, Check, AlertTriangle, Loader2 } from 'lucide-react';
import {
  isPushSupported,
  getNotificationPermission,
  setupPushNotifications,
  getExistingSubscription,
  isSubscriptionCompatible,
  unsubscribeFromPush
} from '@/lib/web-push';

type NotificationState =
  | { status: 'checking' }
  | { status: 'not-supported' }
  | { status: 'not-subscribed' }
  | { status: 'subscribed'; subscription_id: string }
  | { status: 'subscribing' }
  | { status: 'error'; error: string };

export function NotificationSettings() {
  const [state, setState] = useState<NotificationState>({ status: 'checking' });

  useEffect(() => {
    checkNotificationState();
  }, []);

  async function checkNotificationState() {
    try {
      // Check if push is supported
      if (!isPushSupported()) {
        setState({ status: 'not-supported' });
        return;
      }

      // Check current permission
      const permission = getNotificationPermission();
      if (permission === 'denied') {
        setState({ status: 'not-subscribed' });
        return;
      }

      // Check if already subscribed
      const existingSub = await getExistingSubscription();
      if (existingSub && permission === 'granted') {
        // IMPORTANT: Check if subscription uses current VAPID key
        const isCompatible = await isSubscriptionCompatible();

        if (!isCompatible) {
          // VAPID key has changed - need to renew subscription
          console.log('[NotificationSettings] VAPID key changed - renewing subscription');
          setState({ status: 'not-subscribed' });
          return;
        }

        // Subscription is valid and compatible
        setState({ status: 'subscribed', subscription_id: 'existing' });
      } else {
        setState({ status: 'not-subscribed' });
      }
    } catch (error) {
      console.error('[NotificationSettings] Check failed:', error);
      setState({ status: 'not-subscribed' });
    }
  }

  async function handleEnableNotifications() {
    setState({ status: 'subscribing' });

    try {
      // Check if there's an existing subscription that needs to be unsubscribed
      const existingSub = await getExistingSubscription();
      if (existingSub) {
        const isCompatible = await isSubscriptionCompatible();
        if (!isCompatible) {
          // VAPID key changed - unsubscribe old subscription first
          console.log('[NotificationSettings] Unsubscribing old subscription before renewing');
          await unsubscribeFromPush();
        }
      }

      // Create new subscription with current VAPID key
      // For now, we don't have real location - pass undefined
      // In production, this would use the RealMap's user location
      const result = await setupPushNotifications();

      console.log('[NotificationSettings] Push notifications enabled:', result);
      setState({ status: 'subscribed', subscription_id: result.subscription_id });
    } catch (error: any) {
      console.error('[NotificationSettings] Setup failed:', error);
      setState({ status: 'error', error: error.message || 'Failed to enable notifications' });
    }
  }

  if (state.status === 'checking') {
    return (
      <div className="flex items-center gap-2 text-sm text-[#5a6763]">
        <Loader2 size={16} className="animate-spin" />
        Checking notification status...
      </div>
    );
  }

  if (state.status === 'not-supported') {
    return (
      <div className="rounded-xl border border-[#d9d3c6] bg-[#eeeae1] p-3 text-sm text-[#5a6763]">
        <AlertTriangle size={16} className="mb-1 inline text-[#a07a2d]" /> Push notifications are not supported in this browser.
      </div>
    );
  }

  if (state.status === 'subscribed') {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-[#abd8ca] bg-[#d9efe8] px-3 py-2 text-sm text-[#195d52]">
        <Check size={16} />
        <span className="font-semibold">Notifications enabled</span>
      </div>
    );
  }

  if (state.status === 'subscribing') {
    return (
      <button
        type="button"
        disabled
        className="flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-[#195d52] bg-[#e3f1ec] text-sm font-bold text-[#195d52]"
      >
        <Loader2 size={18} className="animate-spin" />
        Enabling notifications...
      </button>
    );
  }

  if (state.status === 'error') {
    return (
      <div className="space-y-2">
        <div className="rounded-xl border border-[#e7b1a5] bg-[#f6d9d2] p-3 text-sm text-[#923d34]">
          <AlertTriangle size={16} className="mb-1 inline" /> {state.error}
        </div>
        <button
          type="button"
          onClick={handleEnableNotifications}
          className="flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-[#195d52] bg-[#fff8f4] text-sm font-bold text-[#195d52] hover:bg-[#e3f1ec]"
        >
          <Bell size={18} />
          Try Again
        </button>
      </div>
    );
  }

  // not-subscribed
  return (
    <div className="space-y-3">
      <p className="text-sm text-[#5a6763]">
        Enable notifications to receive real-time hazard alerts on this device.
      </p>
      <button
        type="button"
        onClick={handleEnableNotifications}
        data-testid="button-enable-notifications"
        className="flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-[#195d52] bg-[#195d52] text-sm font-bold text-[#fff8f4] hover:bg-[#1f6860]"
      >
        <Bell size={18} />
        Enable Notifications
      </button>
    </div>
  );
}
